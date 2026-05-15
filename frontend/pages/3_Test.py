from __future__ import annotations

import sys
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = FRONTEND_DIR.parent
for _path in (FRONTEND_DIR, REPO_ROOT):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

import json

import requests
import streamlit as st

from components.log_viewer import render_logs
from config import API_URL, MOCK_LOGS
from local_store import load_execution_logs, run_local_test

st.title("Test Your API")

workflow = st.session_state.get("test_workflow") or st.session_state.get("draft_workflow")
if not workflow:
    st.warning("No workflow loaded.")
    st.stop()

st.markdown(f"**Workflow:** {workflow.get('workflow_name', 'Unnamed')}")
st.markdown(f"**Endpoint:** `POST /api/generated/{workflow.get('slug', '...')}/run`")
st.divider()

st.subheader("Input Parameters")
inputs: dict = {}
for field in workflow.get("inputs", []):
    label = f"{field['name']} {'*' if field.get('required', True) else '(optional)'}"
    if field["type"] == "number":
        inputs[field["name"]] = st.number_input(label, key=f"test_{field['name']}")
    elif field["type"] == "boolean":
        inputs[field["name"]] = st.checkbox(label, key=f"test_{field['name']}")
    else:
        inputs[field["name"]] = st.text_input(label, key=f"test_{field['name']}")

if st.button("Run Test", type="primary"):
    slug = workflow.get("slug", "")
    with st.status("Running automation...") as status:
        status.write("Launching browser...")
        try:
            response = requests.post(
                f"{API_URL}/api/generated/{slug}/run",
                json=inputs,
                timeout=60,
            )
            response.raise_for_status()
            result = response.json()
            status.update(label="Execution complete", state="complete")
        except Exception:
            result = run_local_test(workflow, inputs)
            status.update(label="Complete in local mode", state="complete")

    st.subheader("Results")
    col1, col2 = st.columns(2)
    col1.metric("Status", result.get("status", "unknown"))
    col2.metric("Duration", f"{result.get('duration_ms', 0)}ms")

    st.subheader("API Response")
    st.json(result.get("outputs", {}))

    st.subheader("Equivalent API Call")
    curl_cmd = (
        f"curl -X POST http://localhost:8000/api/generated/{slug}/run \\\n"
        '  -H "Content-Type: application/json" \\\n'
        f"  -d '{json.dumps(inputs)}'\n"
    )
    st.code(curl_cmd, language="bash")

    execution_id = result.get("execution_id", "")
    st.subheader("Step-by-Step Execution Log")
    try:
        logs_response = requests.get(f"{API_URL}/api/executions/{execution_id}/logs", timeout=15)
        logs_response.raise_for_status()
        logs = logs_response.json()
    except Exception:
        try:
            logs = load_execution_logs(execution_id)
        except Exception:
            logs = MOCK_LOGS

    render_logs(logs)
