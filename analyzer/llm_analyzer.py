from __future__ import annotations

import base64
import json
import re
from pathlib import Path

import requests

from analyzer.config import (
    ANTHROPIC_MODEL,
    LITELLM_PROXY_API_BASE,
    LITELLM_PROXY_API_KEY,
    LITELLM_PROXY_MODEL,
    OPENAI_MODEL,
    get_provider,
    has_anthropic_key,
    has_litellm_proxy_config,
    has_openai_key,
)
from analyzer.prompts import (
    TIMELINE_SYSTEM_PROMPT,
    WORKFLOW_SYSTEM_PROMPT,
    build_timeline_prompt,
    build_workflow_prompt_from_timeline,
)
from analyzer.schema_validator import VALID_STEP_TYPES, validate_and_fix
from analyzer.skills import (
    apply_skill_postprocessing,
    build_timeline_skill_context,
    build_workflow_skill_context,
    detect_skill,
)
from video.processor import process_video

EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
REQUIRED_AUTOMATION_STEP_TYPES = {"navigate", "click", "fill"}


def _strip_code_fences(raw_text: str) -> str:
    raw = raw_text.strip()
    if raw.startswith("```"):
        parts = raw.split("\n", 1)
        raw = parts[1] if len(parts) == 2 else raw
        if raw.endswith("```"):
            raw = raw[:-3]
    return raw.strip()


def _extract_json_text(raw_text: str) -> str:
    stripped = _strip_code_fences(raw_text)
    if not stripped:
        return ""

    object_match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if object_match:
        return object_match.group(0)

    array_match = re.search(r"\[.*\]", stripped, re.DOTALL)
    if array_match:
        return array_match.group(0)

    return stripped


def _parse_json_dict(raw_text: str) -> dict | None:
    json_text = _extract_json_text(raw_text)
    if not json_text:
        return None

    try:
        parsed = json.loads(json_text)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def _build_openai_content(keyframes: list[dict], prompt: str) -> list[dict]:
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
            {
                "type": "text",
                "text": f"Screenshot {index + 1} at {frame['timestamp']}",
            }
        )
    content.append({"type": "text", "text": prompt})
    return content


def _build_anthropic_content(keyframes: list[dict], prompt: str) -> list[dict]:
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
            {
                "type": "text",
                "text": f"Screenshot {index + 1} at {frame['timestamp']}",
            }
        )
    content.append({"type": "text", "text": prompt})
    return content


async def _call_anthropic(keyframes: list[dict], system_prompt: str, prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": _build_anthropic_content(keyframes, prompt)}],
    )
    return response.content[0].text or ""


async def _call_openai(keyframes: list[dict], system_prompt: str, prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI()
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": _build_openai_content(keyframes, prompt)},
        ],
        max_tokens=4096,
    )
    return response.choices[0].message.content or ""


async def _call_litellm_proxy(keyframes: list[dict], system_prompt: str, prompt: str) -> str:
    response = requests.post(
        f"{LITELLM_PROXY_API_BASE.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {LITELLM_PROXY_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": LITELLM_PROXY_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": _build_openai_content(keyframes, prompt)},
            ],
            "max_tokens": 4096,
        },
        timeout=180,
    )
    response.raise_for_status()
    payload = response.json()
    return (((payload.get("choices") or [{}])[0].get("message") or {}).get("content")) or ""


async def _call_model(provider: str, keyframes: list[dict], system_prompt: str, prompt: str) -> str:
    if provider == "anthropic":
        return await _call_anthropic(keyframes, system_prompt, prompt)
    if provider == "openai":
        return await _call_openai(keyframes, system_prompt, prompt)
    if provider == "litellm_proxy":
        return await _call_litellm_proxy(keyframes, system_prompt, prompt)
    return ""


def _finalize_timeline(raw_text: str) -> dict | None:
    timeline = _parse_json_dict(raw_text)
    if not timeline:
        return None

    timeline["workflow_goal"] = timeline.get("workflow_goal") or ""
    timeline["start_url"] = timeline.get("start_url") or ""
    timeline["likely_app_name"] = timeline.get("likely_app_name") or ""
    timeline["candidate_inputs"] = list(timeline.get("candidate_inputs") or [])
    timeline["candidate_outputs"] = list(timeline.get("candidate_outputs") or [])
    timeline["actions"] = list(timeline.get("actions") or [])
    return timeline


def _guess_output_name(source_text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", source_text).strip("_").lower()
    return cleaned[:40] or "result"


def _normalize_account_selector(step: dict) -> None:
    selector_type = step.get("selector_type")
    selector_value = str(step.get("selector_value") or "")
    description = str(step.get("description") or "")

    if not selector_value:
        return

    has_email = bool(EMAIL_RE.search(selector_value))
    account_hint = "account" in description.lower() or "google" in description.lower()
    if has_email and account_hint:
        name_only = EMAIL_RE.sub("", selector_value).strip(" []'\":=-")
        name_only = re.sub(r"\s{2,}", " ", name_only).strip()
        if name_only:
            step["selector_type"] = "text"
            step["selector_value"] = name_only
        else:
            step["selector_type"] = "text"
            step["selector_value"] = "Use another account"


def _infer_confirmation_output(workflow: dict, timeline: dict | None) -> None:
    if not timeline:
        return

    candidate_outputs = timeline.get("candidate_outputs") or []
    if not candidate_outputs:
        return

    existing_extract_outputs = {
        step.get("output_key")
        for step in workflow.get("steps", [])
        if step.get("type") in {"extract_text", "extract_table"} and step.get("output_key")
    }

    source_text = str(candidate_outputs[0].get("source_text") or "").strip()
    if not source_text:
        return

    output_name = candidate_outputs[0].get("name") or _guess_output_name(source_text)
    if output_name in existing_extract_outputs:
        return

    workflow.setdefault("steps", []).append(
        {
            "id": f"step_{len(workflow.get('steps', [])) + 1}",
            "type": "extract_text",
            "selector_type": "text",
            "selector_value": source_text,
            "output_key": output_name,
            "description": "Read the visible confirmation or result text",
            "confidence": "medium",
        }
    )

    existing_outputs = {item.get("name") for item in workflow.get("outputs", [])}
    if output_name not in existing_outputs:
        workflow.setdefault("outputs", []).append({"name": output_name, "type": "string"})


def _sanitize_workflow(workflow: dict, timeline: dict | None) -> dict:
    for step in workflow.get("steps", []):
        if step.get("type") in {"click", "select"}:
            _normalize_account_selector(step)

        selector_value = step.get("selector_value")
        if isinstance(selector_value, str):
            step["selector_value"] = selector_value.strip()

        if step.get("type") == "click" and step.get("selector_type") == "role":
            selector_value = str(step.get("selector_value") or "")
            description = str(step.get("description") or "")
            if selector_value.lower() == "button":
                quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", description)
                flattened = [item for pair in quoted for item in pair if item]
                if flattened:
                    step["selector_type"] = "text"
                    step["selector_value"] = flattened[0]

    _infer_confirmation_output(workflow, timeline)
    return workflow


def _finalize_workflow(raw_text: str, user_context: str, timeline: dict | None) -> dict:
    parsed = _parse_json_dict(raw_text)
    if not parsed:
        return _mock_workflow(user_context)

    workflow = validate_and_fix(parsed)
    workflow = _sanitize_workflow(workflow, timeline)
    workflow = validate_and_fix(workflow)

    invalid_steps = [
        step for step in workflow.get("steps", []) if step.get("type") not in VALID_STEP_TYPES
    ]
    if invalid_steps:
        return _mock_workflow(user_context)

    has_automation_step = any(
        step.get("type") in REQUIRED_AUTOMATION_STEP_TYPES for step in workflow.get("steps", [])
    )
    if not has_automation_step:
        return _mock_workflow(user_context)

    return workflow


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
                    "url": "http://localhost:5500/dashboard.html",
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
                    "selector_type": "text",
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


async def analyze_frames(keyframes: list[dict], user_context: str = "") -> dict:
    """Analyze curated keyframes and return workflow JSON."""
    provider = get_provider()
    if provider == "litellm_proxy" and not has_litellm_proxy_config():
        return _mock_workflow(user_context)
    if provider == "anthropic" and not has_anthropic_key():
        return _mock_workflow(user_context)
    if provider == "openai" and not has_openai_key():
        return _mock_workflow(user_context)
    if provider == "mock":
        return _mock_workflow(user_context)

    hinted_skill = detect_skill(None, user_context=user_context)

    timeline_raw = await _call_model(
        provider,
        keyframes,
        TIMELINE_SYSTEM_PROMPT,
        build_timeline_prompt(
            user_context,
            skill_context=build_timeline_skill_context(hinted_skill),
        ),
    )
    timeline = _finalize_timeline(timeline_raw)
    active_skill = detect_skill(timeline, user_context=user_context) or hinted_skill

    workflow_raw = await _call_model(
        provider,
        keyframes,
        WORKFLOW_SYSTEM_PROMPT,
        build_workflow_prompt_from_timeline(
            timeline or {},
            user_context,
            skill_context=build_workflow_skill_context(active_skill),
        ),
    )
    workflow = _finalize_workflow(workflow_raw, user_context, timeline)
    workflow = apply_skill_postprocessing(active_skill, workflow, timeline)

    if timeline:
        workflow["_timeline"] = timeline
    if active_skill:
        workflow["_skill"] = {
            "name": active_skill.name,
            "description": active_skill.description,
        }
    return workflow


async def analyze_video(video_id: str, video_path: str, user_context: str = "") -> dict:
    """Full pipeline: video -> keyframes -> LLM -> validated workflow JSON."""
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
