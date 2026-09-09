from __future__ import annotations

from .generation_contract import ModelCodeGenerator
from .provider_transport import OpenAICompatibleHTTPTransport


def configured_generator() -> ModelCodeGenerator | None:
    transport = OpenAICompatibleHTTPTransport()
    if not transport.config.configured:
        return None
    return ModelCodeGenerator(transport)
