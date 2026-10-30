# Portfolio and interview proof guide

## Recruiter-friendly description (after local reproduction)

DataForge AI is a prototype, evidence-grounded data engineering assistant that supports synthetic incident RCA, source-cited project documentation retrieval, declared data lineage explanations and restricted BigQuery SQL drafting using Python, FastAPI and Streamlit. It is designed around a reusable connector contract so future projects can supply their own records.

## Technical interview walkthrough

Show the API route, request/response Pydantic schemas, TF-IDF retrieval provenance, JSON incident evidence, strict SQL grammar, separate BigQuery dry-run switch, tests and golden evaluation. Explain why retrieving a document is not a guarantee of truth, why semantic drift is different from schema drift, and why the fixed-cohort replay comparison is not proof of causal business harm.

## Truthful project bullets (only after rerunning tests yourself)

- Built a modular Python/FastAPI Data Engineering Copilot with a Streamlit UI and typed, source-cited evidence responses for incident analysis, lineage and runbooks.
- Implemented a project-scoped DataPulse JSON adapter and TF-IDF retrieval over approved documentation, with deterministic fallback when a local LLM is unavailable.
- Designed restricted BigQuery SELECT generation, schema/table allow-list checks, opt-in dry-run integration and automated tests for unsafe SQL rejection.

## Do not claim yet

No own foundation model, no fine-tuned weights, no deployed Vertex AI service, no real BigQuery query runs, no fully live DataPulse pipeline integration, no independent accuracy validation and no verified cloud deployment. Add these only after measuring them and storing execution evidence.
