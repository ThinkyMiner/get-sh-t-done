from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Body, HTTPException

from api import database
from api.storage import screenshot_url
from engine.runner import run_workflow

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


def _workflow_body(record: dict[str, Any]) -> dict[str, Any]:
    return record["workflow_json"]


def _extract_inputs(body: dict[str, Any]) -> dict[str, Any]:
    return body.get("inputs") if isinstance(body.get("inputs"), dict) else body


def _result_payload(result: Any) -> dict[str, Any]:
    return {
        "execution_id": result.execution_id,
        "status": result.status,
        "outputs": result.outputs,
        "duration_ms": result.duration_ms,
        "error_message": result.error_message,
        "logs_url": f"/api/executions/{result.execution_id}/logs",
    }


def generate_docs(workflow: dict[str, Any]) -> dict[str, Any]:
    slug = workflow["slug"]
    request_example = {
        inp["name"]: f"<{inp.get('type', 'string')}>"
        for inp in workflow.get("inputs", [])
    }
    curl_body = json.dumps(request_example)
    python_body = json.dumps(request_example, indent=4)
    return {
        "endpoint": f"POST /api/generated/{slug}/run",
        "method": "POST",
        "description": workflow.get("description", ""),
        "request_body": {
            inp["name"]: {
                "type": inp.get("type", "string"),
                "required": inp.get("required", True),
            }
            for inp in workflow.get("inputs", [])
        },
        "response_body": {
            out["name"]: {"type": out.get("type", "string")}
            for out in workflow.get("outputs", [])
        },
        "curl_example": (
            f"curl -X POST http://localhost:8000/api/generated/{slug}/run \\\n"
            "  -H \"Content-Type: application/json\" \\\n"
            f"  -d '{curl_body}'"
        ),
        "python_example": (
            "import requests\n\n"
            "response = requests.post(\n"
            f"    \"http://localhost:8000/api/generated/{slug}/run\",\n"
            f"    json={python_body}\n"
            ")\n"
            "print(response.json())"
        ),
    }


@router.post("")
async def create_workflow(workflow: dict[str, Any] = Body(...)) -> dict[str, Any]:
    created = database.create_workflow(workflow, force_slug=True)
    return {
        "status": "created",
        "workflow_id": created["id"],
        "id": created["id"],
        "slug": created["slug"],
        "name": created["name"],
        "workflow": created["workflow_json"],
        "workflow_json": created["workflow_json"],
    }


@router.get("")
async def list_workflows() -> list[dict[str, Any]]:
    return database.list_workflows()


@router.get("/{workflow_id}/docs")
async def get_workflow_docs(workflow_id: str) -> dict[str, Any]:
    record = database.get_workflow_by_id(workflow_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return generate_docs(_workflow_body(record))


@router.post("/{workflow_id}/test")
async def test_workflow(
    workflow_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    record = database.get_workflow_by_id(workflow_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Workflow not found")

    inputs = _extract_inputs(body)
    execution_id = database.create_execution(workflow_id, inputs)
    result = await run_workflow(_workflow_body(record), inputs, execution_id)
    database.update_execution(
        execution_id,
        status=result.status,
        outputs=result.outputs,
        error_message=result.error_message,
        duration_ms=result.duration_ms,
    )
    database.save_execution_logs(execution_id, result.logs)
    return _result_payload(result)


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str) -> dict[str, Any]:
    record = database.get_workflow_by_id(workflow_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return record


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    workflow: dict[str, Any] = Body(...),
) -> dict[str, Any]:
    updated = database.update_workflow(workflow_id, workflow)
    if updated is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {
        "status": "updated",
        "workflow_id": updated["id"],
        "id": updated["id"],
        "slug": updated["slug"],
        "name": updated["name"],
        "workflow": updated["workflow_json"],
        "workflow_json": updated["workflow_json"],
    }


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str) -> dict[str, bool]:
    deleted = database.delete_workflow(workflow_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"deleted": True}
