from __future__ import annotations

from .editor import HeuristicProjectEditor
from .executor import ContainerProjectExecutor
from .generator import HeuristicCodeGenerator
from .models import Project, ProjectStatus
from .planner import HeuristicPlanner
from .preview import StaticPreviewBuilder
from .repair import BoundedRepairEngine
from .runtime import SafeStaticRuntime
from .verifier import StaticVerifier


class FizFoxEngine:
    """Application-builder orchestration kept separate from HTTP routes."""

    def __init__(self) -> None:
        self.planner = HeuristicPlanner()
        self.generator = HeuristicCodeGenerator()
        self.runtime = SafeStaticRuntime()
        self.verifier = StaticVerifier()
        self.editor = HeuristicProjectEditor()
        self.preview = StaticPreviewBuilder()
        self.executor = ContainerProjectExecutor()
        self.repair = BoundedRepairEngine(self.verifier, self.generator, max_attempts=2)

    def plan(self, project: Project) -> Project:
        project.status = ProjectStatus.PLANNING
        project.spec = self.planner.plan(project.prompt)
        project.status = ProjectStatus.PLANNED
        return project

    def generate(self, project: Project) -> Project:
        if project.spec is None:
            raise ValueError("Project must be planned before generation")
        project.status = ProjectStatus.GENERATING
        project.files = self.generator.generate(project.spec)
        project.status = ProjectStatus.GENERATED
        project.preview_html = None
        project.build = None
        return project

    def edit(self, project: Project, instruction: str) -> Project:
        if not project.files:
            raise ValueError("Project must be generated before editing")
        project.status = ProjectStatus.EDITING
        project.files = self.editor.edit(project.files, instruction)
        project.status = ProjectStatus.GENERATED
        project.preview_html = None
        project.build = None
        return project

    def build_and_verify(self, project: Project) -> Project:
        if not project.files:
            raise ValueError("Project must be generated before building")
        project.status = ProjectStatus.BUILDING
        runtime_result = self.runtime.build(project.files)
        if not runtime_result.success:
            project.status = ProjectStatus.FAILED
            return project
        project.status = ProjectStatus.VERIFYING
        verification = self.verifier.verify(project.files)
        project.status = ProjectStatus.READY if verification.success else ProjectStatus.FAILED
        if verification.success:
            project.preview_html = self.preview.build(project.files)
        return project

    def execute(self, project: Project):
        if not project.files:
            raise ValueError("Project must be generated before execution")
        return self.executor.execute(project.id, project.files)
