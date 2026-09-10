from __future__ import annotations

import os
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .health import system_status
from .models import CreateProjectRequest, EditProjectRequest, Project, ProjectStatus
from .pipeline import BuildPipeline
from .service import FizFoxEngine
from .store import ProjectStore

app = FastAPI(title="FizFox API", version="0.1.0", description="Backend for the FizFox AI application builder.")

_allowed_origins = [origin.strip() for origin in os.getenv("FIZFOX_ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = ProjectStore()
engine = FizFoxEngine()
pipeline = BuildPipeline()


def _get(project_id: str) -> Project:
    project = store.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _save(project: Project) -> Project:
    return store.save(project)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fizfox-api", "version": "0.1.0"}


@app.get("/api/system/status")
def status() -> dict[str, object]:
    return system_status()


@app.post("/api/projects", response_model=Project, status_code=201)
def create_project(request: CreateProjectRequest) -> Project:
    return _save(Project(id=str(uuid4()), prompt=request.prompt, status=ProjectStatus.CREATED))


@app.get("/api/projects", response_model=list[Project])
def list_projects(limit: int = Query(default=50, ge=1, le=100)) -> list[Project]:
    return store.list(limit)


@app.post("/api/projects/{project_id}/plan", response_model=Project)
def plan_project(project_id: str) -> Project:
    project = _get(project_id)
    try:
        pipeline.plan(project)
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        _save(project)
        raise HTTPException(status_code=500, detail="Unable to create project plan") from exc
    return _save(project)


@app.post("/api/projects/{project_id}/generate", response_model=Project)
def generate_project(project_id: str) -> Project:
    project = _get(project_id)
    try:
        pipeline.generate(project)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        _save(project)
        raise HTTPException(status_code=500, detail="Unable to generate project files") from exc
    return _save(project)


@app.post("/api/projects/{project_id}/edit", response_model=Project)
def edit_project(project_id: str, request: EditProjectRequest) -> Project:
    project = _get(project_id)
    try:
        pipeline.edit(project, request.instruction)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        _save(project)
        raise HTTPException(status_code=500, detail="Unable to apply the requested edit") from exc
    return _save(project)


@app.post("/api/projects/{project_id}/build", response_model=Project)
def build_project(project_id: str) -> Project:
    project = _get(project_id)
    try:
        if project.spec is None:
            pipeline.plan(project)
        if not project.files:
            pipeline.generate(project)
        pipeline.verify_and_preview(project)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _save(project)


@app.post("/api/projects/{project_id}/build-and-repair", response_model=Project)
def build_and_repair_project(project_id: str) -> Project:
    project = _get(project_id)
    try:
        if project.spec is None:
            pipeline.plan(project)
        if not project.files:
            pipeline.generate(project)
        pipeline.verify_and_preview(project)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if project.status == ProjectStatus.FAILED:
        project.status = ProjectStatus.REPAIRING
        result = engine.repair.repair(project.files, project.spec)
        project.files = result.files
        project.repair_attempts += result.attempts
        pipeline.verify_and_preview(project)
    return _save(project)


@app.post("/api/projects/{project_id}/execute", response_model=dict)
def execute_project(project_id: str) -> dict:
    project = _get(project_id)
    try:
        result = engine.execute(project)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"success": result.success, "preview_url": result.preview_url, "diagnostics": [d.__dict__ for d in result.diagnostics]}


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: str) -> None:
    _get(project_id)
    store.delete(project_id)


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
