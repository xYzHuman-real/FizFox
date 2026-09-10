from __future__ import annotations

from .provider_transport import HttpAIConfig
from .sandbox import IsolatedSandbox


def system_status() -> dict[str, object]:
    ai = HttpAIConfig.from_env()
    sandbox = IsolatedSandbox()
    return {
        "service": "fizfox-api",
        "version": "0.1.0",
        "ai": {
            "provider": "gemini",
            "model_configured": bool(ai.model),
            "endpoint_configured": bool(ai.base_url),
            "ready": ai.configured,
        },
        "sandbox": sandbox.isolation_contract(),
    }
