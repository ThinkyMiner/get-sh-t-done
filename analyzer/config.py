from __future__ import annotations

import os


DEFAULT_PROVIDER = os.getenv("FLOW2API_LLM_PROVIDER", "mock").lower()
ANTHROPIC_MODEL = os.getenv("FLOW2API_ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
OPENAI_MODEL = os.getenv("FLOW2API_OPENAI_MODEL", "gpt-4o")


def get_provider() -> str:
    if DEFAULT_PROVIDER in {"anthropic", "openai", "mock"}:
        return DEFAULT_PROVIDER
    return "mock"


def has_anthropic_key() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY"))


def has_openai_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))
