from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import AppSpec


@dataclass(frozen=True)
class AIRequest:
    system: str
    user: str
    temperature: float = 0.1


class AITransport(Protocol):
    def complete(self, request: AIRequest) -> str:
        """Return model text. Implementations must never execute the response."""


class AIPlanner(Protocol):
    def plan(self, prompt: str) -> AppSpec: ...


PLANNER_SYSTEM_PROMPT = """You are the FizFox application planner. Convert a user's app idea into a strict JSON AppSpec. Return JSON only. Do not output executable code. Include name, app_type, pages, components, features, routes, data_requirements, dependencies, styling_direction, and constraints."""


class ModelPlanner:
    """Model-backed planner boundary with structured-output validation."""

    def __init__(self, transport: AITransport) -> None:
        self.transport = transport

    def plan(self, prompt: str) -> AppSpec:
        from .providers import JsonAppSpecParser
        response = self.transport.complete(
            AIRequest(system=PLANNER_SYSTEM_PROMPT, user=prompt, temperature=0.1)
        )
        return JsonAppSpecParser.parse(response)
