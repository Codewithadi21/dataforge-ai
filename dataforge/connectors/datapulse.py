"""File-based DataPulse export connector, never modifies DataPulse."""
from pathlib import Path
from typing import Any
import json

class DataPulseAdapter:
    def __init__(self, data_dir: Path, project_id: str = "datapulse-demo") -> None:
        self.project_id = project_id
        self.data_dir = Path(data_dir).resolve()
        if not self.data_dir.is_dir():
            raise FileNotFoundError(f"Configured DataPulse export folder does not exist: {self.data_dir}")
        self._overview = self._load("project.json")
        self._incidents = self._load("incidents.json")
        self._lineage = self._load("lineage.json")
        self._schemas = self._load("schemas.json")
        if not isinstance(self._incidents, list) or not isinstance(self._schemas, dict):
            raise ValueError("Expected incidents.json list and schemas.json mapping")
        if self._overview.get("project_id") != project_id:
            raise ValueError("Adapter project_id disagrees with exported project.json")

    def _load(self, name: str) -> Any:
        # Only static, known JSON filenames; no user-controlled path traversal.
        path = self.data_dir / name
        return json.loads(path.read_text(encoding="utf-8"))

    def get_project_overview(self) -> dict[str, Any]:
        return dict(self._overview)

    def list_incidents(self) -> list[dict[str, Any]]:
        return list(self._incidents)

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        return next((i for i in self._incidents if i.get("incident_id") == incident_id), None)

    def get_lineage(self, entity: str) -> dict[str, Any] | None:
        items = self._lineage.get("paths", [])
        for item in items:
            if entity.lower() in {str(v).lower() for v in item.get("aliases", [])} | {str(item.get("entity", "")).lower()}:
                return dict(item)
        return None

    def list_lineage_entities(self) -> list[str]:
        return [str(x.get("entity")) for x in self._lineage.get("paths", [])]

    def list_available_tables(self) -> list[str]:
        return list(self._schemas)

    def get_schema(self, table: str) -> dict[str, Any] | None:
        return self._schemas.get(table)

    def execute_read_only_query(self, sql: str, dry_run: bool = True) -> dict[str, Any]:
        if not dry_run:
            raise PermissionError("DataForge never executes a live SQL query")
        raise RuntimeError("Call the separately guarded BigQueryDryRun tool, not the adapter")
