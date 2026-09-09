from __future__ import annotations

from .ai_contract import ModelPlanner
from .provider_transport import OpenAICompatibleHTTPTransport


def build_model_planner():
    """Return a model planner when HTTP provider configuration is present."""
    transport = OpenAICompatibleHTTPTransport()
    if not transport.config.configured:
        return None
    return ModelPlanner(transport)
