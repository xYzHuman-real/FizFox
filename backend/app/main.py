from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .editor import HeuristicProjectEditor
from .generator import HeuristicCodeGenerator
from .models import BuildResult, CreateProjectRequest, EditProjectRequest, Project, ProjectStatus, RuntimeDiagnosticModel
from .planner import HeuristicPlanner
from .repair import BoundedRepairEngine
from .runtime import SafeStaticRuntime
from .verifier import StaticVerifier

app = FastAPI(
    title="FizFox API",
    version="0.1.0",
    description="Backend foundation for the FizFox AI application builder.",
)

projects: dict[str, Project] = {}
planner = HeuristicPlanner()
generator = HeuristicCodeGenerator()
runtime = SafeStaticRuntime()
verifier = StaticVerifier()
editor = HeuristicProjectEditor()
repair_engine = BoundedRepairEngine(verifier, generator, max_attempts=2)


def _build_result(success: bool, diagnostics: list) -> BuildResult:
    return BuildResult(
        success=success,
        diagnostics=[
            RuntimeDiagnosticModel(
                level=item.level,
                code=item.code,
                message=item.message,
                file=item.file,
            )
            for item in diagnostics
        ],
    )


def _run_build(project: Project) -> Project:
    project.status = ProjectStatus.BUILDING
    runtime_result = runtime.build(project.files)
    if not runtime_result.success:
        project.build = _build_result(False, runtime_result.diagnostics)
        project.status = ProjectStatus.FAILED
        return project

    project.status = ProjectStatus.VERIFYING
    verification_result = verifier.verify(project.files)
    diagnostics = runtime_result.diagnostics + verification_result.diagnostics
    project.build = _build_result(verification_result.success, diagnostics)
    project.status = ProjectStatus.READY if verification_result.success else ProjectStatus.FAILED
    return project


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fizfox-api", "version": "0.1.0"}


@app.post("/api/projects", response_model=Project, status_code=201)
def create_project(request: CreateProjectRequest) -> Project:
    project_id = str(uuid4())
    project = Project(id=project_id, prompt=request.prompt, status=ProjectStatus.CREATED)
    projects[project_id] = project
    return project


@app.post("/api/projects/{project_id}/plan", response_model=Project)
def plan_project(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project.status = ProjectStatus.PLANNING
    try:
        project.spec = planner.plan(project.prompt)
        project.status = ProjectStatus.PLANNED
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        raise HTTPException(status_code=500, detail="Unable to create project plan") from exc

    projects[project_id] = project
    return project


@app.post("/api/projects/{project_id}/generate", response_model=Project)
def generate_project(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.spec is None:
        raise HTTPException(status_code=409, detail="Project must be planned before generation")

    project.status = ProjectStatus.GENERATING
    try:
        project.files = generator.generate(project.spec)
        project.build = None
        project.repair_attempts = 0
        project.status = ProjectStatus.GENERATED
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        raise HTTPException(status_code=500, detail="Unable to generate project files") from exc

    projects[project_id] = project
    return project


@app.post("/api/projects/{project_id}/edit", response_model=Project)
def edit_project(project_id: str, request: EditProjectRequest) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.files:
        raise HTTPException(status_code=409, detail="Project must be generated before editing")

    project.status = ProjectStatus.EDITING
    updated = editor.edit(project.files, request.instruction)
    if updated == project.files:
        project.status = ProjectStatus.READY if project.build and project.build.success else ProjectStatus.GENERATED
        projects[project_id] = project
        return project

    project.files = updated
    project.build = None
    project.status = ProjectStatus.GENERATED
    projects[project_id] = project
    return project


@app.post("/api/projects/{project_id}/build", response_model=Project)
def build_project(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.files:
        raise HTTPException(status_code=409, detail="Project must be generated before building")

    project = _run_build(project)
    projects[project_id] = project
    return project


@app.post("/api/projects/{project_id}/verify", response_model=Project)
def verify_project(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.files:
        raise HTTPException(status_code=409, detail="Project must be generated before verification")

    project.status = ProjectStatus.VERIFYING
    result = verifier.verify(project.files)
    project.build = _build_result(result.success, result.diagnostics)
    project.status = ProjectStatus.VERIFIED if result.success else ProjectStatus.FAILED
    projects[project_id] = project
    return project


@app.post("/api/projects/{project_id}/repair", response_model=Project)
def repair_project(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.spec is None or not project.files:
        raise HTTPException(status_code=409, detail="Project must be planned and generated before repair")

    project.status = ProjectStatus.REPAIRING
    result = repair_engine.repair(project.files, project.spec)
    project.files = result.files
    project.repair_attempts += result.attempts
    project.build = _build_result(
        not any(item.level == "error" for item in result.diagnostics),
        result.diagnostics,
    )
    project.status = ProjectStatus.READY if project.build.success else ProjectStatus.FAILED
    projects[project_id] = project
    return project


@app.post("/api/projects/{project_id}/build-and-repair", response_model=Project)
def build_and_repair_project(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.files:
        raise HTTPException(status_code=409, detail="Project must be generated before building")
    if project.spec is None:
        raise HTTPException(status_code=409, detail="Project must be planned before repair")

    project = _run_build(project)
    if project.status != ProjectStatus.FAILED:
        projects[project_id] = project
        return project

    repaired = repair_project(project_id)
    if repaired.status == ProjectStatus.READY:
        return repaired

    final = _run_build(repaired)
    projects[project_id] = final
    return final


@app.get("/api/projects/{project_id}/files", response_model=dict[str, str])
def get_project_files(project_id: str) -> dict[str, str]:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.files


@app.get("/api/projects/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
