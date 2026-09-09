from __future__ import annotations

import json
from typing import Any

from .generation_contract import ModelCodeGenerator
from .provider_transport import HttpAIConfig, OpenAICompatibleHTTPTransport
from .models import AppSpec


class JsonCodeGenerationTransport:
    """Adapts the shared HTTP model transport to code-generation JSON output."""

    def __init__(self, transport: OpenAICompatibleHTTPTransport | None = None) -> None:
        self.transport = transport or OpenAICompatibleHTTPTransport()

    def complete(self, system: str, user: str) -> str:
        from .ai_contract import AIRequest
        return self.transport.complete(AIRequest(system=system, user=user))


def generation_prompt(spec: AppSpec) -> str:
    return json.dumps(spec.model_dump(), ensure_ascii=False, indent=2)


def configured_generator() -> ModelCodeGenerator | None:
    transport = OpenAICompatibleHTTPTransport()
    if not transport.config.configured:
        return None
    return ModelCodeGenerator(JsonCodeGenerationTransport(transport))
