from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from .ai_contract import AIRequest, AITransport


GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"


@dataclass(frozen=True)
class HttpAIConfig:
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int = 60

    @classmethod
    def from_env(cls) -> "HttpAIConfig":
        provider = os.getenv("FIZFOX_AI_PROVIDER", "gemini").strip().lower()
        try:
            timeout = int(os.getenv("FIZFOX_AI_TIMEOUT", "60"))
        except ValueError:
            timeout = 60
        timeout = max(1, min(timeout, 300))

        if provider == "gemini":
            base_url = os.getenv("GEMINI_BASE_URL", GEMINI_OPENAI_BASE_URL).rstrip("/")
            api_key = os.getenv("GEMINI_API_KEY", os.getenv("FIZFOX_AI_API_KEY", ""))
            model = os.getenv("GEMINI_MODEL", os.getenv("FIZFOX_AI_MODEL", "gemini-3.8-flash"))
        else:
            base_url = os.getenv("FIZFOX_AI_BASE_URL", "").rstrip("/")
            api_key = os.getenv("FIZFOX_AI_API_KEY", "")
            model = os.getenv("FIZFOX_AI_MODEL", "")

        return cls(provider, base_url, api_key, model, timeout)

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)


class OpenAICompatibleHTTPTransport(AITransport):
    """Provider-neutral HTTP transport, with Gemini as the default provider."""

    MAX_RESPONSE_BYTES = 8_000_000

    def __init__(self, config: HttpAIConfig | None = None) -> None:
        self.config = config or HttpAIConfig.from_env()

    def complete(self, request: AIRequest) -> str:
        if not self.config.configured:
            raise RuntimeError("FizFox AI provider is not configured")

        payload = json.dumps({
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.user},
            ],
            "temperature": request.temperature,
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
                raw = response.read(self.MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"FizFox AI provider returned HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("FizFox AI provider request failed") from exc

        if len(raw) > self.MAX_RESPONSE_BYTES:
            raise RuntimeError("FizFox AI provider response is too large")

        try:
            data = json.loads(raw.decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("FizFox AI provider returned an invalid response") from exc

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("FizFox AI provider returned empty content")
        return content
