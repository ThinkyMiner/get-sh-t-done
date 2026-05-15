from __future__ import annotations

from PIL import Image
import imagehash


def deduplicate_frames(frames: list[dict], threshold: int = 5) -> list[dict]:
    """
    Keep frames whose perceptual hash differs enough from the last kept frame.
    """
    if not frames:
        return []

    kept = [frames[0]]
    previous_hash = imagehash.average_hash(Image.open(frames[0]["path"]))

    for frame in frames[1:]:
        current_hash = imagehash.average_hash(Image.open(frame["path"]))
        if abs(current_hash - previous_hash) > threshold:
            kept.append(frame)
            previous_hash = current_hash

    return kept
