from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .models import CreateProjectRequest, Project, ProjectStatus

app = FastAPI(
    title="FizFox API",
    version="0.1.0",
    description="Backend foundation for the FizFox AI application builder.",
)

projects: dict[str, Project] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fizfox-api", "version": "0.1.0"}


@app.post("/api/projects", response_model=Project, status_code=201)
def create_project(request: CreateProjectRequest) -> Project:
    project_id = str(uuid4())
    project = Project(
        id=project_id,
        prompt=request.prompt,
        status=ProjectStatus.CREATED,
    )
    projects[project_id] = project
    return project


@app.get("/api/projects/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
