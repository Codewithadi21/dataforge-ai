# DataForge AI — Deployment Guide

Repository: https://github.com/Codewithadi21/dataforge-ai

## Step 1. Streamlit Community Cloud (public read-only baseline)

- Select the `Codewithadi21/dataforge-ai` repository, `main` branch and `ui/cloud_app.py` entrypoint.
- No credentials required for the public baseline.
- The default project is an upstream-repository seeded synthetic snapshot, not a live Google Cloud dataset.
- The `Refresh DataPulse GitHub evidence` button makes a fixed read-only GitHub API call for the checked-in seeded results; if it fails, the pinned snapshot remains.
- Model inference and GCP resource checks are disabled for anonymous visitors.

## Step 2. Hosted Qwen (only with admin authorization)

In **Streamlit App settings → Secrets**, enter *private* (not checked-in) TOML values:

```toml
HF_TOKEN = "hf_your_private_hf_token"
ADMIN_DEMO_PASSWORD = "your_private_unique_admin_password"
```

Obtain a Hugging Face token with Inference Providers permission. In the sidebar, enter your admin password and choose `Use hosted Qwen on this request`. The app calls a fixed Hugging Face router endpoint for a Qwen model (`Qwen/Qwen3-4B-Instruct-2507:nscale`) and uses the deterministic source-grounded answer if the request fails or grounding checks reject the output. Provider calls may consume credits. Max 3 calls/browser session (not an account-level quota); keep the admin password private.

## Step 3. BigQuery validation (recommended Colab path)

Open [the DataForge GCP audit Colab notebook](../notebooks/02_DataForge_GCP_Audit_Colab.ipynb), authenticate using your Google login in Colab, enter your GCP project ID, then run the read-only metadata and dry-run checks. No service-account key needed for this workflow. The optional billable SELECT aggregate cell is off by default and requires explicit approval.

Advanced optional **admin-only Streamlit** metadata/dry-run validation can use `GCP_PROJECT_ID` and a `[GCP_SERVICE_ACCOUNT]` block in private Streamlit Secrets; avoid a long-lived service-account key on a public web app unless absolutely necessary. No service-account keys should ever be committed to GitHub.

## Do not overclaim

A public hosted UI is not proof of live Qwen inference or live BigQuery execution. Verify each external system in its own runtime, retain the citation and trace metadata, and label upstream DataPulse data as seeded synthetic. See [Phase 2–4 status and limitations](PHASE2_3_4.md).
