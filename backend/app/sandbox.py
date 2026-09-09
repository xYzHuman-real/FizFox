from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol

from .runtime import RuntimeDiagnostic, RuntimeResult, SafeStaticRuntime


@dataclass(frozen=True)
class SandboxPolicy:
    max_files: int = 100
    max_file_size: int = 512_000
    max_total_size: int = 5_000_000
    network_enabled: bool = False
    allow_host_filesystem: bool = False
    max_execution_seconds: int = 10


class Sandbox(Protocol):
    def validate(self, files: Dict[str, str]) -> RuntimeResult:
        """Validate files against the sandbox policy before execution."""


class IsolatedSandbox:
    """Security policy boundary for the future executable runtime.

    This MVP does not execute untrusted code. It validates resource limits and
    explicitly records the isolation policy that a container runtime must obey.
    """

    def __init__(self, policy: SandboxPolicy | None = None) -> None:
        self.policy = policy or SandboxPolicy()
        self.static_runtime = SafeStaticRuntime()

    def validate(self, files: Dict[str, str]) -> RuntimeResult:
        result = self.static_runtime.build(files)
        diagnostics: List[RuntimeDiagnostic] = list(result.diagnostics)

        total_size = sum(len(content.encode("utf-8")) for content in files.values())
        if total_size > self.policy.max_total_size:
            diagnostics.append(RuntimeDiagnostic("error", "TOTAL_SIZE_LIMIT", "Project exceeds the sandbox total-size limit."))

        if self.policy.network_enabled:
            diagnostics.append(RuntimeDiagnostic("warning", "NETWORK_ENABLED", "Network access must be explicitly isolated and allowlisted."))

        return RuntimeResult(
            success=not any(item.level == "error" for item in diagnostics),
            diagnostics=diagnostics,
        )

    def isolation_contract(self) -> dict[str, object]:
        return {
            "network_enabled": self.policy.network_enabled,
            "allow_host_filesystem": self.policy.allow_host_filesystem,
            "max_execution_seconds": self.policy.max_execution_seconds,
            "max_files": self.policy.max_files,
            "max_file_size": self.policy.max_file_size,
            "max_total_size": self.policy.max_total_size,
        }
