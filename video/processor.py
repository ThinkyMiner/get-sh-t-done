from __future__ import annotations

import os

from video.deduplicator import deduplicate_frames
from video.frame_extractor import extract_frames


def process_video(video_path: str, video_id: str, storage_dir: str = "storage") -> dict:
    """
    Extract frames, remove near-duplicates, and return a keyframe summary.
    """
    frames_dir = os.path.join(storage_dir, "frames", video_id)
    all_frames = extract_frames(video_path, frames_dir, fps=0.5)
    keyframes = deduplicate_frames(all_frames, threshold=5)

    return {
        "video_id": video_id,
        "total_frames_extracted": len(all_frames),
        "keyframes_kept": len(keyframes),
        "keyframes": keyframes,
    }
