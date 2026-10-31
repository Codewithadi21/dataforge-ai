"""No real provider credentials or cloud services are used by these tests."""
import base64
import json
import sys
from types import SimpleNamespace, ModuleType

import pytest
import requests

from dataforge.cloud_validation import audit_bigquery_dry_runs, validate_project_id
from dataforge.connectors.repo_refresh import refresh_public_repo_snapshot
from dataforge.hosted import make_public_engine, ask_public
from dataforge.models.hosted_qwen import grounded_hosted_summary, HF_ROUTER
from dataforge.sql_tools.guard import validate_sql

def mock_google_sdk(monkeypatch, module_name, fake_module):
    """Mock optional Google Cloud SDK namespace even on clean CI runners."""
    google_module = ModuleType("google")
    cloud_module = ModuleType("google.cloud")
    setattr(google_module, "cloud", cloud_module)
    setattr(cloud_module, module_name, fake_module)
    monkeypatch.setitem(sys.modules, "google", google_module)
    monkeypatch.setitem(sys.modules, "google.cloud", cloud_module)
    monkeypatch.setitem(sys.modules, "google.cloud." + module_name, fake_module)


def test_repo_snapshot_is_distinct_and_source_grounded():
    engine = make_public_engine()
    orig = ask_public(engine, "Why did the churn model change?", project_id="datapulse-demo")
    repo = ask_public(engine, "Explain incident DP-REPO-SYN-001", project_id="datapulse-repo-snapshot")
    assert "prediction_flip_count=82" in orig.answer
    assert "prediction_flip_count=340" in repo.answer
    assert "paired_cohort_size=1500" in repo.answer
    assert "0.8157" in repo.answer
    assert repo.supporting_sources[0].path.startswith("https://github.com/Codewithadi21/")
    assert repo.supporting_sources[0].synthetic
    assert repo.model_backend == "deterministic"


def test_repo_snapshot_real_sql_names_are_validated():
    engine=make_public_engine()
    result=ask_public(engine,"Show customers whose predictions flipped",project_id="datapulse-repo-snapshot")
    assert result.sql_check["status"] == "passed"
    assert "predicted_churn_before != predicted_churn_after" in result.sql_draft
    assert result.sql_check["dry_run_executed"] is False
    sql="SELECT customer_id FROM `demo-project.datapulse_ai.paired_prediction_replay` LIMIT 5"
    assert validate_sql(sql,engine.registry.get("datapulse-repo-snapshot"))["status"]=="passed"


def test_unknown_public_project_fails_closed():
    with pytest.raises(KeyError):
        ask_public(make_public_engine(),"Explain incident",project_id="unapproved-project")


def test_hosted_qwen_mock_success_preserves_evidence():
    response=ask_public(make_public_engine(),"Explain incident DP-REPO-SYN-001",project_id="datapulse-repo-snapshot")
    original=response.answer
    calls=[]
    def fake_post(url, **kw):
        calls.append((url,kw))
        return SimpleNamespace(raise_for_status=lambda:None, json=lambda:{"choices":[{"message":{"content":"This synthetic replay recorded 340 prediction flips. Root cause remains a hypothesis."}}]})
    out=grounded_hosted_summary(response,"What happened?", "hf_1234567890", post=fake_post)
    assert out.model_backend=="qwen-hosted"
    assert original in out.answer
    assert calls[0][0]==HF_ROUTER
    assert "hf_1234567890" not in out.answer


def test_hosted_qwen_rejects_new_numbers_and_avoids_token_leak():
    answer=ask_public(make_public_engine(),"Explain incident DP-REPO-SYN-001",project_id="datapulse-repo-snapshot")
    def hallucination(url,**kw):
        return SimpleNamespace(raise_for_status=lambda:None,json=lambda:{"choices":[{"message":{"content":"5,000,000 people were harmed."}}]})
    out=grounded_hosted_summary(answer,"Explain incident", "hf_secret_token",post=hallucination)
    assert out.model_backend=="deterministic"
    assert "5,000,000" not in out.answer
    assert "hf_secret_token" not in out.answer


def test_hosted_qwen_skips_unsafe_or_sql_evidence():
    response=ask_public(make_public_engine(),"Show customers whose predictions flipped",project_id="datapulse-repo-snapshot")
    original=response.answer
    out=grounded_hosted_summary(response,"Explain", "hf_12345678",post=lambda *a,**k:1)
    assert out.answer==original
    assert out.model_backend=="deterministic"


def test_public_repo_refresh_reconciles_metrics_without_upstream_write():
    engine=make_public_engine()
    payload={
      "rows":5000,"test_rows":1500,"prediction_flips":340,"prediction_flip_rate":0.2267,
      "baseline_auc":0.8157,"changed_auc":0.5414,"baseline_false_negatives":238,
      "changed_false_negatives":458,"schema_checks_passed_after_shift":True,
      "semantic_checks_passed_after_shift":False}
    result_bytes=json.dumps({"encoding":"base64","content":base64.b64encode(json.dumps(payload).encode()).decode(),"sha":"mocksha"}).encode()
    def fake_get(url,**kw):
        assert "aegis-real-time-supply-chain-ai" in url
        return SimpleNamespace(raise_for_status=lambda:None, content=result_bytes)
    result=refresh_public_repo_snapshot(engine,get=fake_get)
    assert result["status"]=="fetched_and_validated"
    assert result["synthetic"] is True
    assert engine.registry.get("datapulse-repo-snapshot").get_incident("DP-REPO-SYN-001")["metrics"]["prediction_flip_count"]==340


def test_upstream_refresh_rejects_inconsistent_data():
    engine=make_public_engine()
    before=engine.registry.get("datapulse-repo-snapshot").get_incident("DP-REPO-SYN-001")["metrics"].copy()
    bad={"encoding":"base64","content":base64.b64encode(json.dumps({"prediction_flips": 9999}).encode()).decode()}
    outcome=refresh_public_repo_snapshot(engine, get=lambda *a,**kw:SimpleNamespace(raise_for_status=lambda:None,content=json.dumps(bad).encode()))
    assert outcome["status"]=="failed_pinned_snapshot_unchanged"
    assert engine.registry.get("datapulse-repo-snapshot").get_incident("DP-REPO-SYN-001")["metrics"]==before


def test_cloud_project_allowlist():
    for val in ["bad;DROP", "abc.def", "foo`", "", "a"]:
        with pytest.raises(ValueError):
            validate_project_id(val)
    assert validate_project_id("demo-project")=="demo-project"


def test_cloud_audit_uses_only_read_only_bigquery_dry_run(monkeypatch):
    observed=[]
    class FakeConfig:
        def __init__(self,**kw):
            assert kw["dry_run"] is True
            assert kw["use_legacy_sql"] is False
            observed.append(("config",kw))
    class FakeClient:
        def get_table(self,ref):
            observed.append(("table",ref))
            cols={"customer_id","predicted_churn_before","predicted_churn_after"} if ref.endswith("paired_prediction_replay") else {"customer_id"}
            return SimpleNamespace(schema=[SimpleNamespace(name=n) for n in cols])
        def query(self,sql,**kw):
            observed.append(("query",sql))
            assert sql.startswith("SELECT COUNT(*) AS row_count FROM `demo-project.datapulse_ai.")
            assert kw["job_config"].__class__ is FakeConfig
            return SimpleNamespace(total_bytes_processed=1200)
    mock_google_sdk(monkeypatch, "bigquery", SimpleNamespace(QueryJobConfig=FakeConfig))
    out=audit_bigquery_dry_runs(FakeClient(),"demo-project")
    assert out["all_passed"]
    assert out["executed_queries"]==0
    assert out["created_resources"]==0
    assert len([a for a in observed if a[0]=="query"])==3


def test_cloud_audit_rejects_unknown_dataset_without_network():
    with pytest.raises(ValueError):
        audit_bigquery_dry_runs(None,"demo-project",dataset="sensitive")


def test_opt_in_aggregates_never_executes_without_approval():
    from dataforge.cloud_validation import audit_opt_in_aggregates
    result=audit_opt_in_aggregates(None,"demo-project",approved_by_user=False)
    assert result["queries_executed"]==0
    assert result["status"]=="requires_explicit_user_approval"


def test_opt_in_aggregates_hardcoded_and_byte_limited(monkeypatch):
    from dataforge.cloud_validation import audit_opt_in_aggregates
    class FakeConfig:
        def __init__(self,**kwargs):
            assert kwargs["maximum_bytes_billed"] <= 100_000_000
            assert not kwargs["dry_run"]
    class FakeClient:
        def query(self,sql,job_config,location):
            assert sql.startswith("SELECT COUNT(*) AS tested_customers")
            assert "`demo-project.datapulse_ai.paired_prediction_replay`" in sql
            assert "DROP" not in sql
            return SimpleNamespace(result=lambda **kwargs: [SimpleNamespace(tested_customers=1500,prediction_flips=340)])
    mock_google_sdk(monkeypatch, "bigquery", SimpleNamespace(QueryJobConfig=FakeConfig))
    r=audit_opt_in_aggregates(FakeClient(),"demo-project",approved_by_user=True)
    assert r["queries_executed"]==1
    assert r["prediction_flips"]==340


def test_pubsub_metadata_only(monkeypatch):
    from dataforge.cloud_validation import audit_pubsub_topology
    class Pub:
        def __init__(self, credentials=None): pass
        def topic_path(self,p,n): return f"projects/{p}/topics/{n}"
        def get_topic(self,request): pass
    class Sub:
        def __init__(self,credentials=None): pass
        def subscription_path(self,p,n): return f"projects/{p}/subscriptions/{n}"
        def get_subscription(self,request):
            return SimpleNamespace(topic="projects/demo-project/topics/datapulse-incidents")
    mock_google_sdk(monkeypatch, "pubsub_v1", SimpleNamespace(PublisherClient=Pub,SubscriberClient=Sub))
    result=audit_pubsub_topology("demo-project")
    assert result["status"]=="passed"
    assert result["messages_published"]==0
    assert result["messages_acknowledged"]==0


@pytest.mark.parametrize("status,expected", [
    (401, "token authentication"),
    (402, "inference credits"),
    (403, "token permission"),
    (404, "model or inference provider"),
    (429, "rate limit"),
    (503, "temporarily unavailable"),
])
def test_hosted_qwen_reports_safe_http_failure(status, expected):
    answer = ask_public(make_public_engine(), "Explain incident DP-REPO-SYN-001",
                        project_id="datapulse-repo-snapshot")
    def provider_failure(url, **kwargs):
        http = requests.Response()
        http.status_code = status
        def fail():
            raise requests.HTTPError("unsafe private provider body", response=http)
        return SimpleNamespace(status_code=status, raise_for_status=fail)
    out = grounded_hosted_summary(answer, "Explain incident", "hf_private_secret123",
                                  post=provider_failure)
    assert out.model_backend == "deterministic"
    note = out.uncertainty_notes[-1]
    assert "HTTP " + str(status) in note
    assert expected in note
    assert "unsafe private provider body" not in note
    assert "hf_private_secret123" not in note


def test_hosted_qwen_normalizes_thousands_separator_and_known_percentage():
    answer = ask_public(make_public_engine(), "Explain incident DP-REPO-SYN-001",
                        project_id="datapulse-repo-snapshot")
    def response_fn(url, **kwargs):
        text = ("The synthetic record shows 340 flips in 1,500 replay customers "
                "(22.67%). The feature definition is a hypothesis, not confirmed.")
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": text}}]},
        )
    out = grounded_hosted_summary(answer, "Explain incident", "hf_fake_test_token",
                                  post=response_fn)
    assert out.model_backend == "qwen-hosted"
    assert "22.67%" in out.answer
    assert "Verified record" in out.answer


def test_hosted_qwen_rejection_explains_numeric_grounding_not_provider():
    answer = ask_public(make_public_engine(), "Explain incident DP-REPO-SYN-001",
                        project_id="datapulse-repo-snapshot")
    def bad_number(url, **kwargs):
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": "The incident harmed 999999 people."}}]},
        )
    out = grounded_hosted_summary(answer, "Explain incident", "hf_fake_test_token",
                                  post=bad_number)
    assert out.model_backend == "deterministic"
    assert "grounding check rejected" in out.uncertainty_notes[-1]
    assert "999999" not in out.answer


def test_hosted_qwen_network_timeout_is_safely_categorized():
    answer = ask_public(make_public_engine(), "Explain incident DP-REPO-SYN-001",
                        project_id="datapulse-repo-snapshot")
    def timeout(url, **kwargs):
        raise requests.Timeout("private request URL or token should stay hidden")
    out = grounded_hosted_summary(answer, "Explain incident", "hf_fake_test_token",
                                  post=timeout)
    assert out.model_backend == "deterministic"
    assert "network timeout" in out.uncertainty_notes[-1]
    assert "private request" not in out.uncertainty_notes[-1]
