from __future__ import annotations

from .providers import AIProviderConfig
from .sandbox import IsolatedSandbox


def system_status() -> dict[str, object]:
    ai = AIProviderConfig()
    sandbox = IsolatedSandbox()
    return {
        "service": "fizfox-api",
        "version": "0.1.0",
        "ai": {
            "provider": ai.provider,
            "model_configured": bool(ai.model),
            "ready": ai.configured,
        },
        "sandbox": sandbox.isolation_contract(),
    }
