"""Public-demo-only adapter: never loads private data or enables live cloud access."""
from dataforge.assistant.engine import DataForgeEngine
from dataforge.config import ROOT, Settings
from dataforge.schemas import AskRequest, AskResponse


def make_public_engine() -> DataForgeEngine:
    """Ignore runtime environment variables and use only committed synthetic fixtures.

    This configuration intentionally does not run Qwen. Model inference belongs on
    a separate, explicitly configured service with appropriate access controls.
    """
    settings = Settings(
        data_dir=ROOT / "data" / "demo",
        knowledge_dir=ROOT / "knowledge",
        project_id="datapulse-demo",
        model_backend="deterministic",
        enable_bigquery_dry_run=False,
        bigquery_max_bytes=0,
    )
    return DataForgeEngine(settings)


def ask_public(engine: DataForgeEngine, question: str, sql: str | None = None,
               project_id: str = "datapulse-demo") -> AskResponse:
    """Honor the read-only policy; never accept a cloud request from the public UI."""
    return engine.ask(AskRequest(
        question=question,
        project_id=project_id if project_id in {"datapulse-demo", "datapulse-repo-snapshot"} else "unsupported",
        sql=sql,
        cloud_dry_run=False,
    ))
