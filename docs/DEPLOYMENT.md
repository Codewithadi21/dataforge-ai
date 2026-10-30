# GitHub + hosted DataForge demo

## 1. Create a separate GitHub repository

Create an **empty** public GitHub repository named `dataforge-ai` in the `Codewithadi21` account. Do not add a generated README or license to the empty repository, as the project includes its own. Upload the contents of the `dataforge-ai/` directory **to repository root** (not the ZIP itself). Use the connected GitHub app to commit all files when the new repository becomes accessible, or upload through GitHub's **Add file → Upload files** if necessary.

**Do not modify an existing DataPulse repository.** DataForge and DataPulse remain separate and communicate through a versioned read-only adapter when real exports are approved and validated.

## 2. Deploy an interactive public demo (no laptop or local API required)

1. Sign into https://share.streamlit.io with the GitHub account.
2. Choose **Create app → Yup, I have an app**.
3. Repository: `Codewithadi21/dataforge-ai`; branch: `main`.
4. Main file path: `ui/cloud_app.py`.
5. In advanced settings select Python 3.11 if offered (tests use 3.11). There are **no secrets** to enter.
6. Choose a free/available app subdomain and press **Deploy**.
7. Test **Incident investigator**, **Lineage explorer**, and **SQL planner** on the resulting `*.streamlit.app` URL.

The repository-root `requirements.txt` installs `. [ui]` as an editable local package (`-e .[ui]`); the hosted entrypoint imports the project directly. It does not require the FastAPI server.

## 3. What the public link actually runs

The public app intentionally uses **only synthetic fixtures, TF-IDF retrieval and deterministic incident/SQL logic**. It does not load Qwen weights, execute BigQuery jobs, read private exports, accept credentials, or make production changes. This is a useful public working demo but **not a remotely hosted LLM inference endpoint**.

## 4. Separate Qwen-powered hosted inference (future integration)

To give the public app actual LLM responses, provision a remote inference service (e.g. Hugging Face inference/Spaces, a managed inference API, or a hosted VM), then:

- Choose the model and verify its license, compute requirements, serving cost, and latency.
- Never expose endpoint credentials to website visitors or GitHub.
- Add server-side authentication, rate limits and content/size restrictions before exposing the API publicly.
- Design a server-side only model adapter and update the public UI to use it, preserving deterministic evidence and source citations.
- Measure on the existing frozen evaluation set; document failures and timeouts.

A free Colab runtime is temporary and cannot be relied upon as a stable public endpoint. Streamlit Cloud does not automatically supply the resources to run the proposed Qwen 1.5B model. Do not label the public demo "Qwen-powered" until inference is connected and tested.

## 5. Cross-project connection plan

At first, DataForge uses synthetic DataPulse-style incident/schema/lineage fixtures. To connect actual DataPulse, export approved/versioned JSON via an integration contract and connect it in a protected backend; verify source identifiers, timestamps, and allow-list permissions. Do not share production cloud credentials or private datasets in a public demo.

## 6. Test deployment prep

```bash
python -m pip install -e '.[dev,ui]'
python -m pytest -q
python -m dataforge.cli eval --output eval/latest_results.json
python -m streamlit run ui/cloud_app.py
```

This tests the application locally for development, but the hosted app runs independently of the local machine after deployment.
