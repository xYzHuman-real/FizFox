from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol

from .runtime import RuntimeDiagnostic, RuntimeResult
from .sandbox import IsolatedSandbox, SandboxPolicy


@dataclass(frozen=True)
class ExecutionResult:
    success: bool
    preview_url: str | None
    diagnostics: list[RuntimeDiagnostic]


class ProjectExecutor(Protocol):
    def execute(self, project_id: str, files: Dict[str, str]) -> ExecutionResult:
        """Execute a project through an isolated runtime boundary."""


class ContainerProjectExecutor:
    """Container execution adapter contract.

    The default implementation is intentionally non-executing. It validates
    the project against the sandbox policy and returns a clear diagnostic until
    a trusted container service is configured. No generated code is run on the
    FizFox API host.
    """

    def __init__(self, sandbox: IsolatedSandbox | None = None) -> None:
        self.sandbox = sandbox or IsolatedSandbox(SandboxPolicy())

    def execute(self, project_id: str, files: Dict[str, str]) -> ExecutionResult:
        validation = self.sandbox.validate(files)
        if not validation.success:
            return ExecutionResult(False, None, validation.diagnostics)

        diagnostics = list(validation.diagnostics)
        diagnostics.append(
            RuntimeDiagnostic(
                "info",
                "EXECUTOR_NOT_CONFIGURED",
                "Project passed sandbox validation; a container runner must be configured before executable preview is enabled.",
            )
        )
        return ExecutionResult(False, None, diagnostics)
