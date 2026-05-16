from __future__ import annotations

import os

from video.deduplicator import deduplicate_frames
from video.frame_extractor import extract_frames


def _curate_keyframes(
    all_frames: list[dict],
    dedup_threshold: int,
    target_keyframes: int = 5,
) -> list[dict]:
    keyframes = deduplicate_frames(all_frames, threshold=dedup_threshold)
    desired = min(target_keyframes, len(all_frames))
    relaxed_threshold = dedup_threshold

    while len(keyframes) < desired and relaxed_threshold > 0:
        relaxed_threshold -= 1
        candidate = deduplicate_frames(all_frames, threshold=relaxed_threshold)
        if len(candidate) > len(keyframes):
            keyframes = candidate

    return keyframes


def process_video(
    video_path: str,
    video_id: str,
    storage_dir: str = "storage",
    *,
    fps: float = 1.0,
    dedup_threshold: int = 1,
) -> dict:
    """
    Extract frames, remove near-duplicates, and return a keyframe summary.
    """
    frames_dir = os.path.join(storage_dir, "frames", video_id)
    all_frames = extract_frames(video_path, frames_dir, fps=fps)
    keyframes = _curate_keyframes(all_frames, dedup_threshold=dedup_threshold)

    return {
        "video_id": video_id,
        "total_frames_extracted": len(all_frames),
        "keyframes_kept": len(keyframes),
        "keyframes": keyframes,
    }
