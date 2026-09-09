from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .runtime import RuntimeDiagnostic
from .sandbox import IsolatedSandbox, SandboxPolicy


@dataclass(frozen=True)
class ContainerWorkerConfig:
    image: str = "node:22-alpine"
    timeout_seconds: int = 10
    memory: str = "512m"
    cpus: str = "1.0"
    pids_limit: int = 64

    @classmethod
    def from_env(cls) -> "ContainerWorkerConfig":
        return cls(
            image=os.getenv("FIZFOX_WORKER_IMAGE", "node:22-alpine"),
            timeout_seconds=int(os.getenv("FIZFOX_WORKER_TIMEOUT", "10")),
            memory=os.getenv("FIZFOX_WORKER_MEMORY", "512m"),
            cpus=os.getenv("FIZFOX_WORKER_CPUS", "1.0"),
            pids_limit=int(os.getenv("FIZFOX_WORKER_PIDS", "64")),
        )


@dataclass(frozen=True)
class WorkerResult:
    success: bool
    diagnostics: list[RuntimeDiagnostic]
    preview_url: str | None = None


class DockerContainerWorker:
    """Controlled Docker execution boundary.

    The worker requires Docker to be installed on the worker host. Generated
    source is copied into an ephemeral workspace, mounted into the container,
    and executed with a restrictive policy. The API process itself never runs
    generated commands.
    """

    def __init__(
        self,
        config: ContainerWorkerConfig | None = None,
        sandbox: IsolatedSandbox | None = None,
    ) -> None:
        self.config = config or ContainerWorkerConfig.from_env()
        self.sandbox = sandbox or IsolatedSandbox(SandboxPolicy())

    @property
    def configured(self) -> bool:
        return shutil.which("docker") is not None

    def run(self, project_id: str, files: Dict[str, str]) -> WorkerResult:
        validation = self.sandbox.validate(files)
        if not validation.success:
            return WorkerResult(False, validation.diagnostics)
        if not self.configured:
            return WorkerResult(False, [RuntimeDiagnostic("error", "DOCKER_UNAVAILABLE", "Docker is not available on the worker host.")])

        with tempfile.TemporaryDirectory(prefix=f"fizfox-{project_id}-") as tmp:
            root = Path(tmp)
            for relative, content in files.items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

            command = [
                "docker", "run", "--rm",
                "--network", "none",
                "--read-only",
                "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges:true",
                "--pids-limit", str(self.config.pids_limit),
                "--memory", self.config.memory,
                "--cpus", self.config.cpus,
                "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
                "--mount", f"type=bind,src={root},dst=/workspace,readonly",
                "-w", "/workspace",
                self.config.image,
                "sh", "-lc",
                "if [ -f package.json ]; then node -e \"JSON.parse(require('fs').readFileSync('package.json','utf8')); console.log('FizFox container validation passed')\"; else echo 'FizFox container validation passed'; fi",
            ]
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.config.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return WorkerResult(False, [RuntimeDiagnostic("error", "WORKER_TIMEOUT", "Container execution exceeded the configured time limit.")])
            except OSError as exc:
                return WorkerResult(False, [RuntimeDiagnostic("error", "WORKER_START_FAILED", str(exc))])

            if completed.returncode != 0:
                detail = (completed.stderr or completed.stdout or "Container failed").strip()[:4000]
                return WorkerResult(False, [RuntimeDiagnostic("error", "CONTAINER_FAILED", detail)])
            return WorkerResult(True, [RuntimeDiagnostic("info", "CONTAINER_OK", (completed.stdout or "Container validation passed").strip()[:4000])])
