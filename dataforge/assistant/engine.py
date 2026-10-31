"""The safe, evidence-first orchestration layer."""
import re
from uuid import uuid4
from dataforge.config import ROOT, Settings, get_settings
from dataforge.schemas import AskRequest, AskResponse, Citation
from dataforge.connectors.datapulse import DataPulseAdapter
from dataforge.connectors.registry import ConnectorRegistry
from dataforge.retrieval.index import DocumentIndex
from dataforge.sql_tools.guard import SQLPolicyError, validate_sql, draft_sql
from dataforge.sql_tools.bigquery_dryrun import dry_run
from .router import classify

class DataForgeEngine:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.registry = ConnectorRegistry()
        self.registry.register(DataPulseAdapter(self.settings.data_dir, self.settings.project_id))
        # Separate approved seeded snapshot from the illustrative demo; never mix metrics.
        if self.settings.project_id != "datapulse-repo-snapshot":
            self.registry.register(DataPulseAdapter(ROOT / "data" / "datapulse_repo_snapshot", "datapulse-repo-snapshot"))
        self.index = DocumentIndex(self.settings.knowledge_dir)
        self._qwen = None  # Load 1.5B model only if explicitly enabled/requested.

    @staticmethod
    def _citation(id: str, path: str, section: str | None = None, synthetic: bool = False) -> Citation:
        return Citation(source_id=id, path=path, section=section, synthetic=synthetic)

    def _maybe_synthesize(self, response: AskResponse, question: str) -> AskResponse:
        if self.settings.model_backend != "qwen" or not response.supporting_sources:
            return response
        try:
            if self._qwen is None:
                from dataforge.models.qwen import QwenAdapter
                self._qwen = QwenAdapter()
            narrative = self._qwen.synthesize(response.answer, question)
            # Conservative numeric check catches invented numeric values, but is not a
            # comprehensive hallucination detector. The deterministic record remains attached.
            numbers = lambda s: set(re.findall(r"(?<!\w)\d+(?:\.\d+)?%?(?!\w)", s))
            if not narrative or not numbers(narrative).issubset(numbers(response.answer)):
                response.uncertainty_notes.append("Qwen output rejected by numeric grounding check; deterministic answer retained.")
                return response
            response.answer = "LLM summary (review against cited evidence):\n" + narrative + "\n\nVerified record:\n" + response.answer
            response.model_backend = "qwen-local"
            response.uncertainty_notes.append("LLM narrative is not guaranteed factually correct; verify each claim against the cited record.")
        except Exception:
            response.uncertainty_notes.append("Local Qwen unavailable; returned deterministic evidence instead. Check model setup locally.")
        return response

    def ask(self, request: AskRequest) -> AskResponse:
        trace = uuid4().hex[:12]
        adapter = self.registry.get(request.project_id)
        intent = classify(request.question, request.sql)
        base = dict(execution_trace_id=trace, intent=intent)
        if intent == "sql":
            try:
                sql = request.sql if request.sql else draft_sql(request.question, adapter)
                check = validate_sql(sql, adapter)
                if request.cloud_dry_run:
                    check["cloud"] = dry_run(sql, adapter, self.settings.enable_bigquery_dry_run,
                                             self.settings.bigquery_max_bytes)
                table = check["table"]
                return AskResponse(
                    answer="A restricted SELECT draft was validated against approved schema metadata. "
                           "No SQL query was executed. Review the SQL and dry-run status before use.",
                    sql_draft=sql, sql_check=check,
                    supporting_sources=[self._citation("schema:" + table, "adapter:schemas.json", table, bool((adapter.get_schema(table) or {}).get("synthetic", adapter.get_project_overview().get("synthetic", False))))],
                    evidence_ids=["schema:" + table], retrieval_mode="schema-policy", **base,
                )
            except SQLPolicyError as exc:
                return AskResponse(answer=f"SQL rejected: {exc}",
                    uncertainty_notes=["User SQL is not executed; this MVP supports only the restricted single-table SELECT grammar."],
                    retrieval_mode="schema-policy", sql_check={"status": "rejected", "read_only": False}, **base)

        if intent == "incident":
            incidents = adapter.list_incidents()
            requested = next((i for i in incidents if str(i.get("incident_id", "")).lower() in request.question.lower()), None)
            incident = requested or (incidents[0] if incidents else None)
            if incident is None:
                return AskResponse(answer="Not established: no approved incident evidence is available.",
                                   uncertainty_notes=["No verified incident export connected."], **base)
            metrics = incident.get("metrics", {})
            metrics_txt = "; ".join(f"{k}={v}" for k, v in metrics.items()) or "not recorded"
            hypotheses = incident.get("hypotheses", [])
            answer = (f"Incident {incident['incident_id']}: {incident.get('summary', 'No summary recorded')}\n"
                      f"Observed evidence: {metrics_txt}.\n"
                      f"Hypothesis (not confirmed cause): {'; '.join(hypotheses) or 'none recorded'}.\n"
                      f"Scope: {'synthetic example' if incident.get('synthetic') else 'exported record'}; "
                      "an observed drift alone does not prove model harm.")
            resp = AskResponse(answer=answer,
                supporting_sources=[self._citation("incident:" + incident["incident_id"], (incident.get("source_urls") or ["adapter:incidents.json"])[0], "incident", bool(incident.get("synthetic")))],
                evidence_ids=list(incident.get("evidence_ids", [])),
                uncertainty_notes=["Root cause has not been established; reported hypotheses require investigation."],
                recommended_checks=list(incident.get("recommended_checks", [])),
                requires_human_approval=True, retrieval_mode="structured-incident", **base)
            return self._maybe_synthesize(resp, request.question)

        if intent == "lineage":
            entities = adapter.list_lineage_entities() if hasattr(adapter, "list_lineage_entities") else []
            selected = None
            for e in entities:
                record = adapter.get_lineage(e)
                names = [e] + (record.get("aliases", []) if record else [])
                if any(str(n).lower().replace("_", " ") in request.question.lower().replace("_", " ") for n in names):
                    selected = record
                    break
            if selected is None and entities and any(w in request.question.lower() for w in ("lineage", "upstream", "trace")):
                selected = adapter.get_lineage(entities[0])
            if not selected:
                return AskResponse(answer="Not established: this entity has no approved lineage record.",
                    uncertainty_notes=["No source-to-decision path documented for the named entity."],
                    retrieval_mode="declared-lineage", **base)
            path = selected.get("nodes", [])
            resp = AskResponse(answer=f"Declared lineage for {selected['entity']}:\n" + " -> ".join(str(n) for n in path)
                + "\nThis is declared metadata, not independently verified runtime lineage.",
                supporting_sources=[self._citation("lineage:" + selected["entity"], selected.get("source_url", "adapter:lineage.json"), selected["entity"], bool(adapter.get_project_overview().get("synthetic", False)))],
                evidence_ids=["lineage:" + selected["entity"]],
                uncertainty_notes=["Validate declared edges against executed code and warehouse metadata."],
                retrieval_mode="declared-lineage", **base)
            return self._maybe_synthesize(resp, request.question)

        matches = self.index.search(request.question)
        if not matches:
            return AskResponse(answer="Not established: no reliable evidence was found in authorized project documentation.",
                uncertainty_notes=["Connect an approved document or provide a more specific project question."],
                retrieval_mode="tfidf", intent="unsupported", execution_trace_id=trace)
        citations = [self._citation(c.source_id, c.path, c.section) for c, _ in matches]
        sections = [f"[{c.source_id}] {c.section}: {c.text[:600]}" for c, _ in matches]
        resp = AskResponse(answer="Retrieved project documentation (source excerpts):\n" + "\n\n".join(sections),
            supporting_sources=citations, evidence_ids=[x.source_id for x, _ in matches],
            uncertainty_notes=["Excerpts are relevant retrieval matches, not proof of every inferred conclusion."],
            retrieval_mode="tfidf", **base)
        return self._maybe_synthesize(resp, request.question)
