# DataForge AI

**A reusable, evidence-grounded Data Engineering Copilot** · local-first · read-only · separate from DataPulse AI

DataForge AI helps engineers investigate pipeline and model incidents, read project documentation with source references, trace declared data lineage and draft narrowly validated BigQuery SELECT queries. Its first connector is designed for exported DataPulse evidence, but its registry is reusable for other projects. The first release ships with **synthetic demonstration records** and does not modify the DataPulse repository.


## Publish from GitHub without running a laptop

A public, **synthetic-only** Streamlit Cloud entrypoint is included at `ui/cloud_app.py`, with root `requirements.txt`, `.streamlit/config.toml`, and explicit tests that prevent reading private evidence or invoking cloud/Qwen services. Read **[deployment guide](docs/DEPLOYMENT.md)** to create an independent GitHub repository, deploy the online app, and distinguish the working public demo from a future hosted Qwen inference service. The hosted app does not need a separate FastAPI server.

## Product preview

| Mode | Working baseline | Evidence / trust boundary |
|---|---|---|
| Incident RCA | Fixed structured incident report and caveats | Cites synthetic incident ID, source path, metric record |
| Knowledge guide | Approved-document TF-IDF search | Cited Markdown paths and section IDs |
| Lineage | Declared source-to-model graph explanation | Synthetic lineage metadata; not verified job execution |
| SQL assistant | Strict single-table SELECT templates and policy | Approved schemas, column checks, LIMIT policy; no SQL execution |
| API + UI | FastAPI and Streamlit | Run locally; default backend deterministic |
| Qwen model | Optional 1.5B pretrained Qwen adapter | Must download/run separately; untested locally in build environment |
| Cloud | Optional Google BigQuery **dry-run only** | Disabled by default; needs approved credentials and actual tables |

**Never claim** this is a trained-from-scratch foundation model, a deployed Vertex AI pipeline, or a live DataPulse integration until corresponding execution is independently verified.

## Get started in 5 commands

Requirements: Python 3.10+ (3.11 recommended). From the unzipped `dataforge-ai/` directory:

```bash
python -m venv .venv
# Activate .venv: Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev,ui]"
python -m pytest -q
python -m dataforge.cli ask "Why did the churn model behave differently?"
```

Open **two terminals** in this folder, with the environment activated:

```bash
# Terminal 1 — local only
python -m uvicorn dataforge.api:app --host 127.0.0.1 --port 8000
```

```bash
# Terminal 2 — local only
python -m streamlit run ui/streamlit_app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501` in your browser. FastAPI OpenAPI docs are at `http://127.0.0.1:8000/docs`.

## Without UI: 4 working commands

```bash
python -m dataforge.cli ask "What is paired model replay?"
python -m dataforge.cli ask "Trace lineage for engagement_score"
python -m dataforge.cli ask "Write a SQL query for customers whose predictions flipped"
python -m dataforge.cli eval --output eval/latest_results.json
```

Run the 26-case evaluation after installation and inspect the printed totals. **Its metric is routing and source-citation coverage, not answer accuracy.**

## Colab route without paid Gemini API credits

Open `notebooks/01_DataForge_Colab.ipynb` on Google Colab. Upload the provided project ZIP when the first cell requests it. Install editable dependencies, run tests, run the synthetic incident demo, and optionally install Qwen model packages. The default path requires no API keys and does not create cloud resources. Model downloads may be large and GPU access is never guaranteed on the free tier.

## Optional local Qwen2.5-1.5B-Instruct

```bash
python -m pip install -e ".[qwen]"
# PowerShell:
$env:DATAFORGE_MODEL_BACKEND="qwen"
# macOS/Linux: export DATAFORGE_MODEL_BACKEND=qwen
python -m dataforge.cli ask "Explain incident DP-SYN-001"
```

This downloads pretrained weights when first run; model setup was not executed in the artifact build environment. If model loading fails, the system returns deterministic evidence with a note. No paid Gemini Developer API key is involved.

## Optional BigQuery dry run — no live queries

**Read `docs/SECURITY.md` before connecting a Google Cloud project.** Install `.[cloud]`, authenticate with Application Default Credentials, export `DATAFORGE_ENABLE_BIGQUERY_DRY_RUN=true` (PowerShell: `$env:DATAFORGE_ENABLE_BIGQUERY_DRY_RUN="true"`), then issue an SQL request with `--cloud-dry-run`. Replace demo table IDs with explicitly approved real schema IDs only after a scoped credentials review. The app never executes a live query. BigQuery dry runs can require permissions and the reported estimate is not a billing cap.

## Project layout

```text
dataforge-ai/
├── dataforge/
│   ├── api.py                    # FastAPI + Pydantic
│   ├── cli.py                    # Offline Q&A and evaluation
│   ├── assistant/               # Routing and evidence synthesis
│   ├── connectors/              # Stable project protocol + DataPulse JSON adapter
│   ├── models/                  # Optional local Qwen inference adapter
│   ├── retrieval/               # TF-IDF, chunking, citations
│   └── sql_tools/               # Narrow SELECT grammar, optional dry-run
├── ui/streamlit_app.py
├── data/demo/                    # Explicit synthetic fixtures
├── knowledge/                    # Approved project documentation
├── tests/                        # Safety, API and connector tests
├── eval/                         # 26 curated golden routing/citation cases
├── notebooks/                    # Reproducible Colab path
├── docs/                         # Architecture, adapter, security, walkthrough
└── .github/workflows/tests.yml   # CI configuration (not yet proven on GitHub)
```

## When you're ready to connect your *actual* DataPulse

Read `docs/ADAPTER_CONTRACT.md`. Export approved JSON incident metrics and lineage to a new folder without editing DataPulse source code. Point `DATAFORGE_DATA_DIR` there; ensure its project ID matches `DATAFORGE_PROJECT_ID`. Real integration and all output claims need validation against the actual DataPulse records. No GitHub repository has been created or modified by this package.

## What's intentionally not included

Large-scale embedding-based RAG, FAISS, LoRA fine-tuning, autonomous SQL execution, remediation tools, model retraining, Vertex AI / Cloud Run deployment, live Pub/Sub ingestion, authentication for production, and independent groundedness evaluation. The blueprint's M7 tuning phase is future work and should only follow measured baseline failures.

## Supporting files

- `docs/ARCHITECTURE.md`: system diagram and trust boundaries.
- `docs/ADAPTER_CONTRACT.md`: how to connect real DataPulse JSON.
- `docs/SECURITY.md`: privacy, SQL restrictions and deployment caveats.
- `docs/DEMO_WALKTHROUGH.md`: reproducible portfolio demo.
- `docs/PORTFOLIO.md`: recruiter- and technical-interview versions.

*Concept and requirements from the user-provided DataForge AI Future Project Blueprint (30 October 2026); software implementation created as an independent MVP.*
