from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, HTTPException

from .generator import HeuristicCodeGenerator
from .models import CreateProjectRequest, Project, ProjectStatus
from .planner import HeuristicPlanner

app = FastAPI(
    title="FizFox API",
    version="0.1.0",
    description="Backend foundation for the FizFox AI application builder.",
)

projects: dict[str, Project] = {}
planner = HeuristicPlanner()
generator = HeuristicCodeGenerator()


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
        project.status = ProjectStatus.GENERATED
    except Exception as exc:
        project.status = ProjectStatus.FAILED
        raise HTTPException(status_code=500, detail="Unable to generate project files") from exc

    projects[project_id] = project
    return project


@app.get("/api/projects/{project_id}", response_model=Project)
def get_project(project_id: str) -> Project:
    project = projects.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
