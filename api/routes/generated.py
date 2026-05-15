from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from api import database
from engine.runner import run_workflow

router = APIRouter(prefix="/api/generated", tags=["generated"])


def _validate_inputs(workflow: dict[str, Any], body: dict[str, Any]) -> None:
    missing = [
        item["name"]
        for item in workflow.get("inputs", [])
        if item.get("required", True) and item.get("name") not in body
    ]
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required input(s): {', '.join(missing)}",
        )


@router.post("/{slug}/run")
async def run_generated_api(
    slug: str,
    body: dict[str, Any] = Body(default_factory=dict),
) -> dict[str, Any]:
    record = database.get_workflow_by_slug(slug)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"No workflow found for generated API slug '{slug}'",
        )

    workflow = record["workflow_json"]
    _validate_inputs(workflow, body)
    execution_id = database.create_execution(record["id"], body)
    result = await run_workflow(workflow, body, execution_id)
    database.update_execution(
        execution_id,
        status=result.status,
        outputs=result.outputs,
        error_message=result.error_message,
        duration_ms=result.duration_ms,
    )
    database.save_execution_logs(execution_id, result.logs)

    return {
        "execution_id": execution_id,
        "status": result.status,
        "outputs": result.outputs,
        "duration_ms": result.duration_ms,
        "logs_url": f"/api/executions/{execution_id}/logs",
    }

