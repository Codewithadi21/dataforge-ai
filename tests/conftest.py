from pathlib import Path
import pytest
from dataforge.config import Settings
from dataforge.assistant.engine import DataForgeEngine

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def engine():
    return DataForgeEngine(Settings(
        data_dir=ROOT / "data/demo", knowledge_dir=ROOT / "knowledge",
        project_id="datapulse-demo", model_backend="deterministic",
        enable_bigquery_dry_run=False, bigquery_max_bytes=100000000,
    ))
