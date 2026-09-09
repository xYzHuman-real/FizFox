from __future__ import annotations

from typing import Dict

from .container_worker import DockerContainerWorker
from .executor import ExecutionResult


class WorkerBackedExecutor:
    """Project executor that delegates generated projects to the container worker."""

    def __init__(self, worker: DockerContainerWorker | None = None) -> None:
        self.worker = worker or DockerContainerWorker()

    def execute(self, project_id: str, files: Dict[str, str]) -> ExecutionResult:
        result = self.worker.run(project_id, files)
        return ExecutionResult(result.success, result.preview_url, result.diagnostics)
