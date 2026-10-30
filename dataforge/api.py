"""Local-first API. Do NOT expose publicly without authentication and network controls."""
from functools import lru_cache
from fastapi import FastAPI, HTTPException
from dataforge.assistant.engine import DataForgeEngine
from dataforge.schemas import AskRequest, AskResponse

app = FastAPI(title="DataForge AI", version="0.1.0", description="Read-only evidence-grounded copilot")

@lru_cache(maxsize=1)
def engine() -> DataForgeEngine:
    return DataForgeEngine()

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": engine().settings.model_backend,
            "projects": engine().registry.available(), "live_sql_execution": False}

@app.get("/projects")
def projects() -> dict:
    return {"projects": engine().registry.available()}

@app.get("/projects/{project_id}/incidents")
def incidents(project_id: str) -> dict:
    try:
        return {"incidents": [i["incident_id"] for i in engine().registry.get(project_id).list_incidents()]}
    except KeyError:
        raise HTTPException(404, detail="Unknown project") from None

@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        return engine().ask(request)
    except KeyError:
        raise HTTPException(404, detail="Unknown project") from None
