"""Optional BigQuery dry-run only; never calls result() or performs non-dry-run jobs."""
from typing import Any
from .guard import validate_sql
from dataforge.connectors.base import ProjectAdapter


def dry_run(sql: str, adapter: ProjectAdapter, enabled: bool, max_bytes: int,
            client: Any | None = None) -> dict[str, Any]:
    validate_sql(sql, adapter)
    if not enabled:
        return {"status": "disabled", "dry_run_executed": False,
                "message": "Cloud dry run disabled by default; set DATAFORGE_ENABLE_BIGQUERY_DRY_RUN=true"}
    try:
        from google.cloud import bigquery
    except ImportError as exc:
        return {"status": "unavailable", "dry_run_executed": False,
                "message": "Install project optional dependency: pip install -e '.[cloud]'"}
    try:
        if client is None:
            client = bigquery.Client()
        cfg = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, use_legacy_sql=False)
        query_job = client.query(sql, job_config=cfg)
        bytes_estimate = int(query_job.total_bytes_processed or 0)
        # False sense of certainty avoided; BigQuery dry run estimates can be inexact.
        return {"status": "passed" if bytes_estimate <= max_bytes else "over_budget",
                "dry_run_executed": True, "estimated_bytes": bytes_estimate,
                "max_bytes": max_bytes, "query_executed": False,
                "warning": "Dry-run estimates do not guarantee final billed bytes; zero bytes can reflect restricted metadata."}
    except Exception as exc:
        # Do not expose credential/project details in API errors.
        return {"status": "failed", "dry_run_executed": False,
                "message": f"BigQuery dry-run failed ({type(exc).__name__}); check credentials and location locally"}
