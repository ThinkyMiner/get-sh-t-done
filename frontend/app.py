from __future__ import annotations

import sys
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent
REPO_ROOT = FRONTEND_DIR.parent
for _path in (FRONTEND_DIR, REPO_ROOT):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

import requests
import streamlit as st

from config import API_URL, DEMO_WORKFLOWS
from local_store import list_example_workflows, list_saved_workflows, load_workflow_reference

st.set_page_config(page_title="Flow2API", page_icon="->", layout="wide")

st.title("Flow2API")
st.markdown("**Turn screen recordings into APIs.** Show a process once. Use it as an API forever.")
st.divider()

st.subheader("Your APIs")

try:
    response = requests.get(f"{API_URL}/api/workflows", timeout=3)
    response.raise_for_status()
    workflows = response.json()
except Exception:
    local_workflows = list_saved_workflows()
    workflows = local_workflows or (list_example_workflows() + DEMO_WORKFLOWS)
    st.info("Backend not connected yet. Showing local and example workflows.")

if workflows:
    for workflow in workflows:
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
        col1.markdown(f"**{workflow['name']}**")
        col1.caption(workflow.get("description", ""))
        col2.code(f"POST /api/generated/{workflow['slug']}/run", language=None)
        if col3.button("Test", key=f"test_{workflow['id']}"):
            st.session_state["test_workflow_id"] = workflow["id"]
            st.session_state["test_workflow"] = load_workflow_reference(workflow["id"])
            st.switch_page("pages/3_Test.py")
        if col4.button("Docs", key=f"docs_{workflow['id']}"):
            st.session_state["docs_workflow_id"] = workflow["id"]
            st.session_state["draft_workflow"] = load_workflow_reference(workflow["id"])
            st.switch_page("pages/4_API_Docs.py")
else:
    st.info("No workflows yet. Upload a video to create your first API!")

st.divider()
col1, col2, col3 = st.columns(3)
col1.metric("Workflows", len(workflows))
col2.metric("Total Executions", "-")
col3.metric("Success Rate", "-")
