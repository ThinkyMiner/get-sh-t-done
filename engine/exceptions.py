class Flow2APIError(Exception):
    """Base exception for Flow2API runtime errors."""


class WorkflowExecutionError(Flow2APIError):
    """Raised when a workflow cannot complete."""


class SelectorResolutionError(WorkflowExecutionError):
    """Raised when an unsupported selector type is requested."""


class VariableResolutionError(WorkflowExecutionError):
    """Raised when a workflow references a missing input variable."""


class UnsupportedStepError(WorkflowExecutionError):
    """Raised when a workflow step type is not implemented."""

