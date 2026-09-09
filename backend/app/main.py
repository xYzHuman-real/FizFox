from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .models import CreateProjectRequest, EditProjectRequest, Project, ProjectStatus
from .service import FizFoxEngine

app = FastAPI(
    title="FizFox API",
    version="0.1.0",
    description="Backend for the FizFox AI application builder.",
)

projects: dict[str, Project] = {}
engine = FizFoxEngine()


def _get(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fizfox-api", "version": "0.1.0"}


@app.post("/api/projects", response_model=Project, status_code=201)
def create_project(request: CreateProjectRequest) -> Project:
    project = Project(id=str(uuid4()), prompt=request.prompt, status=ProjectStatus.CREATED)
    projects[project.id] = project
    return project


@app.post("/api/projects/{project_id}/plan", response_model=Project)
def plan_project(project_id: str) -> Project:
    project = _get(project_id)
    try:
        engine.plan(project)
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        raise HTTPException(status_code=500, detail="Unable to create project plan") from exc
    return project


@app.post("/api/projects/{project_id}/generate", response_model=Project)
def generate_project(project_id: str) -> Project:
    project = _get(project_id)
    try:
        engine.generate(project)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        raise HTTPException(status_code=500, detail="Unable to generate project files") from exc
    return project


@app.post("/api/projects/{project_id}/edit", response_model=Project)
def edit_project(project_id: str, request: EditProjectRequest) -> Project:
    project = _get(project_id)
    try:
        engine.edit(project, request.instruction)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return project


@app.post("/api/projects/{project_id}/build", response_model=Project)
def build_project(project_id: str) -> Project:
    project = _get(project_id)
    try:
        engine.build_and_verify(project)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return project


@app.post("/api/projects/{project_id}/build-and-repair", response_model=Project)
def build_and_repair_project(project_id: str) -> Project:
    project = _get(project_id)
    if not project.files:
        raise HTTPException(status_code=409, detail="Project must be generated before building")
    if project.spec is None:
        raise HTTPException(status_code=409, detail="Project must be planned before repair")

    engine.build_and_verify(project)
    if project.status == ProjectStatus.FAILED:
        project.status = ProjectStatus.REPAIRING
        result = engine.repair.repair(project.files, project.spec)
        project.files = result.files
        project.repair_attempts += result.attempts
        engine.build_and_verify(project)
    return project


@app.post("/api/projects/{project_id}/execute", response_model=dict)
def execute_project(project_id: str) -> dict:
    project = _get(project_id)
    try:
        result = engine.execute(project)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "success": result.success,
        "preview_url": result.preview_url,
        "diagnostics": [d.__dict__ for d in result.diagnostics],
    }


@app.get("/api/projects/{project_id}/files", response_model=dict[str, str])
def get_project_files(project_id: str) -> dict[str, str]:
    return _get(project_id).files


@app.get("/api/projects/{project_id}/preview", response_model=dict[str, str])
def get_project_preview(project_id: str) -> dict[str, str]:
    project = _get(project_id)
    if not project.preview_html:
        raise HTTPException(status_code=409, detail="Project must pass build and verification before preview")
    return {"html": project.preview_html}


@app.get("/api/projects/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    return _get(project_id)
