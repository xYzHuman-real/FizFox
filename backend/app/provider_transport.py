from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

from .ai_contract import AIRequest, AITransport


@dataclass(frozen=True)
class GeminiConfig:
    api_key: str
    model: str = "gemini-3.8-flash"
    timeout_seconds: int = 60
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        try:
            timeout = int(os.getenv("GEMINI_TIMEOUT", "60"))
        except ValueError:
            timeout = 60
        return cls(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
            timeout_seconds=max(1, min(timeout, 300)),
            base_url=os.getenv(
                "GEMINI_API_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta",
            ).rstrip("/"),
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.model and self.base_url)


class GeminiHTTPTransport(AITransport):
    """Server-side Gemini REST transport using the Gemini API directly."""

    MAX_RESPONSE_BYTES = 8_000_000

    def __init__(self, config: GeminiConfig | None = None) -> None:
        self.config = config or GeminiConfig.from_env()

    def complete(self, request: AIRequest) -> str:
        if not self.config.configured:
            raise RuntimeError("FizFox Gemini provider is not configured")

        generation_config: dict[str, object] = {
            "temperature": request.temperature,
        }
        if request.response_mime_type:
            generation_config["responseMimeType"] = request.response_mime_type

        payload = json.dumps({
            "systemInstruction": {"parts": [{"text": request.system}]},
            "contents": [{
                "role": "user",
                "parts": [{"text": request.user}],
            }],
            "generationConfig": generation_config,
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.config.base_url}/models/{self.config.model}:generateContent",
            data=payload,
            headers={
                "x-goog-api-key": self.config.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.config.timeout_seconds) as response:
                raw = response.read(self.MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"Gemini API request failed ({exc.code}): {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise RuntimeError("Gemini API request failed") from exc

        if len(raw) > self.MAX_RESPONSE_BYTES:
            raise RuntimeError("Gemini API response is too large")

        try:
            data = json.loads(raw.decode("utf-8"))
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Gemini API returned an invalid response") from exc

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Gemini API returned empty content")
        return content


# Keep existing internal imports working while FizFox migrates naming.
OpenAICompatibleHTTPTransport = GeminiHTTPTransport
HttpAIConfig = GeminiConfig
