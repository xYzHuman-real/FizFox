from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class ProjectStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    PLANNED = "planned"
    GENERATED = "generated"
    BUILDING = "building"
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


class CreateProjectRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=20_000)


class Project(BaseModel):
    id: str
    prompt: str
    status: ProjectStatus
    spec: Optional[AppSpec] = None
