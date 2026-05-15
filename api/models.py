from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class WorkflowRunRequest(BaseModel):
    inputs: dict[str, Any] = Field(default_factory=dict)


class GeneratedRunResponse(BaseModel):
    execution_id: str
    status: str
    outputs: dict[str, Any]
    duration_ms: int
    logs_url: str


class VideoAnalyzeRequest(BaseModel):
    user_context: str = ""

