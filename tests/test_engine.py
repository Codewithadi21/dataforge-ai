from dataforge.schemas import AskRequest


def test_incident_grounded(engine):
    answer = engine.ask(AskRequest(question="Explain incident DP-SYN-001 and drift metrics"))
    assert answer.intent == "incident"
    assert "prediction_flip_count=82" in answer.answer
    assert "8.2" in answer.answer
    assert "not confirmed cause" in answer.answer
    assert answer.requires_human_approval
    assert answer.supporting_sources[0].synthetic
    assert answer.evidence_ids


def test_lineage_cited(engine):
    answer = engine.ask(AskRequest(question="Trace lineage for engagement_score"))
    assert answer.intent == "lineage"
    assert "raw engagement events" in answer.answer
    assert "declared metadata" in answer.answer
    assert answer.supporting_sources[0].source_id == "lineage:engagement_score"


def test_guide_has_provenance(engine):
    answer = engine.ask(AskRequest(question="How does DataPulse work?"))
    assert answer.intent == "guide"
    assert answer.supporting_sources and answer.retrieval_mode == "tfidf"
    assert all(s.path.startswith("knowledge/") for s in answer.supporting_sources)


def test_unsupported_no_invented_sources(engine):
    answer = engine.ask(AskRequest(question="Who won the cricket World Cup in 1983?"))
    assert answer.intent == "unsupported"
    assert "Not established" in answer.answer
    assert not answer.supporting_sources


def test_unknown_project_does_not_fall_back(engine):
    try:
        engine.ask(AskRequest(question="Explain churn", project_id="another-project"))
    except KeyError:
        pass
    else:
        assert False, "Project boundary must be enforced"


def test_cloud_dryrun_off_by_default(engine):
    answer = engine.ask(AskRequest(question="SQL count rows in baseline_customers", cloud_dry_run=True))
    assert answer.sql_check["status"] == "passed"
    assert answer.sql_check["cloud"]["status"] == "disabled"
    assert answer.sql_check["cloud"]["dry_run_executed"] is False


def test_restricted_sql_template(engine):
    answer = engine.ask(AskRequest(question="Write SQL query for customers whose predictions flipped"))
    assert answer.sql_draft is not None
    assert "WHERE baseline_prediction != shifted_prediction" in answer.sql_draft
    assert answer.sql_check["status"] == "passed"
    assert "No SQL query was executed" in answer.answer


def test_ui_sql_prompts_route_correctly(engine):
    for question in ("Show customers whose predictions flipped", "Preview shifted_customers", "Count rows in baseline_customers"):
        response = engine.ask(AskRequest(question=question))
        assert response.intent == "sql", (question, response.intent)
        assert response.sql_check["status"] == "passed", question
