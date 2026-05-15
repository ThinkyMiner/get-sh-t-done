from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from .exceptions import VariableResolutionError

VARIABLE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


def resolve_value(value: Any, inputs: dict[str, Any]) -> Any:
    if isinstance(value, str):
        exact_match = VARIABLE_PATTERN.fullmatch(value)
        if exact_match:
            variable_name = exact_match.group(1)
            if variable_name not in inputs:
                raise VariableResolutionError(f"Missing input variable: {variable_name}")
            return inputs[variable_name]

        def replace(match: re.Match[str]) -> str:
            variable_name = match.group(1)
            if variable_name not in inputs:
                raise VariableResolutionError(f"Missing input variable: {variable_name}")
            return str(inputs[variable_name])

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

