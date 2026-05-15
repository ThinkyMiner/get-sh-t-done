from __future__ import annotations

import asyncio
import copy
import json
import re
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from analyzer.llm_analyzer import analyze_video  # noqa: E402
from analyzer.schema_validator import validate_and_fix  # noqa: E402


STORAGE_DIR = REPO_ROOT / "storage"
VIDEOS_DIR = STORAGE_DIR / "videos"
WORKFLOWS_DIR = STORAGE_DIR / "workflows"
EXECUTIONS_DIR = STORAGE_DIR / "executions"
EXAMPLES_DIR = REPO_ROOT / "examples"


def _ensure_dirs() -> None:
    for directory in (VIDEOS_DIR, WORKFLOWS_DIR, EXECUTIONS_DIR):
        directory.mkdir(parents=True, exist_ok=True)


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _humanize_name(workflow_name: str) -> str:
    return workflow_name.replace("_", " ").strip().title() or "Unnamed Workflow"


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return cleaned or "unnamed-workflow"


def save_uploaded_video(uploaded_file) -> tuple[str, str]:
    _ensure_dirs()
    video_id = f"vid_{uuid.uuid4().hex[:8]}"
    suffix = Path(uploaded_file.name).suffix or ".mp4"
    video_path = VIDEOS_DIR / f"{video_id}{suffix}"
    video_path.write_bytes(uploaded_file.getvalue())
    return video_id, str(video_path)


def analyze_uploaded_video(uploaded_file, user_context: str = "") -> tuple[str, dict]:
    video_id, video_path = save_uploaded_video(uploaded_file)
    workflow = analyze_saved_video(video_id=video_id, video_path=video_path, user_context=user_context)
    return video_id, workflow


def analyze_saved_video(video_id: str, video_path: str, user_context: str = "") -> dict:
    workflow = asyncio.run(analyze_video(video_id=video_id, video_path=video_path, user_context=user_context))
    return workflow


def save_workflow(workflow: dict) -> dict:
    _ensure_dirs()
    data = validate_and_fix(copy.deepcopy(workflow))
    workflow_id = data.get("_workflow_id") or f"wf_{uuid.uuid4().hex[:8]}"
    data["_workflow_id"] = workflow_id
    data["_saved_at"] = _utc_now()

    output_path = WORKFLOWS_DIR / f"{workflow_id}.json"
    output_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return {
        "workflow_id": workflow_id,
        "slug": data["slug"],
        "name": _humanize_name(data["workflow_name"]),
    }


def load_workflow(workflow_id: str) -> dict:
    workflow_path = WORKFLOWS_DIR / f"{workflow_id}.json"
    if not workflow_path.exists():
        raise FileNotFoundError(f"Workflow not found: {workflow_id}")
    return json.loads(workflow_path.read_text(encoding="utf-8"))


def list_saved_workflows() -> list[dict]:
    _ensure_dirs()
    items: list[dict] = []
    for workflow_path in sorted(WORKFLOWS_DIR.glob("*.json"), reverse=True):
        workflow = json.loads(workflow_path.read_text(encoding="utf-8"))
        items.append(
            {
                "id": workflow["_workflow_id"],
                "name": _humanize_name(workflow.get("workflow_name", "")),
                "slug": workflow.get("slug", "unknown"),
                "description": workflow.get("description", ""),
                "created_at": workflow.get("_saved_at", ""),
                "source": "local",
            }
        )
    return items


def list_example_workflows() -> list[dict]:
    items: list[dict] = []
    for example_path in sorted(EXAMPLES_DIR.glob("*.json")):
        workflow = json.loads(example_path.read_text(encoding="utf-8"))
        example_id = f"example:{example_path.stem}"
        items.append(
            {
                "id": example_id,
                "name": _humanize_name(workflow.get("workflow_name", "")),
                "slug": workflow.get("slug", _slugify(workflow.get("workflow_name", ""))),
                "description": workflow.get("description", ""),
                "created_at": "example",
                "source": "example",
            }
        )
    return items


def load_workflow_reference(workflow_id: str) -> dict:
    if workflow_id.startswith("example:"):
        example_name = workflow_id.split(":", 1)[1]
        example_path = EXAMPLES_DIR / f"{example_name}.json"
        if not example_path.exists():
            raise FileNotFoundError(f"Example workflow not found: {workflow_id}")
        return json.loads(example_path.read_text(encoding="utf-8"))
    return load_workflow(workflow_id)


def generate_local_docs(workflow: dict) -> dict:
    slug = workflow.get("slug", "unknown")
    return {
        "endpoint": f"POST /api/generated/{slug}/run",
        "description": workflow.get("description", ""),
        "request_body": {item["name"]: f"<{item['type']}>" for item in workflow.get("inputs", [])},
        "response_body": {item["name"]: f"<{item['type']}>" for item in workflow.get("outputs", [])},
    }


def run_local_test(workflow: dict, inputs: dict) -> dict:
    _ensure_dirs()
    execution_id = f"exec_{uuid.uuid4().hex[:8]}"
    logs: list[dict] = []
    outputs: dict[str, object] = {}

    for index, step in enumerate(workflow.get("steps", []), start=1):
        step_type = step.get("type", "unknown")
        message = step.get("description", f"Executed {step_type}")
        if step_type == "navigate":
            message = f"Navigated to {step.get('url', '(missing url)')}"
        elif step_type == "fill":
            value = step.get("value", "")
            for key, input_value in inputs.items():
                value = value.replace(f"{{{{{key}}}}}", str(input_value))
            message = f"Filled {step.get('selector_value', 'field')} with {value}"
        elif step_type == "click":
            message = f"Clicked {step.get('selector_value', 'target')}"
        elif step_type == "select":
            message = f"Selected {step.get('option_value', '')} in {step.get('selector_value', 'field')}"
        elif step_type == "wait":
            message = f"Waited {step.get('duration_ms', 1500)}ms"
        elif step_type in {"extract_text", "extract_table"}:
            output_key = step.get("output_key", f"output_{index}")
            outputs[output_key] = f"mock_{output_key}"
            message = f"Extracted {output_key}"

        logs.append(
            {
                "step_id": step.get("id", f"step_{index}"),
                "step_type": step_type,
                "status": "success",
                "message": message,
                "screenshot_path": None,
                "duration_ms": 200 if step_type != "wait" else int(step.get("duration_ms", 1500)),
            }
        )

    for output in workflow.get("outputs", []):
        outputs.setdefault(output["name"], f"mock_{output['name']}")

    execution_payload = {
        "execution_id": execution_id,
        "status": "success",
        "outputs": outputs,
        "duration_ms": sum(item["duration_ms"] for item in logs),
        "logs": logs,
        "inputs": inputs,
        "workflow_slug": workflow.get("slug", "unknown"),
        "created_at": _utc_now(),
    }
    (EXECUTIONS_DIR / f"{execution_id}.json").write_text(
        json.dumps(execution_payload, indent=2),
        encoding="utf-8",
    )
    return execution_payload


def load_execution_logs(execution_id: str) -> list[dict]:
    execution_path = EXECUTIONS_DIR / f"{execution_id}.json"
    if not execution_path.exists():
        raise FileNotFoundError(f"Execution not found: {execution_id}")
    payload = json.loads(execution_path.read_text(encoding="utf-8"))
    return payload.get("logs", [])
