"""Local Streamlit interface for the FastAPI copilot."""
import json
import os
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import streamlit as st

st.set_page_config(page_title="DataForge AI", page_icon="🧱", layout="wide")
API = os.getenv("DATAFORGE_API_URL", "http://127.0.0.1:8000").rstrip("/")


def send(question: str, sql: str | None = None, cloud: bool = False) -> dict:
    payload = json.dumps({"question": question, "project_id": "datapulse-demo", "sql": sql,
                          "cloud_dry_run": cloud}).encode("utf-8")
    req = Request(f"{API}/ask", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(req, timeout=120) as response:
            return json.load(response)
    except (URLError, HTTPError, TimeoutError, ValueError) as exc:
        return {"error": f"Cannot reach local FastAPI backend ({type(exc).__name__}). Start uvicorn first."}


def render(result: dict) -> None:
    if "error" in result:
        st.error(result["error"])
        return
    st.markdown(result["answer"])
    if result.get("sql_draft"):
        st.code(result["sql_draft"], language="sql")
    if result.get("sql_check"):
        st.json(result["sql_check"])
    sources = result.get("supporting_sources", [])
    if sources:
        with st.expander(f"Evidence & sources ({len(sources)})", expanded=True):
            for source in sources:
                st.caption(f"{source['source_id']} — {source['path']}" +
                           (" [SYNTHETIC]" if source.get("synthetic") else ""))
    for label, key in (("Uncertainty and limitations", "uncertainty_notes"),
                       ("Recommended human checks", "recommended_checks")):
        if result.get(key):
            with st.expander(label):
                for entry in result[key]:
                    st.write(f"• {entry}")
    if result.get("requires_human_approval"):
        st.warning("Human review required before any operational changes. This app cannot remediate incidents.")
    st.caption(f"Intent: {result.get('intent')} | Retrieval: {result.get('retrieval_mode')} | "
               f"Model: {result.get('model_backend')} | Trace: {result.get('execution_trace_id')}")

st.title("DataForge AI")
st.caption("Evidence-grounded Data Engineering Copilot · read-only · local-first")
st.info("Demo uses illustrative synthetic DataPulse records, not live company data or a verified BigQuery deployment.")
mode = st.sidebar.radio("Explore", ["Ask DataForge", "Investigate incident", "Trace lineage", "BigQuery SQL planner", "Project guide"])
st.sidebar.caption("DataPulse is the first *adapter*, not the entire application.")

if mode == "Ask DataForge":
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant": render(msg["result"])
            else: st.write(msg["text"])
    question = st.chat_input("Ask about pipelines, drift, SQL, runbooks, or lineage")
    if question:
        st.session_state.messages.append({"role": "user", "text": question})
        with st.chat_message("user"): st.write(question)
        result = send(question)
        st.session_state.messages.append({"role": "assistant", "result": result})
        with st.chat_message("assistant"): render(result)
elif mode == "Investigate incident":
    st.subheader("Evidence-grounded incident RCA")
    if st.button("Inspect illustrative DP-SYN-001", type="primary"):
        render(send("Explain incident DP-SYN-001 and its drift metrics"))
elif mode == "Trace lineage":
    st.subheader("Declared lineage explorer")
    selection = st.selectbox("Entity", ["engagement_score", "paired_prediction_replay"])
    if st.button("Trace lineage", type="primary"):
        render(send(f"Trace lineage of {selection}"))
elif mode == "BigQuery SQL planner":
    st.subheader("Restricted SELECT planner")
    st.write("Choose a suggested query, or paste a SELECT within the limited approved grammar.")
    request = st.selectbox("Suggested question", ["Show customers whose predictions flipped", "Count rows in baseline_customers", "Preview shifted_customers"])
    raw = st.text_area("Optional custom SQL to validate (never executed)", height=120)
    cloud = st.checkbox("Request optional BigQuery dry run", value=False,
                        help="Requires explicit backend enablement, ADC credentials and the cloud extra.")
    if st.button("Validate / generate draft", type="primary"):
        render(send(request, sql=raw.strip() or None, cloud=cloud))
else:
    st.subheader("Project architecture and onboarding")
    request = st.selectbox("Guide topics", ["How does DataPulse work?", "What is semantic drift?", "How do I start DataForge locally?", "How are source citations attached?"])
    if st.button("Read verified documentation", type="primary"):
        render(send(request))
