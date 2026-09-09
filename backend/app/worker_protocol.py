from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol

from .execution_contract import ExecutionResult
from .sandbox import SandboxPolicy


@dataclass(frozen=True)
class WorkerRequest:
    project_id: str
    files: Dict[str, str]
    policy: SandboxPolicy


class IsolatedWorker(Protocol):
    def run(self, request: WorkerRequest) -> ExecutionResult: ...


class DockerWorkerBoundary:
    """Protocol boundary for a separately hosted container worker.

    The API server passes validated project files to a worker process/service.
    This class intentionally contains no host-side subprocess execution.
    """

    def __init__(self, image: str = "fizfox-runner:latest") -> None:
        self.image = image

    def request_spec(self, project_id: str, files: Dict[str, str], policy: SandboxPolicy) -> WorkerRequest:
        return WorkerRequest(project_id=project_id, files=files, policy=policy)
