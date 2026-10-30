"""Settings with no implicit network or production access."""
from dataclasses import dataclass
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]


def _resolve_path(name: str, fallback: str) -> Path:
    value = Path(os.getenv(name, fallback)).expanduser()
    return (ROOT / value).resolve() if not value.is_absolute() else value.resolve()


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    knowledge_dir: Path
    project_id: str
    model_backend: str
    enable_bigquery_dry_run: bool
    bigquery_max_bytes: int


def get_settings() -> Settings:
    return Settings(
        data_dir=_resolve_path("DATAFORGE_DATA_DIR", "data/demo"),
        knowledge_dir=_resolve_path("DATAFORGE_KNOWLEDGE_DIR", "knowledge"),
        project_id=os.getenv("DATAFORGE_PROJECT_ID", "datapulse-demo"),
        model_backend=os.getenv("DATAFORGE_MODEL_BACKEND", "deterministic").lower(),
        enable_bigquery_dry_run=os.getenv("DATAFORGE_ENABLE_BIGQUERY_DRY_RUN", "false").lower() == "true",
        bigquery_max_bytes=int(os.getenv("DATAFORGE_BIGQUERY_MAX_BYTES", "100000000")),
    )
