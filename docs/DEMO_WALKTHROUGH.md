# Reproducible demonstration (local)

Run the README setup first, then try these scenarios in Streamlit or the CLI.

## 1. Incident investigator
`python -m dataforge.cli ask "Why did the churn model behave differently?"`

Expected: `DP-SYN-001` synthetic incident, fixed-cohort metrics, recorded hypothesis (not proven cause), source `adapter:incidents.json` and explicit human approval boundary. Note that 82 flips / 1,000 customers and PSI 0.26 are synthetic fixtures, not real DataPulse observations.

## 2. Data lineage
`python -m dataforge.cli ask "Trace lineage for engagement_score"`

Expected: producer events -> raw -> curated feature -> model -> replay plus `adapter:lineage.json` provenance and warning that declared edges require code validation.

## 3. Project guide
`python -m dataforge.cli ask "How does DataPulse work?"`

Expected: approved document excerpts with `knowledge/...md` paths, source IDs and retrieval mode `tfidf`. The offline baseline does not invent a full free-form LLM answer.

## 4. SQL policy
`python -m dataforge.cli ask "Show customers whose predictions flipped with SQL"`

Expected: fully qualified demo table `demo-project.datapulse_demo.paired_prediction_replay`, a single SELECT with LIMIT 100 and schema-policy pass. No query is executed. Try a malicious SQL via:

`python -m dataforge.cli ask "Check my SQL" --sql 'DELETE FROM \`demo-project.datapulse_demo.paired_prediction_replay\`'`

Expected: rejected. On shells with special quoting rules, paste SQL in the Streamlit UI instead.

## 5. Model failure recovery
Keep `DATAFORGE_MODEL_BACKEND=deterministic`. This offline fallback is intentional. On a machine with sufficient resources, opt in to Qwen and compare its narrative with the attached evidence. Do not claim pretrained model loading until you observe actual output.

## 6. Evaluation proof
`python -m pytest -q`

`python -m dataforge.cli eval --output eval/latest_results.json`

The golden file contains 26 questions. The evaluator checks intent and provenance only, not factual accuracy or trustworthy real-world causality.
