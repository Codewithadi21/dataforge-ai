"""Public Streamlit app: evidence tools for all; admin-gated external services."""
import hmac
import streamlit as st

from dataforge.hosted import make_public_engine, ask_public
from dataforge.models.hosted_qwen import grounded_hosted_summary, DEFAULT_MODEL
from dataforge.connectors.repo_refresh import refresh_public_repo_snapshot
from dataforge.cloud_validation import (audit_bigquery_dry_runs,
                                         authorized_service_account_client)

st.set_page_config(page_title="DataForge AI | Data Engineering Copilot", page_icon="🧱", layout="wide")

@st.cache_resource
def engine():
    return make_public_engine()


def private_setting(name, default=None):
    # Streamlit's secrets object may raise when no secrets.toml exists.
    try:
        return st.secrets.get(name, default)
    except (KeyError, FileNotFoundError):
        return default


def show_response(response):
    st.write(response.answer)
    if response.sql_draft:
        st.code(response.sql_draft, language="sql")
    if response.sql_check:
        st.json(response.sql_check)
    if response.supporting_sources:
        with st.expander(f"Evidence sources ({len(response.supporting_sources)})", expanded=True):
            for source in response.supporting_sources:
                if source.path.startswith("https://github.com/"):
                    st.markdown(f"[{source.source_id}]({source.path}) · Seeded synthetic upstream evidence")
                else:
                    st.caption(f"{source.source_id} · {source.path}"
                               + (" · Synthetic example" if source.synthetic else ""))
    if response.uncertainty_notes:
        with st.expander("Evidence limitations", expanded=True):
            for note in response.uncertainty_notes:
                st.write("- " + note)
    if response.recommended_checks:
        with st.expander("Suggested human checks"):
            for check in response.recommended_checks:
                st.write("- " + check)
    if response.requires_human_approval:
        st.warning("Human approval required for operational changes. No changes are made by this app.")
    st.caption(f"Mode: {response.intent} · Retrieval: {response.retrieval_mode} · "
               f"Backend: {response.model_backend} · Trace: {response.execution_trace_id}")


st.title("DataForge AI")
st.caption("Evidence-grounded Data Engineering Copilot · Read-only public demo")

st.sidebar.caption("Release: diagnostics-2026-10-31b · GitHub main")
st.sidebar.markdown("### Data source")
selected = st.sidebar.selectbox("Project", [
    "DataPulse repository snapshot (seeded synthetic)",
    "Illustrative DataPulse demo (82/1,000)",
])
project_id = ("datapulse-repo-snapshot" if selected.startswith("DataPulse repository") else "datapulse-demo")
st.sidebar.caption("The repository snapshot comes from DataPulse's checked-in seeded results. Neither mode is live production data.")
if project_id == "datapulse-repo-snapshot":
    if st.sidebar.button("Refresh DataPulse GitHub evidence", help="Reads only the published seeded metrics JSON; no upstream changes"):
        st.session_state["upstream_refresh"] = refresh_public_repo_snapshot(engine())
    if "upstream_refresh" in st.session_state:
        status = st.session_state["upstream_refresh"]
        st.sidebar.caption("Upstream refresh: " + status["status"])
        if status["status"] == "fetched_and_validated":
            st.sidebar.caption("GitHub source blob: " + str(status.get("source_blob_sha", "unknown"))[:12])

st.sidebar.markdown("### Explore")
mode = st.sidebar.radio("Tool", ["Ask DataForge", "Incident investigator", "Lineage explorer",
                                 "SQL planner", "Project guide", "Cloud validation"])
st.sidebar.caption("Do not paste sensitive data, passwords, tokens or company records.")

# Server-side administrative feature gate; public visitors cannot spend provider credits.
admin_password = private_setting("ADMIN_DEMO_PASSWORD")
entered = st.sidebar.text_input("Admin demo password (optional)", type="password",
                                help="Only needed for privately testing hosted Qwen or GCP audit.")
admin_ok = bool(admin_password and entered and hmac.compare_digest(str(admin_password), entered))
hf_token = private_setting("HF_TOKEN")
qwen_ready = bool(admin_ok and hf_token)
with st.sidebar.expander("Advanced service status"):
    st.write("Hosted Qwen:", "Ready for a live test" if qwen_ready else "Not enabled")
    st.write("BigQuery in this web app:", "Admin audit available" if admin_ok and private_setting("GCP_SERVICE_ACCOUNT") else "Not connected — Colab audit is separate")

use_model = False
if admin_ok and hf_token and mode in {"Ask DataForge", "Incident investigator", "Lineage explorer", "Project guide"}:
    use_model = st.sidebar.checkbox("Use hosted Qwen on this request", value=False)
    st.sidebar.caption("Hugging Face Inference Providers may consume credits. Maximum three model calls per browser session.")
    st.sidebar.caption("If a response stays deterministic, expand Evidence limitations for a safe failure category (HTTP status, timeout, or grounding rejection).")

if project_id == "datapulse-repo-snapshot":
    st.info("Connected to a **pinned export from the actual DataPulse GitHub repository**. The metrics are seeded synthetic examples, not live GCP results. Read-only; no modifications to DataPulse.")
else:
    st.info("Illustrative, self-contained synthetic fixture. Not the actual DataPulse replay metrics.")
if not qwen_ready:
    st.caption("LLM backend: deterministic evidence only. Hosted Qwen requires a private Streamlit token and admin authorization.")


def respond(question, sql=None):
    answer = ask_public(engine(), question, sql, project_id=project_id)
    if use_model and answer.intent != "sql":
        if st.session_state.get("hosted_llm_uses", 0) >= 3:
            st.warning("Hosted model trial limit reached for this browser session; using deterministic answer.")
        else:
            st.session_state["hosted_llm_uses"] = st.session_state.get("hosted_llm_uses", 0) + 1
            with st.spinner("Requesting Qwen inference..."):
                answer = grounded_hosted_summary(answer, question, token=str(hf_token), model=DEFAULT_MODEL)
    show_response(answer)


if mode == "Ask DataForge":
    st.subheader("Ask an evidence-grounded question")
    q = st.text_input("Question", placeholder="Why did the churn model behave differently?", max_chars=1500)
    if st.button("Ask", type="primary") and q.strip():
        respond(q.strip())
elif mode == "Incident investigator":
    st.subheader("Inspect a documented seeded incident")
    incident_id = "DP-REPO-SYN-001" if project_id == "datapulse-repo-snapshot" else "DP-SYN-001"
    if st.button(f"Investigate {incident_id}", type="primary"):
        respond(f"Explain incident {incident_id} and its drift metrics")
elif mode == "Lineage explorer":
    st.subheader("Trace declared source-to-model dependencies")
    options = (["engagement_events_30d", "decision.retention_contact"]
               if project_id == "datapulse-repo-snapshot" else ["engagement_score", "paired_prediction_replay"])
    entity = st.selectbox("Entity", options)
    if st.button("Trace lineage", type="primary"):
        respond(f"Trace lineage for {entity}")
elif mode == "SQL planner":
    st.subheader("Schema-aware, read-only SQL drafts")
    st.caption("Uses approved table schemas. This tool NEVER sends the drafted SQL to BigQuery.")
    template = st.selectbox("Example", ["Show customers whose predictions flipped",
                                         "Count rows in baseline_customers", "Preview shifted_customers"])
    raw = st.text_area("Or paste a restricted SELECT for policy validation (optional)", max_chars=4000)
    if st.button("Generate or validate", type="primary"):
        respond(template, raw.strip() or None)
elif mode == "Project guide":
    st.subheader("Grounded documentation retrieval")
    q = st.selectbox("Guide", ["How does DataPulse work?", "What is semantic drift?",
                               "How does DataForge work?", "How are citations attached?"])
    if st.button("Retrieve documentation", type="primary"):
        respond(q)
else:
    st.subheader("Cloud validation: BigQuery metadata + dry runs")
    st.caption("Admin-only. This does not execute query results, alter Google Cloud resources, or verify Pub/Sub delivery.")
    if not admin_ok:
        st.warning("Private admin authorization is required. Configure ADMIN_DEMO_PASSWORD in Streamlit secrets.")
    elif not private_setting("GCP_SERVICE_ACCOUNT") or not private_setting("GCP_PROJECT_ID"):
        st.info("This Streamlit server has no private GCP credentials. A successful Colab audit verifies Google Cloud separately; it does not authenticate this server. Use the Colab audit notebook for cloud checks. No new GCP project is required.")
    else:
        st.write("This will make read-only metadata calls and dry-run compilation requests. No query results are fetched.")
        if st.button("Run BigQuery read-only checks", type="primary"):
            try:
                project = str(private_setting("GCP_PROJECT_ID"))
                credentials = private_setting("GCP_SERVICE_ACCOUNT")
                client = authorized_service_account_client(dict(credentials), project)
                audit = audit_bigquery_dry_runs(client, project)
                st.json(audit)
                if audit["all_passed"]:
                    st.success("BigQuery table metadata and dry-run compilation verified. Data contents and streaming still unverified.")
            except Exception as exc:
                st.error(f"Cloud validation unavailable ({type(exc).__name__}). Check private credentials and IAM roles.")

st.divider()
st.caption("DataForge AI · seeded synthetic evidence · Qwen optional behind admin gate · no autonomous actions")
