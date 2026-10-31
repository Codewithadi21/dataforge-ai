# DataForge AI — Phase 2–4 test report

Local Python verification after new implementation:

- `python -m pytest -q`: **49 tests passed** (including original MVP, independent DataPulse upstream snapshot, Qwen HTTP mock, hallucinated-numeric rejection, GitHub refresh validation, BigQuery dry-run mock, no-approval aggregate guard, and Pub/Sub metadata mock).
- `python -m dataforge.cli eval --output eval/latest_results.json`: **26/26** deterministic routing/citation golden cases passed. This does **not** demonstrate external Qwen accuracy.
- `python -m compileall -q ui dataforge`: passed.

**Not locally tested with real credentials:** Hugging Face hosted Qwen request, Streamlit Secrets and Streamlit post-deploy runtime, Google BigQuery table existence, GCP dry runs/aggregate data, Pub/Sub topology, full end-to-end DataPulse streaming delivery. The local test environment did not have cloud credentials and tests used mocks.

GitHub Actions CI runs on push and pull requests. Check the latest run before claiming a passing remote build.
