"""Registrations are project-scoped; no cross-project retrieval."""
from .base import ProjectAdapter

class ConnectorRegistry:
    def __init__(self) -> None:
        self._registered: dict[str, ProjectAdapter] = {}

    def register(self, adapter: ProjectAdapter) -> None:
        if adapter.project_id in self._registered:
            raise ValueError(f"Duplicate project id: {adapter.project_id}")
        self._registered[adapter.project_id] = adapter

    def get(self, project_id: str) -> ProjectAdapter:
        if project_id not in self._registered:
            raise KeyError(f"Project not registered: {project_id}")
        return self._registered[project_id]

    def available(self) -> list[str]:
        return list(self._registered)
