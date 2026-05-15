from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StepLog:
    step_id: str
    step_type: str
    status: str
    message: str
    screenshot_path: str | None = None
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionResult:
    execution_id: str
    status: str
    outputs: dict[str, Any] = field(default_factory=dict)
    logs: list[StepLog] = field(default_factory=list)
    error_message: str | None = None
    duration_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "status": self.status,
            "outputs": self.outputs,
            "logs": [log.to_dict() for log in self.logs],
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
        }

