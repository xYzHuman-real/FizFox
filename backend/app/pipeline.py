from __future__ import annotations

from .edit_provider import configured_editor
from .ai_generation import configured_generator
from .model_provider import configured_planner
from .models import Project, ProjectStatus
from .generator import HeuristicCodeGenerator
from .planner import HeuristicPlanner
from .verifier import StaticVerifier
from .preview import StaticPreviewBuilder
from .editor import HeuristicProjectEditor


class BuildPipeline:
    """Single pipeline entry point for model-backed or deterministic MVP builds."""

    def __init__(self) -> None:
        self.ai_planner = configured_planner()
        self.ai_generator = configured_generator()
        self.ai_editor = configured_editor()
        self.fallback_planner = HeuristicPlanner()
        self.fallback_generator = HeuristicCodeGenerator()
        self.fallback_editor = HeuristicProjectEditor()
        self.verifier = StaticVerifier()
        self.preview = StaticPreviewBuilder()

    def plan(self, project: Project) -> Project:
        project.status = ProjectStatus.PLANNING
        if self.ai_planner:
            project.spec = self.ai_planner.plan(project.prompt)
        else:
            project.spec = self.fallback_planner.plan(project.prompt)
        project.status = ProjectStatus.PLANNED
        return project

    def generate(self, project: Project) -> Project:
        if project.spec is None:
            raise ValueError("Project must be planned before generation")
        project.status = ProjectStatus.GENERATING
        if self.ai_generator:
            generated = self.ai_generator.generate(project.spec)
            project.files = generated.files
        else:
            project.files = self.fallback_generator.generate(project.spec)
        project.status = ProjectStatus.GENERATED
        project.preview_html = None
        project.build = None
        return project

    def edit(self, project: Project, instruction: str) -> Project:
        if not project.files:
            raise ValueError("Project must be generated before editing")
        project.status = ProjectStatus.EDITING
        if self.ai_editor:
            edited = self.ai_editor.edit(project.spec, project.files, instruction)
            project.files = edited.files
        else:
            project.files = self.fallback_editor.edit(project.files, instruction)
        project.status = ProjectStatus.GENERATED
        project.preview_html = None
        project.build = None
        return project

    def verify_and_preview(self, project: Project) -> Project:
        project.status = ProjectStatus.VERIFYING
        result = self.verifier.verify(project.files)
        project.build = result
        if not result.success:
            project.status = ProjectStatus.FAILED
            return project
        project.preview_html = self.preview.build(project.files)
        project.status = ProjectStatus.READY
        return project

    def build(self, project: Project) -> Project:
        self.plan(project)
        self.generate(project)
        return self.verify_and_preview(project)
