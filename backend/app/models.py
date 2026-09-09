from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    PLANNED = "planned"
    GENERATING = "generating"
    GENERATED = "generated"
    EDITING = "editing"
    BUILDING = "building"
    VERIFYING = "verifying"
    REPAIRING = "repairing"
    VERIFIED = "verified"
    READY = "ready"
    FAILED = "failed"


class PageSpec(BaseModel):
    name: str
    route: str
    purpose: Optional[str] = None


class ComponentSpec(BaseModel):
    name: str
    purpose: Optional[str] = None


class AppSpec(BaseModel):
    name: str
    app_type: str
    pages: List[PageSpec] = Field(default_factory=list)
    components: List[ComponentSpec] = Field(default_factory=list)
    features: List[str] = Field(default_factory=list)
    routes: List[str] = Field(default_factory=list)
    data_requirements: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    styling_direction: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)


class RuntimeDiagnosticModel(BaseModel):
    level: str
    code: str
    message: str
    file: Optional[str] = None


class BuildResult(BaseModel):
    success: bool
    diagnostics: List[RuntimeDiagnosticModel] = Field(default_factory=list)


class CreateProjectRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)


class EditProjectRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=10_000)


class Project(BaseModel):
    id: str
    prompt: str
    status: ProjectStatus
    spec: Optional[AppSpec] = None
    files: Dict[str, str] = Field(default_factory=dict)
    build: Optional[BuildResult] = None
    preview_html: Optional[str] = None
    repair_attempts: int = 0
