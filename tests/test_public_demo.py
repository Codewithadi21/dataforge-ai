"""Ensure the remotely deployable demo cannot inherit cloud or model credentials."""
from pathlib import Path
from dataforge.hosted import make_public_engine, ask_public


def test_public_demo_forces_synthetic_evidence(monkeypatch):
    monkeypatch.setenv("DATAFORGE_MODEL_BACKEND", "qwen")
    monkeypatch.setenv("DATAFORGE_ENABLE_BIGQUERY_DRY_RUN", "true")
    monkeypatch.setenv("DATAFORGE_DATA_DIR", "/tmp/unauthorized")
    e = make_public_engine()
    assert e.settings.model_backend == "deterministic"
    assert e.settings.enable_bigquery_dry_run is False
    assert e.settings.data_dir.name == "demo"
    assert e.settings.data_dir.is_relative_to(Path(__file__).resolve().parents[1])
    result = ask_public(e, "Explain incident DP-SYN-001")
    assert result.supporting_sources
    assert result.supporting_sources[0].synthetic is True
    assert result.model_backend == "deterministic"


def test_public_sql_does_not_execute_cloud():
    e = make_public_engine()
    result = ask_public(e, "Count rows in baseline_customers")
    assert result.sql_check
    assert "cloud" not in result.sql_check
    result = ask_public(e, "Preview shifted_customers", "DELETE FROM x")
    assert result.sql_check["status"] == "rejected"
