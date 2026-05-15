from __future__ import annotations

import re
from pathlib import Path

from playwright.async_api import Page

SCREENSHOT_ROOT = Path("storage/screenshots")


def screenshot_dir(execution_id: str) -> Path:
    path = SCREENSHOT_ROOT / execution_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_filename(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_") or "step"


async def take_screenshot(page: Page, execution_id: str, step_id: str) -> str:
    directory = screenshot_dir(execution_id)
    filename = f"step_{_safe_filename(step_id)}.png"
    path = directory / filename
    await page.screenshot(path=str(path), full_page=True)
    return str(path)

