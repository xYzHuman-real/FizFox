from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models import AppSpec


@dataclass(frozen=True)
class GeneratedProject:
    files: dict[str, str]


class CodeGenerationProvider(Protocol):
    def generate(self, spec: AppSpec) -> GeneratedProject: ...


GENERATOR_SYSTEM_PROMPT = """You are the FizFox code generator. Generate a complete application from the supplied AppSpec. Return a JSON object with a 'files' object mapping safe relative file paths to UTF-8 source strings. Never include absolute paths, parent traversal, secrets, or instructions to run code on the host."""


class ModelCodeGenerator:
    """Model-backed code-generation boundary.

    The transport is injected so network credentials and provider-specific
    SDKs never leak into the core generation pipeline.
    """

    def __init__(self, transport) -> None:
        self.transport = transport

    def generate(self, spec: AppSpec) -> GeneratedProject:
        import json
        response = self.transport.complete({
            "system": GENERATOR_SYSTEM_PROMPT,
            "user": spec.model_dump_json(),
        })
        data = json.loads(response)
        files = data.get("files")
        if not isinstance(files, dict) or not files:
            raise ValueError("AI generator response must contain a non-empty files object")
        clean: dict[str, str] = {}
        for path, content in files.items():
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("Generated files must map string paths to string contents")
            normalized = path.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/"):
                raise ValueError(f"Unsafe generated path: {path}")
            clean[normalized] = content
        return GeneratedProject(clean)
