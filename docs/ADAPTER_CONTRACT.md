# Stable project adapter contract

Every project is registered with a unique `project_id`. DataForge cannot silently fall back to another project when a requested ID is missing.

| Method | Return | Notes |
|---|---|---|
| `get_project_overview()` | project JSON | Includes project ID, environment, sources and version |
| `list_incidents()` | list of incident dicts | Incident ID must be unique and stable |
| `get_incident(id)` | dict or None | Evidence must come from an external deterministic report |
| `get_lineage(entity)` | dict or None | Clearly distinguish declared from observed edges |
| `list_available_tables()` | list of fully qualified table IDs | Only approved identifiers |
| `get_schema(table)` | dict or None | Include columns and sensitivity classification |
| `execute_read_only_query(sql, dry_run=True)` | dict or exception | Deliberately unavailable in the example; use separate guarded BigQuery tool |

## Export layout

A valid data folder requires four JSON files. See `data/demo` for fully reproducible examples:

- `project.json` with `project_id`, `name`, `synthetic`, `allowed_sources`, `environment`.
- `incidents.json` list of `{incident_id, detected_at, summary, incident_type, synthetic, metrics, hypotheses, evidence_ids, recommended_checks}`.
- `lineage.json` with `paths` list of `{entity, aliases, nodes, lineage_type, limitations}`.
- `schemas.json` keyed by fully qualified BigQuery table name and containing `{description, columns: [{name, type, sensitivity}]}`.

The blueprint describes existing DataPulse `investigate(summary)` with `incident_type`, `evidence`, `recommended_action`, and `approval flag`. Its **actual serialized output structure is not available here**. Map it explicitly to this contract after examining the real JSON; do not assume a fabricated field is present or substitute invented replay values. The sample numeric metrics here are **illustrative only**.

## Additional project connectors

Implement the `dataforge.connectors.base.ProjectAdapter` protocol and register an adapter with `ConnectorRegistry`. Do not add blanket filesystem scans or import private application internals. Keep retrieval indices and schema allowlists separate per project before any multi-tenant use.
