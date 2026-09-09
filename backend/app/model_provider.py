from __future__ import annotations

from .ai_contract import ModelPlanner
from .provider_transport import OpenAICompatibleHTTPTransport


def configured_planner() -> ModelPlanner | None:
    transport = OpenAICompatibleHTTPTransport()
    return ModelPlanner(transport) if transport.config.configured else None
