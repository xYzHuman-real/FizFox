from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

from .ai_contract import AIRequest
from .models import AppSpec


@dataclass(frozen=True)
class GeneratedProject:
    files: dict[str, str]


class CodeGenerationProvider(Protocol):
    def generate(self, spec: AppSpec) -> GeneratedProject: ...


def parse_json_object(response: str) -> dict:
    """Parse strict JSON while tolerating a single markdown code fence."""
    text = response.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("AI generator returned invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("AI generator response must be a JSON object")
    return payload


GENERATOR_SYSTEM_PROMPT = """You are the FizFox code generator. Generate a complete application from the supplied AppSpec. Return JSON only in the form {\"files\": {\"relative/path\": \"complete UTF-8 source\"}}. Never include absolute paths, parent traversal, secrets, host commands, or instructions to run code on the host. Keep generated output within the supplied application requirements."""


class ModelCodeGenerator:
    """Model-backed code-generation boundary with strict output validation."""

    def __init__(self, transport) -> None:
        self.transport = transport

    def generate(self, spec: AppSpec) -> GeneratedProject:
        response = self.transport.complete(
            AIRequest(system=GENERATOR_SYSTEM_PROMPT, user=spec.model_dump_json(), temperature=0.1)
        )
        data = parse_json_object(response)
        files = data.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError("AI generator response must contain a non-empty files object")
        if len(files) > 100:
            raise ValueError("AI generator returned too many files")
        clean: dict[str, str] = {}
        total_size = 0
        for path, content in files.items():
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("Generated files must map string paths to string contents")
            normalized = path.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/"):
                raise ValueError(f"Unsafe generated path: {path}")
            if len(content.encode("utf-8")) > 512_000:
                raise ValueError(f"Generated file is too large: {path}")
            total_size += len(content.encode("utf-8"))
            if total_size > 5_000_000:
                raise ValueError("AI generator returned too much source content")
            clean[normalized] = content
        return GeneratedProject(clean)
