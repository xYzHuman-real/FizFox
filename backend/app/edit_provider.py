from __future__ import annotations

from .ai_editor import AIProjectEditor
from .provider_transport import OpenAICompatibleHTTPTransport


def configured_editor() -> AIProjectEditor | None:
    transport = OpenAICompatibleHTTPTransport()
    return AIProjectEditor(transport) if transport.config.configured else None
