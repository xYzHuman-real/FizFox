from __future__ import annotations

import json
import re
from typing import Protocol

from .models import AppSpec


class PlannerProvider(Protocol):
    def plan(self, prompt: str) -> AppSpec: ...


class GeneratorProvider(Protocol):
    def generate(self, spec: AppSpec) -> dict[str, str]: ...


class AIProviderConfig:
    """Provider metadata shared with the model transport."""

    def __init__(self) -> None:
        import os
        self.provider = os.getenv("FIZFOX_AI_PROVIDER", "openai-compatible")
        self.model = os.getenv("FIZFOX_AI_MODEL", "")
        self.api_key = os.getenv("FIZFOX_AI_API_KEY", "")
        self.base_url = os.getenv("FIZFOX_AI_BASE_URL", "").rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)


def parse_json_object(payload: str, source: str = "AI") -> dict:
    """Parse one JSON object, allowing a single markdown JSON fence."""
    text = payload.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source} returned invalid JSON") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{source} response must be a JSON object")
    return data


class JsonAppSpecParser:
    """Parse and validate planner output before it enters FizFox's core."""

    @staticmethod
    def parse(payload: str) -> AppSpec:
        data = parse_json_object(payload, "AI planner")
        try:
            return AppSpec.model_validate(data)
        except Exception as exc:
            raise ValueError("AI planner returned an invalid AppSpec") from exc


class ProviderNotConfigured(RuntimeError):
    pass


class OpenAICompatiblePlanner:
    """Compatibility boundary for the shared model transport."""

    def __init__(self, config: AIProviderConfig | None = None) -> None:
        self.config = config or AIProviderConfig()

    def plan(self, prompt: str) -> AppSpec:
        if not self.config.configured:
            raise ProviderNotConfigured("FizFox AI provider is not configured")
        raise NotImplementedError("Use the configured model transport through ModelPlanner")


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
