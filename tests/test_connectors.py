from pathlib import Path
import pytest
from dataforge.connectors.registry import ConnectorRegistry
from dataforge.connectors.datapulse import DataPulseAdapter


def test_fixture_data_is_not_claimed_real(engine):
    adapter = engine.registry.get("datapulse-demo")
    assert adapter.get_project_overview()["synthetic"] is True
    assert adapter.get_incident("DP-SYN-001")["synthetic"] is True
    assert adapter.get_incident("missing") is None
    assert adapter.get_schema("unknown") is None


def test_adapter_never_executes_query(engine):
    adapter = engine.registry.get("datapulse-demo")
    with pytest.raises(PermissionError):
        adapter.execute_read_only_query("SELECT 1", dry_run=False)
    with pytest.raises(RuntimeError):
        adapter.execute_read_only_query("SELECT 1", dry_run=True)


def test_registry_is_project_agnostic(engine):
    registry = ConnectorRegistry()
    class OtherAdapter:
        project_id = "other"
    instance = OtherAdapter()
    registry.register(instance)
    assert registry.get("other") is instance
    with pytest.raises(ValueError):
        registry.register(instance)
    with pytest.raises(KeyError):
        registry.get("datapulse-demo")
