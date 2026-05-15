from __future__ import annotations

import json
import os
from typing import Any

AI_SELECTOR_PROMPT = """I am automating a browser task. I need to {description}.
The step type is '{step_type}'.
I tried to find an element using {selector_type}='{selector_value}' but it was not found.

Look at this screenshot of the current page state.
Identify the correct element I should interact with.

Return ONLY a JSON object:
{{
  "selector_type": "css" | "text" | "test_id" | "label" | "role",
  "selector_value": "the correct selector"
}}"""


async def ai_resolve_selector(
    page: Any,
    step: dict[str, Any],
    screenshot_path: str,
) -> dict[str, str] | None:
    """Hook for vision-LLM selector repair.

    The hackathon demo can run without a model key, so this returns None unless a
    future integration sets FLOW2API_AI_FALLBACK_RESPONSE to a JSON selector.
    That env var is useful for local smoke tests of the fallback path.
    """
    response = os.getenv("FLOW2API_AI_FALLBACK_RESPONSE")
    if not response:
        return None

    try:
        payload = json.loads(response)
    except json.JSONDecodeError:
        return None

    selector_type = payload.get("selector_type")
    selector_value = payload.get("selector_value")
    if selector_type and selector_value:
        return {"selector_type": selector_type, "selector_value": selector_value}
    return None

