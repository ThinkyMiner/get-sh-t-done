from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from api import database
from api.models import VideoAnalyzeRequest
from api.storage import save_video_upload

router = APIRouter(prefix="/api/videos", tags=["videos"])


def _confidence_score(workflow: dict[str, object]) -> float:
    weights = {"high": 0.9, "medium": 0.7, "low": 0.5}
    steps = workflow.get("steps", [])
    if not isinstance(steps, list) or not steps:
        return 0.0
    scores: list[float] = []
    for step in steps:
        if isinstance(step, dict):
            scores.append(weights.get(str(step.get("confidence", "medium")).lower(), 0.7))
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)) -> dict[str, object]:
    video_id, file_path = await save_video_upload(file)
    record = database.create_video(video_id, file.filename, file_path)
    return {
        "video_id": video_id,
        "filename": record["filename"],
        "file_path": record["file_path"],
        "status": record["status"],
    }


@router.post("/{video_id}/analyze")
async def analyze_video_endpoint(
    video_id: str,
    request: VideoAnalyzeRequest | None = None,
) -> dict[str, object]:
    video = database.get_video(video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        from analyzer.llm_analyzer import analyze_video
    except ImportError:
        return {
            "status": "pending",
            "message": "Analysis module not yet connected",
        }

    user_context = request.user_context if request else ""
    try:
        workflow = await analyze_video(video_id, video["file_path"], user_context=user_context)
    except NotImplementedError:
        return {
            "status": "pending",
            "message": "Analysis module not yet connected",
        }

    if not workflow:
        return {
            "status": "pending",
            "message": "Analysis module returned no workflow",
        }

    saved = database.create_workflow(
        workflow,
        source="video_analysis",
        video_id=video_id,
        force_slug=False,
    )
    database.update_video(video_id, status="analyzed", workflow_id=saved["id"])
    return {
        "status": "completed",
        "confidence": _confidence_score(saved["workflow_json"]),
        "workflow_id": saved["id"],
        "workflow": saved["workflow_json"],
        "workflow_json": saved["workflow_json"],
    }
