from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from fastapi import UploadFile

STORAGE_ROOT = Path("storage")
SCREENSHOTS_DIR = STORAGE_ROOT / "screenshots"
FRAMES_DIR = STORAGE_ROOT / "frames"
VIDEOS_DIR = STORAGE_ROOT / "videos"
DOWNLOADS_DIR = STORAGE_ROOT / "downloads"
DB_PATH = STORAGE_ROOT / "flow2api.db"


def ensure_storage_dirs() -> None:
    for path in [STORAGE_ROOT, SCREENSHOTS_DIR, FRAMES_DIR, VIDEOS_DIR, DOWNLOADS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def safe_filename(filename: str | None) -> str:
    base = Path(filename or "upload.bin").name
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]+", "_", base).strip("._")
    return cleaned or "upload.bin"


async def save_video_upload(upload: "UploadFile") -> tuple[str, str]:
    ensure_storage_dirs()
    video_id = str(uuid4())
    filename = safe_filename(upload.filename)
    target = VIDEOS_DIR / f"{video_id}_{filename}"
    with target.open("wb") as handle:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
    return video_id, str(target)


def screenshot_url(path: str | None) -> str | None:
    if not path:
        return None
    try:
        rel = Path(path).relative_to(SCREENSHOTS_DIR)
    except ValueError:
        try:
            rel = Path(path).resolve().relative_to(SCREENSHOTS_DIR.resolve())
        except ValueError:
            return None
    return f"/screenshots/{rel.as_posix()}"


def frame_url(path: str | None) -> str | None:
    if not path:
        return None
    try:
        rel = Path(path).relative_to(FRAMES_DIR)
    except ValueError:
        try:
            rel = Path(path).resolve().relative_to(FRAMES_DIR.resolve())
        except ValueError:
            return None
    return f"/frames/{rel.as_posix()}"
