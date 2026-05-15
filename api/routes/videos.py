from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from api import database
from api.models import VideoAnalyzeRequest
from api.storage import FRAMES_DIR, save_video_upload

router = APIRouter(prefix="/api/videos", tags=["videos"])


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

    frames_dir = str(FRAMES_DIR / video_id)
    user_context = request.user_context if request else ""
    try:
        workflow = await analyze_video(video_id, frames_dir, user_context=user_context)
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
        "workflow_id": saved["id"],
        "workflow": saved["workflow_json"],
    }

