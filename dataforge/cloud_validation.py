"""Read-only GCP audit: metadata fetch + BigQuery dry-run only.

Credentials must be supplied via private runtime secrets. No insert, load,
subscription ACK, live SQL result() or cloud resource mutation occurs.
"""
import re
from typing import Any

TABLES = ("baseline_customers", "shifted_customers", "paired_prediction_replay")
REPLAY_COLUMNS = {"customer_id", "predicted_churn_before", "predicted_churn_after"}


def validate_project_id(project_id: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", project_id or ""):
        raise ValueError("A valid Google Cloud project ID is required")
    return project_id


def audit_bigquery_dry_runs(client: Any, project_id: str,
                            dataset: str = "datapulse_ai", location: str = "US",
                            max_bytes: int = 100_000_000) -> dict:
    """Verify actual table metadata and compile read-only estimates; never execute results."""
    validate_project_id(project_id)
    if dataset != "datapulse_ai" or location not in {"US", "EU"}:
        raise ValueError("Dataset/location not on approved list")
    if not 0 <= max_bytes <= 1_000_000_000:
        raise ValueError("Unapproved dry-run bytes budget")
    from google.cloud import bigquery
    output = {"mode":"metadata_and_dry_run_only", "source":"live_gcp",
              "project_id":project_id, "dataset":dataset, "checks":[],
              "executed_queries":0, "created_resources":0}
    for name in TABLES:
        ref = f"{project_id}.{dataset}.{name}"
        item = {"table":ref, "metadata_verified":False,"dry_run_executed":False}
        try:
            info = client.get_table(ref)
            columns = {field.name for field in info.schema}
            if name == "paired_prediction_replay" and not REPLAY_COLUMNS <= columns:
                raise ValueError("Replay table lacks required DataPulse columns")
            item["metadata_verified"] = True
            item["schema_columns"] = sorted(columns)
            # All SQL is fixed by code; no arbitrary user query can enter this path.
            sql = f"SELECT COUNT(*) AS row_count FROM `{ref}`"
            cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False,
                                          use_legacy_sql=False, maximum_bytes_billed=max_bytes or 1)
            job = client.query(sql, job_config=cfg, location=location)
            item["dry_run_executed"] = True
            item["estimated_bytes"] = int(job.total_bytes_processed or 0)
            item["within_estimate_budget"] = item["estimated_bytes"] <= max_bytes
        except Exception as exc:
            # Deliberately hide credential details from public output.
            item["status"] = "unavailable_or_failed"
            item["error_type"] = type(exc).__name__
        else:
            item["status"] = "passed" if item["within_estimate_budget"] else "estimate_over_budget"
        output["checks"].append(item)
    output["all_passed"] = all(x["status"] == "passed" for x in output["checks"])
    output["caveat"] = "Metadata and dry runs do not verify rows, Pub/Sub delivery, live ML replay, or model outcomes. No query results were fetched."
    return output


def authorized_service_account_client(service_account_info: dict, project_id: str):
    """Only for admin-gated audits; do not log or persist the service account key."""
    from google.oauth2 import service_account
    from google.cloud import bigquery
    validate_project_id(project_id)
    creds = service_account.Credentials.from_service_account_info(
        dict(service_account_info), scopes=["https://www.googleapis.com/auth/bigquery"])
    return bigquery.Client(project=project_id, credentials=creds)


def audit_pubsub_topology(project_id: str, credentials: Any = None) -> dict:
    """Read Pub/Sub topic/subscription metadata only, no pull/ack/publish."""
    validate_project_id(project_id)
    from google.cloud import pubsub_v1
    publisher = pubsub_v1.PublisherClient(credentials=credentials)
    subscriber = pubsub_v1.SubscriberClient(credentials=credentials)
    topic = publisher.topic_path(project_id, "datapulse-incidents")
    subpath = subscriber.subscription_path(project_id, "datapulse-incidents-consumer")
    status = {"topic_exists": False, "subscription_connected": False,
              "messages_read": 0, "messages_published":0, "messages_acknowledged":0}
    try:
        publisher.get_topic(request={"topic": topic})
        status["topic_exists"] = True
        subscription = subscriber.get_subscription(request={"subscription":subpath})
        status["subscription_connected"] = subscription.topic == topic
    except Exception as exc:
        status["status"] = "unavailable_or_failed"
        status["error_type"] = type(exc).__name__
    else:
        status["status"] = "passed" if status["subscription_connected"] else "mismatch"
    return status


def audit_opt_in_aggregates(client: Any, project_id: str,
                            approved_by_user: bool = False,
                            max_bytes: int = 100_000_000, location: str = "US") -> dict:
    """Optional **billable** bounded aggregate queries for authorized Colab use only.

    Never expose via anonymous Streamlit UI. Caller must explicitly consent.
    """
    validate_project_id(project_id)
    if not approved_by_user:
        return {"status": "requires_explicit_user_approval", "queries_executed": 0}
    if not 1 <= max_bytes <= 1_000_000_000 or location not in {"US", "EU"}:
        raise ValueError("Invalid query budget or location")
    from google.cloud import bigquery
    sql=("SELECT COUNT(*) AS tested_customers, "
         "COUNTIF(predicted_churn_before != predicted_churn_after) AS prediction_flips "
         f"FROM `{project_id}.datapulse_ai.paired_prediction_replay`")
    cfg=bigquery.QueryJobConfig(dry_run=False,use_legacy_sql=False,
                                 maximum_bytes_billed=max_bytes)
    # There is ONE hardcoded SELECT aggregate; no dynamic user SQL is executed.
    results=list(client.query(sql,job_config=cfg,location=location).result(max_results=1))
    row=results[0] if results else None
    if row is None:
        return {"status":"no_rows", "queries_executed": 1}
    return {"status":"passed", "queries_executed":1,
            "tested_customers":int(row.tested_customers),
            "prediction_flips":int(row.prediction_flips),
            "mode":"explicitly_approved_read_only_aggregate",
            "warning":"This query can incur charges; byte cap is not a budget hard-stop for all cloud services."}
