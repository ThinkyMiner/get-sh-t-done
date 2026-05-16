from __future__ import annotations

import glob
import os
import shutil
import subprocess
from pathlib import Path


def _format_timestamp(seconds: float) -> str:
    whole_seconds = int(seconds)
    milliseconds = int(round((seconds - whole_seconds) * 1000))
    if milliseconds == 1000:
        whole_seconds += 1
        milliseconds = 0

    hours = whole_seconds // 3600
    minutes = (whole_seconds % 3600) // 60
    secs = whole_seconds % 60
    if milliseconds:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def extract_frames(video_path: str, output_dir: str, fps: float = 0.5) -> list[dict]:
    """
    Extract PNG frames from a video.

    `fps=0.5` means one frame every two seconds.
    """
    if fps <= 0:
        raise ValueError("fps must be greater than 0")

    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required but was not found on PATH")

    source = Path(video_path)
    if not source.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    os.makedirs(output_dir, exist_ok=True)
    output_pattern = str(Path(output_dir) / "frame_%04d.png")

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(source),
            "-vf",
            f"fps={fps}",
            "-q:v",
            "2",
            output_pattern,
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    frames = sorted(glob.glob(str(Path(output_dir) / "frame_*.png")))
    result: list[dict] = []
    for index, path in enumerate(frames):
        result.append(
            {
                "index": index,
                "timestamp": _format_timestamp(index / fps),
                "path": path,
            }
        )

    return result
