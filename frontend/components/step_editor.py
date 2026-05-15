from __future__ import annotations

import streamlit as st

from config import SELECTOR_TYPES, STEP_TYPES


def render_step_editor(workflow: dict) -> None:
    confidence_badges = {"high": "High", "medium": "Medium", "low": "Low"}
    steps_to_remove: list[int] = []

    for index, step in enumerate(workflow.get("steps", [])):
        confidence = step.get("confidence", "medium")
        badge = confidence_badges.get(confidence, "Unknown")

        with st.expander(
            f"Step {index + 1}: {step.get('type', '?')} - {step.get('description', '')} [{badge}]",
            expanded=(confidence == "low"),
        ):
            col1, col2 = st.columns(2)
            current_type = step.get("type", STEP_TYPES[0])
            if current_type not in STEP_TYPES:
                current_type = STEP_TYPES[0]
            step["type"] = col1.selectbox(
                "Action Type",
                STEP_TYPES,
                index=STEP_TYPES.index(current_type),
                key=f"step_type_{index}",
            )

            current_confidence = step.get("confidence", "medium")
            if current_confidence not in {"high", "medium", "low"}:
                current_confidence = "medium"
            step["confidence"] = col2.selectbox(
                "Confidence",
                ["high", "medium", "low"],
                index=["high", "medium", "low"].index(current_confidence),
                key=f"step_conf_{index}",
            )

            step["description"] = st.text_input(
                "Description",
                value=step.get("description", ""),
                key=f"step_desc_{index}",
            )

            if step["type"] == "navigate":
                step["url"] = st.text_input(
                    "URL",
                    value=step.get("url", ""),
                    key=f"step_url_{index}",
                )
            elif step["type"] == "wait":
                step["duration_ms"] = int(
                    st.number_input(
                        "Wait (ms)",
                        value=int(step.get("duration_ms", 1000)),
                        min_value=100,
                        max_value=30000,
                        step=100,
                        key=f"step_wait_{index}",
                    )
                )
            else:
                col1, col2 = st.columns(2)
                selector_type = step.get("selector_type", "text")
                if selector_type not in SELECTOR_TYPES:
                    selector_type = "text"
                step["selector_type"] = col1.selectbox(
                    "Selector Type",
                    SELECTOR_TYPES,
                    index=SELECTOR_TYPES.index(selector_type),
                    key=f"step_seltype_{index}",
                )
                step["selector_value"] = col2.text_input(
                    "Selector Value",
                    value=step.get("selector_value", ""),
                    key=f"step_selval_{index}",
                )

                if step["type"] == "fill":
                    step["value"] = st.text_input(
                        "Value (use {{var}} for inputs)",
                        value=step.get("value", ""),
                        key=f"step_val_{index}",
                    )

                if step["type"] == "select":
                    step["option_value"] = st.text_input(
                        "Option to Select",
                        value=step.get("option_value", ""),
                        key=f"step_opt_{index}",
                    )

                if step["type"] in {"extract_text", "extract_table"}:
                    step["output_key"] = st.text_input(
                        "Output Key",
                        value=step.get("output_key", ""),
                        key=f"step_outkey_{index}",
                    )

            col1, col2, col3 = st.columns([1, 1, 4])
            if col1.button("Move Up", key=f"step_up_{index}", disabled=(index == 0)):
                workflow["steps"][index], workflow["steps"][index - 1] = (
                    workflow["steps"][index - 1],
                    workflow["steps"][index],
                )
                st.rerun()

            if col2.button(
                "Move Down",
                key=f"step_down_{index}",
                disabled=(index == len(workflow["steps"]) - 1),
            ):
                workflow["steps"][index], workflow["steps"][index + 1] = (
                    workflow["steps"][index + 1],
                    workflow["steps"][index],
                )
                st.rerun()

            if col3.button("Remove Step", key=f"step_del_{index}"):
                steps_to_remove.append(index)

    for index in sorted(steps_to_remove, reverse=True):
        workflow["steps"].pop(index)
        st.rerun()
