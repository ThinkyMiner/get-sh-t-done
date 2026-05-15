from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api import database
from api.storage import screenshot_url

router = APIRouter(prefix="/api/executions", tags=["executions"])


@router.get("/{execution_id}/logs")
async def get_execution_logs(execution_id: str) -> list[dict[str, object]]:
    if database.get_execution(execution_id) is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    logs = database.get_execution_logs(execution_id)
    for log in logs:
        log["screenshot_url"] = screenshot_url(log.get("screenshot_path"))
    return logs


@router.get("/{execution_id}")
async def get_execution(execution_id: str) -> dict[str, object]:
    record = database.get_execution(execution_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    record["logs_url"] = f"/api/executions/{execution_id}/logs"
    return record

