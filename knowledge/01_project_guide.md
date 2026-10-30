# DataPulse and DataForge project guide
## What is DataForge AI?
DataForge AI is a reusable data engineering copilot. Its role is to retrieve approved documentation, read deterministic incident reports, explain declared lineage, and draft restricted read-only BigQuery SELECT queries. DataPulse AI is the first intended integration; the copilot belongs in a separate repository and must not copy or modify DataPulse business logic.
## How does DataPulse work?
The proposed DataPulse workflow uses synthetic customer-event generation, data-quality and schema-contract checks, an engagement-feature semantic shift, drift monitoring, fixed-cohort replay of a fixed churn prediction model, and a deterministic incident JSON report. DataForge reads exported results; it does not recalculate the ML pipeline or train the model.
## What is paired replay?
A paired model replay compares predictions before and after a feature or data definition changes, while holding the model and customer cohort fixed. It can reveal prediction flips, but prediction flips do not prove model harm or a production outage.
## Getting started with the project
Install Python dependencies, run pytest, start the FastAPI server on 127.0.0.1:8000, then run Streamlit on 127.0.0.1:8501. The synthetic fixture works without Google Cloud credentials or a model download. A future real DataPulse integration must replace the synthetic JSON export and be validated by tests.
## What is implemented in the starter?
Working baseline features are TF-IDF search, deterministic incident explanations, declared lineage, schema-aware restricted SELECT drafts, an optional BigQuery dry-run switch, FastAPI, Streamlit, tests, a golden-query benchmark, and an optional local Qwen2.5-1.5B-Instruct model adapter. Embedding vector search, finetuning, cloud deployment and live Pub/Sub are future work.
