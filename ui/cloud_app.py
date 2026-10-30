"""Public Streamlit Community Cloud entrypoint; no local API server required."""
import streamlit as st
from dataforge.hosted import make_public_engine, ask_public

st.set_page_config(page_title="DataForge AI | Public Demo", page_icon="🧱", layout="wide")

@st.cache_resource
def engine():
    return make_public_engine()


def show_response(response):
    st.write(response.answer)
    if response.sql_draft:
        st.code(response.sql_draft, language="sql")
    if response.sql_check:
        st.json(response.sql_check)
    if response.supporting_sources:
        with st.expander(f"Evidence sources ({len(response.supporting_sources)})", expanded=True):
            for source in response.supporting_sources:
                st.caption(f"{source.source_id} · {source.path}"
                           + (" · Synthetic demo" if source.synthetic else ""))
    if response.uncertainty_notes:
        with st.expander("Evidence limitations"):
            for note in response.uncertainty_notes:
                st.write("- " + note)
    if response.recommended_checks:
        with st.expander("Suggested human checks"):
            for check in response.recommended_checks:
                st.write("- " + check)
    if response.requires_human_approval:
        st.warning("Human approval required for any operational changes. No changes are made by this demo.")
    st.caption(f"Mode: {response.intent} · Retrieval: {response.retrieval_mode} · "
               f"Backend: {response.model_backend} · Trace: {response.execution_trace_id}")


st.title("DataForge AI")
st.caption("Evidence-grounded Data Engineering Copilot · Public, read-only demonstration")
st.info("This online preview uses synthetic DataPulse evidence and deterministic retrieval. "
        "It is NOT connected to production systems and is NOT running Qwen inference.")
st.sidebar.markdown("### Explore")
mode = st.sidebar.radio("Tool", ["Ask DataForge", "Incident investigator", "Lineage explorer", "SQL planner", "Project guide"])
st.sidebar.caption("No credentials, company data, or live BigQuery execution. Do not paste sensitive data.")

if mode == "Ask DataForge":
    st.subheader("Ask about the example project")
    q = st.text_input("Question", placeholder="Why did the churn model behave differently?", max_chars=1500)
    if st.button("Ask", type="primary") and q.strip():
        show_response(ask_public(engine(), q.strip()))
elif mode == "Incident investigator":
    st.subheader("Investigate a sample drift incident")
    if st.button("Investigate DP-SYN-001", type="primary"):
        show_response(ask_public(engine(), "Explain incident DP-SYN-001 and its drift metrics"))
elif mode == "Lineage explorer":
    st.subheader("Trace declared source-to-model dependencies")
    entity = st.selectbox("Entity", ["engagement_score", "paired_prediction_replay"])
    if st.button("Trace lineage", type="primary"):
        show_response(ask_public(engine(), f"Trace lineage for {entity}"))
elif mode == "SQL planner":
    st.subheader("Read-only BigQuery SQL planner")
    st.caption("Generates a restricted SELECT draft; no queries are sent to Google Cloud.")
    template = st.selectbox("Example", ["Show customers whose predictions flipped", "Count rows in baseline_customers", "Preview shifted_customers"])
    raw = st.text_area("Or paste a SELECT for validation (optional)", max_chars=4000)
    if st.button("Generate or validate", type="primary"):
        show_response(ask_public(engine(), template, raw.strip() or None))
else:
    st.subheader("Project documentation")
    q = st.selectbox("Guide", ["How does DataPulse work?", "What is semantic drift?", "How does DataForge work?", "How are citations attached?"])
    if st.button("Retrieve documentation", type="primary"):
        show_response(ask_public(engine(), q))

st.divider()
st.caption("DataForge AI MVP · synthetic evidence · no model training claimed · no autonomous actions")
