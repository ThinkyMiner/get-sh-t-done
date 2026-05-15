from __future__ import annotations

import streamlit as st

from config import API_URL


def render_logs(logs: list[dict]) -> None:
    for log in logs:
        status = log.get("status", "unknown")
        status_icon = "SUCCESS" if status == "success" else "AI" if status == "ai_fallback" else "ERROR"
        title = (
            f"{status_icon} {log.get('step_id', 'step')}: "
            f"{log.get('step_type', '')} - {status} ({log.get('duration_ms', 0)}ms)"
        )
        with st.expander(title):
            st.write(log.get("message", ""))
            screenshot = log.get("screenshot_url") or log.get("screenshot_path")
            if screenshot:
                image_url = screenshot if str(screenshot).startswith("http") else f"{API_URL}{screenshot}"
                st.image(image_url, caption=f"After {log.get('step_id', '')}")
            if status == "ai_fallback":
                st.info("This step used AI self-healing to locate the element.")
