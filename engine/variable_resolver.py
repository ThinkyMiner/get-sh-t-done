from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from .exceptions import VariableResolutionError

VARIABLE_PATTERN = re.compile(
    r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)(?:\[(\d+)\])?\s*\}\}"
)


def _resolve_variable(variable_name: str, index: str | None, inputs: dict[str, Any]) -> Any:
    if variable_name not in inputs:
        raise VariableResolutionError(f"Missing input variable: {variable_name}")

    value = inputs[variable_name]
    if index is None:
        return value

    position = int(index)
    try:
        return value[position]
    except (IndexError, KeyError, TypeError) as exc:
        raise VariableResolutionError(
            f"Unable to resolve index [{position}] for variable: {variable_name}"
        ) from exc


def resolve_value(value: Any, inputs: dict[str, Any]) -> Any:
    if isinstance(value, str):
        exact_match = VARIABLE_PATTERN.fullmatch(value)
        if exact_match:
            return _resolve_variable(exact_match.group(1), exact_match.group(2), inputs)

        def replace(match: re.Match[str]) -> str:
            return str(_resolve_variable(match.group(1), match.group(2), inputs))

        return VARIABLE_PATTERN.sub(replace, value)

    if isinstance(value, list):
        return [resolve_value(item, inputs) for item in value]

    if isinstance(value, dict):
        return {key: resolve_value(item, inputs) for key, item in value.items()}

    return value


def resolve_workflow_variables(workflow: dict[str, Any], inputs: dict[str, Any]) -> dict[str, Any]:
    resolved = deepcopy(workflow)
    resolved["steps"] = resolve_value(resolved.get("steps", []), inputs)
    return resolved
