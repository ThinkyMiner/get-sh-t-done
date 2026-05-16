from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from analyzer.schema_validator import validate_and_fix

SKILLS_ROOT = Path(__file__).resolve().parent.parent / "skills"
LEGACY_SKILLS_ROOT = Path(__file__).resolve().parent.parent / "workflow_skills"


@dataclass(frozen=True)
class WorkflowSkill:
    name: str
    description: str
    detection_terms: tuple[str, ...]
    core_instructions: str
    timeline_guidance: str
    workflow_guidance: str
    agent_display_name: str | None = None
    agent_short_description: str | None = None
    agent_default_prompt: str | None = None
    workflow_template: dict[str, Any] | None = None


def _timeline_text_blob(timeline: dict | None, user_context: str = "") -> str:
    parts: list[str] = [user_context]
    if timeline:
        parts.extend(
            [
                str(timeline.get("workflow_goal") or ""),
                str(timeline.get("start_url") or ""),
                str(timeline.get("likely_app_name") or ""),
            ]
        )
        for action in timeline.get("actions") or []:
            parts.extend(
                [
                    str(action.get("screen_state") or ""),
                    str(action.get("user_action") or ""),
                    str(action.get("target_text") or ""),
                    str(action.get("result") or ""),
                ]
            )
        for item in timeline.get("candidate_outputs") or []:
            parts.append(str(item.get("source_text") or ""))
    return " ".join(parts).lower()


def _split_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    if not markdown.startswith("---\n"):
        return {}, markdown
    end_marker = "\n---\n"
    end_index = markdown.find(end_marker, 4)
    if end_index == -1:
        return {}, markdown
    frontmatter_text = markdown[4:end_index]
    body = markdown[end_index + len(end_marker) :]
    parsed = yaml.safe_load(frontmatter_text) or {}
    return parsed if isinstance(parsed, dict) else {}, body


def _read_text_if_exists(path: Path) -> str:
    return path.read_text().strip() if path.exists() else ""


def _join_texts(*parts: str) -> str:
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return "\n\n".join(cleaned)


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text())


def _read_yaml_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    parsed = yaml.safe_load(path.read_text()) or {}
    return parsed if isinstance(parsed, dict) else {}


def _load_skill_folder(path: Path) -> WorkflowSkill | None:
    skill_md_path = path / "SKILL.md"
    if not skill_md_path.exists():
        return None

    frontmatter, body = _split_frontmatter(skill_md_path.read_text())
    agent_meta = _read_yaml_if_exists(path / "agents" / "openai.yaml")
    interface_meta = agent_meta.get("interface") if isinstance(agent_meta.get("interface"), dict) else agent_meta
    name = str(frontmatter.get("name") or path.name).strip()
    description = str(frontmatter.get("description") or "").strip()
    detection_terms = tuple(str(term).lower() for term in frontmatter.get("detection_terms") or [])
    core_instructions = body.strip()
    timeline_guidance = _join_texts(
        core_instructions,
        _read_text_if_exists(path / "references" / "timeline-guidance.md"),
        _read_text_if_exists(path / "references" / "failure-patterns.md"),
    )
    workflow_guidance = _join_texts(
        core_instructions,
        _read_text_if_exists(path / "references" / "workflow-guidance.md"),
        _read_text_if_exists(path / "references" / "runtime-guidance.md"),
        _read_text_if_exists(path / "references" / "failure-patterns.md"),
    )
    workflow_template = _read_json_if_exists(path / "assets" / "workflow-template.json")

    if not name or not description:
        return None

    return WorkflowSkill(
        name=name,
        description=description,
        detection_terms=detection_terms,
        core_instructions=core_instructions,
        timeline_guidance=timeline_guidance,
        workflow_guidance=workflow_guidance,
        agent_display_name=str(interface_meta.get("display_name") or "").strip() or None,
        agent_short_description=str(interface_meta.get("short_description") or "").strip() or None,
        agent_default_prompt=str(interface_meta.get("default_prompt") or "").strip() or None,
        workflow_template=workflow_template,
    )


@lru_cache(maxsize=1)
def load_skills() -> tuple[WorkflowSkill, ...]:
    root = SKILLS_ROOT if SKILLS_ROOT.exists() else LEGACY_SKILLS_ROOT
    if not root.exists():
        return ()

    loaded: list[WorkflowSkill] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        skill = _load_skill_folder(child)
        if skill:
            loaded.append(skill)
    return tuple(loaded)


def detect_skill(timeline: dict | None, user_context: str = "") -> WorkflowSkill | None:
    blob = _timeline_text_blob(timeline, user_context=user_context)
    best_skill: WorkflowSkill | None = None
    best_score = 0
    for skill in load_skills():
        score = sum(1 for term in skill.detection_terms if term in blob)
        if score > best_score:
            best_skill = skill
            best_score = score
    return best_skill if best_score > 0 else None


def build_timeline_skill_context(skill: WorkflowSkill | None) -> str:
    return skill.timeline_guidance if skill else ""


def build_workflow_skill_context(skill: WorkflowSkill | None) -> str:
    return skill.workflow_guidance if skill else ""


def apply_skill_postprocessing(
    skill: WorkflowSkill | None,
    workflow: dict[str, Any],
    timeline: dict | None,
) -> dict[str, Any]:
    del timeline
    if not skill or not skill.workflow_template:
        return workflow
    return validate_and_fix(skill.workflow_template)
