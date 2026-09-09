from __future__ import annotations

from .edit_contract import ModelProjectEditor
from .provider_transport import OpenAICompatibleHTTPTransport


def configured_editor() -> ModelProjectEditor | None:
    transport = OpenAICompatibleHTTPTransport()
    return ModelProjectEditor(transport) if transport.config.configured else None
