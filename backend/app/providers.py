from __future__ import annotations

import json
import os
from typing import Protocol

from .models import AppSpec, PageSpec, ComponentSpec


class PlannerProvider(Protocol):
    def plan(self, prompt: str) -> AppSpec: ...


class GeneratorProvider(Protocol):
    def generate(self, spec: AppSpec) -> dict[str, str]: ...


class AIProviderConfig:
    """Configuration shared by future model-backed providers."""

    def __init__(self) -> None:
        self.provider = os.getenv("FIZFOX_AI_PROVIDER", "heuristic")
        self.model = os.getenv("FIZFOX_AI_MODEL", "")
        self.api_key = os.getenv("FIZFOX_AI_API_KEY", "")

    @property
    def configured(self) -> bool:
        return bool(self.provider and self.provider != "heuristic" and self.api_key and self.model)


class JsonAppSpecParser:
    """Strict parser for model responses before they enter FizFox's core."""

    @staticmethod
    def parse(payload: str) -> AppSpec:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise ValueError("AI planner response must be a JSON object")
        return AppSpec.model_validate(data)


class ProviderNotConfigured(RuntimeError):
    pass


class OpenAICompatiblePlanner:
    """Placeholder boundary for an OpenAI-compatible model service.

    Network/model invocation is intentionally not performed here yet. This
    adapter makes configuration and response validation explicit so a real
    provider can be added without changing the FizFox engine contract.
    """

    def __init__(self, config: AIProviderConfig | None = None) -> None:
        self.config = config or AIProviderConfig()

    def plan(self, prompt: str) -> AppSpec:
        if not self.config.configured:
            raise ProviderNotConfigured("FizFox AI provider is not configured")
        raise NotImplementedError("Connect the configured model transport here")


class ProviderRegistry:
    def __init__(self, config: AIProviderConfig | None = None) -> None:
        self.config = config or AIProviderConfig()
        self.planner: PlannerProvider | None = None
        self.generator: GeneratorProvider | None = None

    def register_planner(self, planner: PlannerProvider) -> None:
        self.planner = planner

    def register_generator(self, generator: GeneratorProvider) -> None:
        self.generator = generator

    def status(self) -> dict[str, object]:
        return {
            "provider": self.config.provider,
            "model": self.config.model or None,
            "configured": self.config.configured,
            "planner_registered": self.planner is not None,
            "generator_registered": self.generator is not None,
        }
