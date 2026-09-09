from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from .ai_contract import AIRequest, AITransport


@dataclass(frozen=True)
class HttpAIConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "HttpAIConfig":
        return cls(
            base_url=os.getenv("FIZFOX_AI_BASE_URL", "").rstrip("/"),
            api_key=os.getenv("FIZFOX_AI_API_KEY", ""),
            model=os.getenv("FIZFOX_AI_MODEL", ""),
            timeout_seconds=int(os.getenv("FIZFOX_AI_TIMEOUT", "60")),
        )

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)


class OpenAICompatibleHTTPTransport(AITransport):
    """Minimal OpenAI-compatible HTTP transport.

    It sends only prompts and receives text. The response is never executed by
    FizFox; callers must validate structured output before using it.
    """

    def __init__(self, config: HttpAIConfig | None = None) -> None:
        self.config = config or HttpAIConfig.from_env()

    def complete(self, request: AIRequest) -> str:
        if not self.config.configured:
            raise RuntimeError("FizFox AI HTTP provider is not configured")
        payload = json.dumps({
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "temperature": 0.1,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.config.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("FizFox AI provider request failed") from exc
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("FizFox AI provider returned an invalid response") from exc
