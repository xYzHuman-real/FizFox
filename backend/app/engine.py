from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .editor import HeuristicProjectEditor
from .generator import HeuristicCodeGenerator
from .models import AppSpec, Project, ProjectStatus
from .planner import HeuristicPlanner
from .preview import StaticPreviewBuilder
from .repair import BoundedRepairEngine
from .runtime import SafeStaticRuntime
from .verifier import StaticVerifier


@dataclass
class EngineResult:
    project: Project
    message: str = ""


class FizFoxEngine:
    """Provider-agnostic application-building orchestration layer."""

    def __init__(self) -> None:
        self.planner = HeuristicPlanner()
        self.generator = HeuristicCodeGenerator()
        self.editor = HeuristicProjectEditor()
        self.runtime = SafeStaticRuntime()
        self.verifier = StaticVerifier()
        self.preview = StaticPreviewBuilder()
        self.repair = BoundedRepairEngine(self.verifier, self.generator, max_attempts=2)

    def plan(self, project: Project) -> EngineResult:
        project.status = ProjectStatus.PLANNING
        project.spec = self.planner.plan(project.prompt)
        project.status = ProjectStatus.PLANNED
        return EngineResult(project, "Project plan created.")

    def generate(self, project: Project) -> EngineResult:
        if project.spec is None:
            raise ValueError("Project must be planned before generation")
        project.status = ProjectStatus.GENERATING
        project.files = self.generator.generate(project.spec)
        project.status = ProjectStatus.GENERATED
        project.build = None
        project.preview_html = None
        return EngineResult(project, "Project files generated.")

    def edit(self, project: Project, instruction: str) -> EngineResult:
        if not project.files:
            raise ValueError("Project must be generated before editing")
        project.status = ProjectStatus.EDITING
        project.files = self.editor.edit(project.files, instruction)
        project.build = None
        project.preview_html = None
        project.status = ProjectStatus.GENERATED
        return EngineResult(project, "Project updated.")

    def build_verify(self, project: Project) -> EngineResult:
        if not project.files:
            raise ValueError("Project must be generated before building")
        project.status = ProjectStatus.BUILDING
        runtime_result = self.runtime.build(project.files)
        if not runtime_result.success:
            project.build = self._result(False, runtime_result.diagnostics)
            project.status = ProjectStatus.FAILED
            return EngineResult(project, "Runtime validation failed.")
        project.status = ProjectStatus.VERIFYING
        verification = self.verifier.verify(project.files)
        project.build = self._result(verification.success, verification.diagnostics)
        project.status = ProjectStatus.READY if verification.success else ProjectStatus.FAILED
        if verification.success:
            project.preview_html = self.preview.build(project.files)
        return EngineResult(project, "Project verified." if verification.success else "Verification failed.")

    def build_and_repair(self, project: Project) -> EngineResult:
        result = self.build_verify(project)
        if project.status != ProjectStatus.FAILED or project.spec is None:
            return result
        project.status = ProjectStatus.REPAIRING
        repaired = self.repair.repair(project.files, project.spec)
        project.files = repaired.files
        project.repair_attempts += repaired.attempts
        project.status = ProjectStatus.GENERATED
        return self.build_verify(project)

    @staticmethod
    def _result(success: bool, diagnostics: list) -> object:
        from .models import BuildResult, RuntimeDiagnosticModel
        return BuildResult(
            success=success,
            diagnostics=[RuntimeDiagnosticModel(level=d.level, code=d.code, message=d.message, file=d.file) for d in diagnostics],
        )
