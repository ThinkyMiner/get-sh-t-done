from __future__ import annotations

import base64
import json
from pathlib import Path

from analyzer.config import (
    ANTHROPIC_MODEL,
    OPENAI_MODEL,
    get_provider,
    has_anthropic_key,
    has_openai_key,
)
from analyzer.prompts import SYSTEM_PROMPT, build_analysis_prompt
from analyzer.schema_validator import validate_and_fix
from video.processor import process_video


def _strip_code_fences(raw_text: str) -> str:
    raw = raw_text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:-3]
    return raw.strip()


def _mock_workflow(user_context: str = "") -> dict:
    description = user_context or "Automated workflow from video"
    return validate_and_fix(
        {
            "workflow_name": "check_supplier_status",
            "slug": "check-supplier-status",
            "description": description,
            "inputs": [{"name": "supplier_id", "type": "string", "required": True}],
            "steps": [
                {
                    "id": "step_1",
                    "type": "navigate",
                    "url": "http://localhost:5500/dashboard",
                    "description": "Open the supplier dashboard",
                    "confidence": "high",
                },
                {
                    "id": "step_2",
                    "type": "fill",
                    "selector_type": "label",
                    "selector_value": "Supplier ID",
                    "value": "{{supplier_id}}",
                    "description": "Type the supplier ID into the search field",
                    "confidence": "high",
                },
                {
                    "id": "step_3",
                    "type": "click",
                    "selector_type": "role",
                    "selector_value": "Search",
                    "description": "Click the search button",
                    "confidence": "high",
                },
                {
                    "id": "step_4",
                    "type": "wait",
                    "duration_ms": 1500,
                    "description": "Wait for results to load",
                    "confidence": "medium",
                },
                {
                    "id": "step_5",
                    "type": "extract_text",
                    "selector_type": "test_id",
                    "selector_value": "verification-status",
                    "output_key": "verification_status",
                    "description": "Read the verification status from the results",
                    "confidence": "high",
                },
            ],
            "outputs": [{"name": "verification_status", "type": "string"}],
        }
    )


async def _analyze_with_anthropic(keyframes: list[dict], user_context: str) -> dict:
    import anthropic

    client = anthropic.Anthropic()
    content: list[dict] = []
    for index, frame in enumerate(keyframes):
        with open(frame["path"], "rb") as file_obj:
            img_b64 = base64.b64encode(file_obj.read()).decode()
        content.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_b64,
                },
            }
        )
        content.append(
            {"type": "text", "text": f"Screenshot {index + 1} - timestamp {frame['timestamp']}"}
        )

    content.append({"type": "text", "text": build_analysis_prompt(user_context)})
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )

    raw_text = response.content[0].text
    return validate_and_fix(json.loads(_strip_code_fences(raw_text)))


async def _analyze_with_openai(keyframes: list[dict], user_context: str) -> dict:
    from openai import OpenAI

    client = OpenAI()
    content: list[dict] = []
    for index, frame in enumerate(keyframes):
        with open(frame["path"], "rb") as file_obj:
            img_b64 = base64.b64encode(file_obj.read()).decode()
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{img_b64}"},
            }
        )
        content.append(
            {"type": "text", "text": f"Screenshot {index + 1} - timestamp {frame['timestamp']}"}
        )

    content.append({"type": "text", "text": build_analysis_prompt(user_context)})
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        max_tokens=4096,
    )
    raw_text = response.choices[0].message.content or "{}"
    return validate_and_fix(json.loads(_strip_code_fences(raw_text)))


async def analyze_frames(keyframes: list[dict], user_context: str = "") -> dict:
    """
    Analyze curated keyframes and return workflow JSON.
    """
    provider = get_provider()
    if provider == "anthropic" and has_anthropic_key():
        return await _analyze_with_anthropic(keyframes, user_context)
    if provider == "openai" and has_openai_key():
        return await _analyze_with_openai(keyframes, user_context)
    return _mock_workflow(user_context)


async def analyze_video(video_id: str, video_path: str, user_context: str = "") -> dict:
    """
    Full pipeline: video -> keyframes -> LLM -> validated workflow JSON.
    """
    if not Path(video_path).exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    processing_result = process_video(video_path=video_path, video_id=video_id)
    workflow = await analyze_frames(processing_result["keyframes"], user_context=user_context)
    workflow["_video"] = {
        "video_id": video_id,
        "video_path": video_path,
        "keyframes_kept": processing_result["keyframes_kept"],
    }
    return workflow
