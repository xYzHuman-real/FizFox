from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Protocol

from .runtime import RuntimeDiagnostic


@dataclass
class ExecutionResult:
    success: bool
    preview_url: str | None = None
    diagnostics: list[RuntimeDiagnostic] = field(default_factory=list)


class ProjectExecutor(Protocol):
    def execute(self, files: Dict[str, str]) -> ExecutionResult: ...


class ContainerExecutionBoundary:
    """Explicit contract for a future container worker.

    The API process does not execute generated source. A production worker must
    consume validated files, run them in an isolated container, and return only
    structured status plus an opaque preview reference.
    """

    def execute(self, files: Dict[str, str]) -> ExecutionResult:
        return ExecutionResult(
            success=False,
            diagnostics=[RuntimeDiagnostic(
                "error",
                "EXECUTOR_NOT_CONFIGURED",
                "No isolated container worker is configured. Generated code will not be executed on the API host.",
            )],
        )
