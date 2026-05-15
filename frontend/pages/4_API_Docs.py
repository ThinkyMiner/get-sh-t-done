from __future__ import annotations

import sys
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = FRONTEND_DIR.parent
for _path in (FRONTEND_DIR, REPO_ROOT):
    _path_str = str(_path)
    if _path_str not in sys.path:
        sys.path.insert(0, _path_str)

import requests
import streamlit as st

from components.api_display import render_api_docs
from config import API_URL
from local_store import generate_local_docs

st.title("API Documentation")

workflow_id = st.session_state.get("active_workflow_id") or st.session_state.get("docs_workflow_id")
workflow = st.session_state.get("draft_workflow") or st.session_state.get("test_workflow")
if not workflow:
    st.warning("No workflow loaded.")
    st.stop()

slug = workflow.get("slug", "unknown")

try:
    response = requests.get(f"{API_URL}/api/workflows/{workflow_id}/docs", timeout=15)
    response.raise_for_status()
    docs = response.json()
except Exception:
    docs = generate_local_docs(workflow)

render_api_docs(slug, workflow, docs)

st.subheader("Workflow Steps")
for index, step in enumerate(workflow.get("steps", [])):
    confidence = step.get("confidence", "medium")
    badge = {"high": "high", "medium": "medium", "low": "low"}.get(confidence, "unknown")
    st.markdown(f"**Step {index + 1}:** {step.get('type', '?')} - {step.get('description', '')} ({badge})")
