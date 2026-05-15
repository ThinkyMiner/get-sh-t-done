from __future__ import annotations

import re

VALID_STEP_TYPES = {
    "navigate",
    "fill",
    "click",
    "select",
    "wait",
    "extract_text",
    "extract_table",
    "download_file",
}
VALID_SELECTOR_TYPES = {"label", "role", "text", "test_id", "css", "placeholder"}
VALID_PRIMITIVE_TYPES = {"string", "number", "boolean"}


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned or "unnamed-workflow"


def validate_and_fix(workflow: dict) -> dict:
    """
    Validate LLM output against the workflow schema and repair common issues.
    """
    errors: list[str] = []

    workflow["workflow_name"] = workflow.get("workflow_name") or "unnamed_workflow"
    workflow["slug"] = workflow.get("slug") or _slugify(workflow["workflow_name"])
    workflow["description"] = workflow.get("description") or ""
    workflow["inputs"] = list(workflow.get("inputs") or [])
    workflow["steps"] = list(workflow.get("steps") or [])
    workflow["outputs"] = list(workflow.get("outputs") or [])

    if not workflow["steps"]:
        errors.append("CRITICAL: No steps found in workflow")

    for index, item in enumerate(workflow["inputs"]):
        item["name"] = item.get("name") or f"input_{index + 1}"
        item["type"] = item.get("type") if item.get("type") in VALID_PRIMITIVE_TYPES else "string"
        item["required"] = bool(item.get("required", True))

    for index, step in enumerate(workflow["steps"]):
        step["id"] = step.get("id") or f"step_{index + 1}"
        step["type"] = step.get("type") or "click"
        step["description"] = step.get("description") or f"{step['type']} action"
        step["confidence"] = step.get("confidence") or "medium"

        if step["type"] not in VALID_STEP_TYPES:
            errors.append(f"Step {step['id']}: invalid type '{step['type']}'")

        if "selector_type" in step and step["selector_type"] not in VALID_SELECTOR_TYPES:
            errors.append(
                f"Step {step['id']}: invalid selector_type '{step['selector_type']}'"
            )
            step["selector_type"] = "text"

        if step["type"] == "wait":
            step["duration_ms"] = int(step.get("duration_ms") or 1500)

    declared_outputs = {output.get("name") for output in workflow["outputs"] if output.get("name")}
    for step in workflow["steps"]:
        if step.get("type") in {"extract_text", "extract_table"} and step.get("output_key"):
            if step["output_key"] not in declared_outputs:
                workflow["outputs"].append({"name": step["output_key"], "type": "string"})
                declared_outputs.add(step["output_key"])

    for index, output in enumerate(workflow["outputs"]):
        output["name"] = output.get("name") or f"output_{index + 1}"
        output["type"] = output.get("type") if output.get("type") in VALID_PRIMITIVE_TYPES else "string"

    workflow["_validation_errors"] = errors
    return workflow
