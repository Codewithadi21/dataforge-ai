# Local verification report

Verified in the artifact-building runtime on 30 October 2026.

- Python: 3.13.5 (Linux)
- Command: `python -m pytest -q`
- Result: **35 passed**
- Golden question evaluation: **26/26 passed** (intent routing and source ID checks)
- Python code: `python -m compileall -q dataforge` completed successfully.
- Manual CLI demonstration: `Show customers whose predictions flipped` returned a strictly scoped, synthetic, approved BigQuery SELECT draft without executing it.

## Not verified by these tests

- No Qwen weights downloaded or Qwen-generated answer validated.
- No live DataPulse data loaded or real DataPulse repo changed.
- No BigQuery API dry-run, Google Cloud credentials, or real tables used.
- Public hosting helper enforces demo-only fixtures, no Qwen/cloud API (2 added safety tests).
- No Streamlit browser session, free-Colab execution, cloud deploy or GitHub Actions run verified.
- Retrieval routing/citation coverage is **not a factual accuracy percentage** and is not an ATS score.

Run the setup yourself, inspect source citations and rerun the suite before publishing project claims.
