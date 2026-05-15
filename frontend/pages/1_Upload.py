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

from config import API_URL, clone_mock_workflow
from local_store import analyze_saved_video, analyze_uploaded_video, save_uploaded_video

st.title("Create New API from Video")

st.subheader("1. Upload Screen Recording")
video_file = st.file_uploader(
    "Upload a screen recording showing the task you want to automate",
    type=["mp4", "webm", "mov", "avi"],
)
if video_file:
    st.video(video_file)

st.subheader("2. Add Context (Optional)")
website_url = st.text_input("Website URL", placeholder="https://internal-tool.company.com")
description = st.text_area(
    "Describe what this process does",
    placeholder="Example: Search for a supplier by ID and check their verification status",
)

st.subheader("3. Analyze")
if st.button("Analyze Video", disabled=not video_file, type="primary"):
    with st.status("Analyzing your video...") as status:
        status.write("Uploading video...")
        video_path = st.session_state.get("video_path")
        try:
            files = {"file": (video_file.name, video_file.getvalue(), video_file.type)}
            upload_resp = requests.post(f"{API_URL}/api/videos/upload", files=files, timeout=15)
            upload_resp.raise_for_status()
            video_id = upload_resp.json()["video_id"]
            status.write(f"Uploaded with ID: {video_id}")
        except Exception:
            video_id, video_path = save_uploaded_video(video_file)
            st.session_state["video_path"] = video_path
            status.write(f"Backend unavailable, saved video locally as {video_id}.")

        status.write("Extracting keyframes...")
        status.write("Running workflow analysis...")

        try:
            analyze_resp = requests.post(
                f"{API_URL}/api/videos/{video_id}/analyze",
                json={"user_context": description, "website_url": website_url},
                timeout=60,
            )
            analyze_resp.raise_for_status()
            workflow = analyze_resp.json()["workflow_json"]
        except Exception:
            try:
                local_context = description
                if website_url:
                    local_context = f"{description}\nWebsite URL: {website_url}".strip()
                if video_path:
                    workflow = analyze_saved_video(video_id=video_id, video_path=video_path, user_context=local_context)
                else:
                    video_id, workflow = analyze_uploaded_video(video_file, user_context=local_context)
                status.write("Local analyzer completed successfully.")
            except Exception:
                workflow = clone_mock_workflow()
                workflow["description"] = description or workflow["description"]
                if website_url:
                    workflow["steps"][0]["url"] = website_url
                status.write("Local analyzer unavailable, using static mock workflow.")

        st.session_state["draft_workflow"] = workflow
        st.session_state["video_id"] = video_id
        status.update(label="Analysis complete", state="complete")

    st.success("Workflow extracted. Review and edit it below.")
    if st.button("Review and Edit Workflow"):
        st.switch_page("pages/2_Editor.py")
