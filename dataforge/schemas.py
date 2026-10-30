"""Typed public API contract (matches the handoff blueprint)."""
from typing import Any, Literal
from pydantic import BaseModel, Field

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1500)
    project_id: str = "datapulse-demo"
    sql: str | None = Field(default=None, max_length=4000)
    cloud_dry_run: bool = False

class Citation(BaseModel):
    source_id: str
    path: str
    section: str | None = None
    synthetic: bool = False

class AskResponse(BaseModel):
    answer: str
    supporting_sources: list[Citation] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    uncertainty_notes: list[str] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    model_backend: str = "deterministic"
    retrieval_mode: str = "none"
    execution_trace_id: str
    intent: Literal["incident", "guide", "lineage", "sql", "unsupported"]
    sql_draft: str | None = None
    sql_check: dict[str, Any] | None = None
