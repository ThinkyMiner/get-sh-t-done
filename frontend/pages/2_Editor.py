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

from components.step_editor import render_step_editor
from config import API_URL, FIELD_TYPES
from local_store import save_workflow

st.title("Review & Edit Workflow")

if "draft_workflow" not in st.session_state:
    st.warning("No workflow loaded. Go to Upload page first.")
    st.stop()

workflow = st.session_state["draft_workflow"]

validation_errors = workflow.get("_validation_errors") or []
if validation_errors:
    st.warning("Validation notes: " + " | ".join(validation_errors))

st.subheader("Workflow Info")
col1, col2 = st.columns(2)
workflow["workflow_name"] = col1.text_input("Name", value=workflow.get("workflow_name", ""))
workflow["slug"] = col2.text_input("API Slug", value=workflow.get("slug", ""))
workflow["description"] = st.text_input("Description", value=workflow.get("description", ""))

st.subheader("Input Parameters")
st.caption("These become the request body fields of your generated API.")
inputs_to_remove: list[int] = []
for index, item in enumerate(workflow.get("inputs", [])):
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    item["name"] = col1.text_input("Name", value=item["name"], key=f"inp_name_{index}")
    current_type = item.get("type", "string")
    if current_type not in FIELD_TYPES:
        current_type = "string"
    item["type"] = col2.selectbox(
        "Type",
        FIELD_TYPES,
        index=FIELD_TYPES.index(current_type),
        key=f"inp_type_{index}",
    )
    item["required"] = col3.checkbox(
        "Required",
        value=item.get("required", True),
        key=f"inp_req_{index}",
    )
    if col4.button("Delete", key=f"inp_del_{index}"):
        inputs_to_remove.append(index)

for index in sorted(inputs_to_remove, reverse=True):
    workflow["inputs"].pop(index)

if st.button("Add Input"):
    workflow["inputs"].append({"name": "new_input", "type": "string", "required": True})
    st.rerun()

st.subheader("Workflow Steps")
render_step_editor(workflow)

if st.button("Add Step"):
    workflow["steps"].append(
        {
            "id": f"step_{len(workflow['steps']) + 1}",
            "type": "click",
            "selector_type": "text",
            "selector_value": "",
            "description": "",
            "confidence": "low",
        }
    )
    st.rerun()

st.subheader("Output Fields")
for index, output in enumerate(workflow.get("outputs", [])):
    col1, col2 = st.columns([3, 2])
    output["name"] = col1.text_input("Output Name", value=output["name"], key=f"out_name_{index}")
    current_type = output.get("type", "string")
    if current_type not in FIELD_TYPES:
        current_type = "string"
    output["type"] = col2.selectbox(
        "Type",
        FIELD_TYPES,
        index=FIELD_TYPES.index(current_type),
        key=f"out_type_{index}",
    )

st.divider()
with st.expander("Raw Workflow JSON"):
    st.json(workflow)

col1, col2 = st.columns(2)
if col1.button("Save & Deploy", type="primary"):
    try:
        response = requests.post(f"{API_URL}/api/workflows", json=workflow, timeout=15)
        response.raise_for_status()
        result = response.json()
        st.session_state["active_workflow_id"] = result.get("workflow_id") or result.get("id")
        st.session_state["active_workflow_slug"] = result["slug"]
        st.success(f"Deployed. Endpoint: POST /api/generated/{result['slug']}/run")
    except Exception:
        result = save_workflow(workflow)
        st.session_state["active_workflow_id"] = result["workflow_id"]
        st.session_state["active_workflow_slug"] = result["slug"]
        st.success(f"Saved locally. Endpoint: POST /api/generated/{result['slug']}/run")

if col2.button("Save & Test"):
    try:
        response = requests.post(f"{API_URL}/api/workflows", json=workflow, timeout=15)
        response.raise_for_status()
        result = response.json()
        st.session_state["active_workflow_id"] = result.get("workflow_id") or result.get("id")
    except Exception:
        result = save_workflow(workflow)
        st.session_state["active_workflow_id"] = result["workflow_id"]

    st.session_state["test_workflow"] = workflow
    st.switch_page("pages/3_Test.py")
