from fastapi.testclient import TestClient
from dataforge.api import app, engine as api_engine


def test_api_health(monkeypatch, engine):
    api_engine.cache_clear()
    app.dependency_overrides = {}
    monkeypatch.setattr("dataforge.api.engine", lambda: engine)
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["live_sql_execution"] is False


def test_api_ask_and_unknown_project(monkeypatch, engine):
    monkeypatch.setattr("dataforge.api.engine", lambda: engine)
    client = TestClient(app)
    res = client.post("/ask", json={"question": "Explain incident DP-SYN-001"})
    assert res.status_code == 200
    assert res.json()["supporting_sources"]
    bad = client.post("/ask", json={"question": "Explain an incident", "project_id": "private"})
    assert bad.status_code == 404
