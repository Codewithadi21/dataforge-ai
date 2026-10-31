# DataForge AI — Phase 2, 3 and 4 implementation

## Accurate status (do not inflate portfolio claims)

| Capability | Code | Verified locally | Verified against external service |
|---|---|---|---|
| Qwen via HF router | Yes | Mocked request, grounding fallback and HTTP error path | **Pending HF token, admin unlock and live test** |
| Repository snapshot integration | Yes | Actual public DataPulse seeded metrics matched to the checked-in report | Static snapshot read from upstream repository; **not a live ML run** |
| GitHub upstream refresh | Yes | Schema/rate checks, hostile/invalid response fallback mocked | **Pending manual refresh in Streamlit** |
| Schema-aware SQL planning | Yes | Policy tests passed | No live SQL execution |
| BigQuery metadata and dry-run | Yes | Mocked cloud jobs verify `dry_run=True` | **Pending GCP credentials and manual audit** |
| Optional bounded BigQuery aggregate | Yes | Tests require explicit opt-in and byte limit | **Pending manual Colab approval**; aggregate queries may incur charges |
| Pub/Sub topology | Yes | Topic/subscription readers tested with mocks | **Pending GCP credentials**; no messages pulled or published |
| Live, end-to-end GCP DataPulse pipeline | No — upstream deployment not altered | — | Not claimed |

## Phase 2 — Hosted Qwen

The public Streamlit interface defaults to deterministic evidence. To privately enable hosted inference:

1. Register at https://huggingface.co and create a **fine-grained token with Inference Providers permission**. Keep its value private.
2. Open **Streamlit Community Cloud → My apps → your DataForge app → Settings → Secrets**.
3. Add the following example with your own values (**never commit these secrets or paste them into a public chat**):

```toml
HF_TOKEN = "hf_REPLACE_IN_STREAMLIT_SETTINGS_ONLY"
ADMIN_DEMO_PASSWORD = "REPLACE_WITH_A_LONG_UNIQUE_PASSWORD"
```

4. Save and restart the app if Streamlit prompts you. Enter the admin password in the sidebar; select **Use hosted Qwen on this request** and test an incident explanation. The displayed backend must say `qwen-hosted`. If inference fails, the answer remains deterministic and tells you so.
5. There is a limit of **three Qwen calls per Streamlit browser session**. This is a demo cost guard, **not robust global rate limiting**. Keep the password private; do not enable the public paid model for arbitrary visitors.

The default supported routing model is `Qwen/Qwen3-4B-Instruct-2507:nscale` on Hugging Face Inference Providers. Verify current model/provider availability and pricing in your HF account. The pretrained Qwen2.5-1.5B model in `dataforge/models/qwen.py` remains a **separate local Colab** option. Nothing here claims custom-trained foundation weights or LoRA tuning. HF routing may cost money after any available credit; only enable it on purpose.

Qwen is used **only to interpret deterministic, already-retrieved synthetic evidence**. It cannot propose a new SQL query for execution. Source citations and authoritative numbers remain attached. A conservative numeric gate and error fallback help, but do not guarantee zero hallucinations.

## Phase 3 — DataPulse repository integration

Source repository: https://github.com/Codewithadi21/aegis-real-time-supply-chain-ai/tree/main/datapulse-ai

Actual pinned source commit: `ee4a0683f6f6ebf22da55385343a3b771f18b06c`

- [Seeded replay results](https://github.com/Codewithadi21/aegis-real-time-supply-chain-ai/blob/ee4a0683f6f6ebf22da55385343a3b771f18b06c/datapulse-ai/examples/verified_synthetic_results.json)
- [Declared lineage](https://github.com/Codewithadi21/aegis-real-time-supply-chain-ai/blob/ee4a0683f6f6ebf22da55385343a3b771f18b06c/datapulse-ai/configs/lineage.yml)
- [Data contract](https://github.com/Codewithadi21/aegis-real-time-supply-chain-ai/blob/ee4a0683f6f6ebf22da55385343a3b771f18b06c/datapulse-ai/configs/contracts.yml)
- [Source replay column contract](https://github.com/Codewithadi21/aegis-real-time-supply-chain-ai/blob/ee4a0683f6f6ebf22da55385343a3b771f18b06c/datapulse-ai/datapulse/replay.py)

`data/datapulse_repo_snapshot` is **a copy of the documented seeded synthetic run, not live cloud data**. It is separate from `data/demo`, which contains the illustrative 82/1000 example. Public Streamlit offers a `Refresh DataPulse GitHub evidence` button that reads **only** the approved public JSON file on the upstream repository's `main` branch through a fixed GitHub API URL. It checks metric types, bounds, percentages, and sizes; invalid responses leave the pinned source untouched. Refresh does not run the upstream ML pipeline and does not write to the DataPulse repository.

**Do not conflate the projects:** the source repo is also home to AEGIS supply-chain code, while DataPulse lives under `datapulse-ai/`. DataForge remains independent and never edits the upstream repository.

## Phase 4 — GCP audit using Colab without service-account downloads

Recommended: open [the audit notebook](../notebooks/02_DataForge_GCP_Audit_Colab.ipynb) in Colab from GitHub, sign in to Google Cloud through Colab, specify your actual GCP project ID, and execute the three **dry-run only** table checks. The notebook does **not** store user keys or require a laptop.

Expected BigQuery dataset from DataPulse: `datapulse_ai`; expected tables `baseline_customers`, `shifted_customers`, and `paired_prediction_replay`. Expected Pub/Sub topic `datapulse-incidents` and subscription `datapulse-incidents-consumer` (metadata only). All of these must be independently verified in your GCP project; their existence is not assumed.

- **Default notebook mode** checks BigQuery metadata and compiles COUNT(*) dry runs, then optionally checks Pub/Sub topology. No results read, no data changes, no message acknowledgements.
- **Optional explicit opt-in** queries the replay table only for aggregate test rows and prediction flips with a maximum-bytes-billed setting; this can consume GCP credits and must be approved in the notebook. Never enable it in the anonymous public Streamlit app.
- To use the optional admin-gated Streamlit BigQuery audit, you must privately configure `GCP_SERVICE_ACCOUNT` and `GCP_PROJECT_ID` through Streamlit Secrets. For a publicly hosted portfolio site, **prefer Colab's user sign-in instead** of placing long-lived service account keys in a web app.

Google Cloud budget alerts are notifications, not hard limits. Dry-run scan estimates are advisory. A successful GCP metadata audit **does not prove end-to-end event ingestion, Pub/Sub delivery, model correctness, or production reliability**.

## Evidence and limitations

Only local tests and deterministic evaluations can run without cloud/provider authorization. Never claim hosted Qwen inference, BigQuery live validation, or working Pub/Sub delivery until a real authenticated run is recorded and separately inspected. The system is a safe educational prototype, not a production security boundary.
