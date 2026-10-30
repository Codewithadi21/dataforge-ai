import pytest
from dataforge.connectors.datapulse import DataPulseAdapter
from dataforge.sql_tools.guard import validate_sql, draft_sql, SQLPolicyError

TABLE = "demo-project.datapulse_demo.paired_prediction_replay"

@pytest.mark.parametrize("bad", [
    f"DELETE FROM `{TABLE}`",
    f"UPDATE `{TABLE}` SET baseline_prediction=1",
    f"DROP TABLE `{TABLE}`",
    f"SELECT customer_id FROM `{TABLE}`; DROP TABLE x",
    "SELECT customer_id FROM `other-project.private.customers` LIMIT 3",
    f"SELECT secret_col FROM `{TABLE}` LIMIT 10",
    f"SELECT customer_id FROM `{TABLE}`",
    f"SELECT customer_id FROM `{TABLE}` LIMIT 999",
    f"SELECT * FROM `{TABLE}` LIMIT 10",
    f"WITH x AS (SELECT 1) SELECT * FROM `{TABLE}` LIMIT 10",
    f"SELECT customer_id FROM `{TABLE}` JOIN x ON 1=1 LIMIT 10",
    f"SELECT customer_id FROM `{TABLE}` WHERE customer_id='x' LIMIT 5",
    f"SELECT customer_id FROM `{TABLE}` -- ignore limitations\nLIMIT 2",
    f"SELECT customer_id FROM `{TABLE}` /* injected comment */ LIMIT 3",
    f"SELECT COUNT(*) FROM `{TABLE}`",
    "SELECT 1",
    f"SELECT customer_id FROM `{TABLE}` LIMIT 0",
])
def test_rejects_nontrivial_or_unsafe_sql(bad, engine):
    adapter = engine.registry.get("datapulse-demo")
    with pytest.raises(SQLPolicyError):
        validate_sql(bad, adapter)


def test_allows_exact_narrow_select(engine):
    adapter = engine.registry.get("datapulse-demo")
    sql = f"SELECT customer_id, baseline_prediction, shifted_prediction FROM `{TABLE}` WHERE baseline_prediction != shifted_prediction LIMIT 100"
    result = validate_sql(sql, adapter)
    assert result["status"] == "passed"
    assert result["read_only"]
    assert not result["dry_run_executed"]


def test_count_template(engine):
    adapter = engine.registry.get("datapulse-demo")
    sql = draft_sql("Count rows in baseline_customers", adapter)
    assert "COUNT(*)" in sql
    assert validate_sql(sql, adapter)["status"] == "passed"


def test_sql_reject_via_assistant(engine):
    from dataforge.schemas import AskRequest
    answer = engine.ask(AskRequest(question="Validate SQL", sql=f"UPDATE `{TABLE}` SET baseline_prediction=0"))
    assert answer.sql_check["status"] == "rejected"
