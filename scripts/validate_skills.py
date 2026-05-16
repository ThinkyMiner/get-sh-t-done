from __future__ import annotations

from pathlib import Path
import sys

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_ROOT = REPO_ROOT / "skills"
REQUIRED_AGENT_KEYS = ("display_name", "short_description", "default_prompt")


def _split_frontmatter(markdown: str) -> tuple[dict, str]:
    if not markdown.startswith("---\n"):
        return {}, markdown
    end_marker = "\n---\n"
    end_index = markdown.find(end_marker, 4)
    if end_index == -1:
        return {}, markdown
    frontmatter = yaml.safe_load(markdown[4:end_index]) or {}
    body = markdown[end_index + len(end_marker) :]
    return frontmatter if isinstance(frontmatter, dict) else {}, body


def validate_skill_folder(path: Path) -> list[str]:
    errors: list[str] = []
    skill_md = path / "SKILL.md"
    agent_yaml = path / "agents" / "openai.yaml"

    if not skill_md.exists():
        return [f"{path.name}: missing SKILL.md"]

    frontmatter, body = _split_frontmatter(skill_md.read_text())
    if not frontmatter.get("name"):
        errors.append(f"{path.name}: SKILL.md missing frontmatter name")
    if not frontmatter.get("description"):
        errors.append(f"{path.name}: SKILL.md missing frontmatter description")
    if not body.strip():
        errors.append(f"{path.name}: SKILL.md body is empty")

    if not agent_yaml.exists():
        errors.append(f"{path.name}: missing agents/openai.yaml")
    else:
        parsed = yaml.safe_load(agent_yaml.read_text()) or {}
        if not isinstance(parsed, dict):
            errors.append(f"{path.name}: agents/openai.yaml is not a mapping")
        else:
            interface = parsed.get("interface")
            if not isinstance(interface, dict):
                errors.append(f"{path.name}: agents/openai.yaml missing interface mapping")
                interface = {}
            for key in REQUIRED_AGENT_KEYS:
                if not str(interface.get(key) or "").strip():
                    errors.append(f"{path.name}: agents/openai.yaml missing {key}")

    return errors


def main() -> int:
    if not SKILLS_ROOT.exists():
        print("skills root missing", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for child in sorted(SKILLS_ROOT.iterdir()):
        if child.is_dir():
            all_errors.extend(validate_skill_folder(child))

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1

    print(f"validated {len([p for p in SKILLS_ROOT.iterdir() if p.is_dir()])} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
