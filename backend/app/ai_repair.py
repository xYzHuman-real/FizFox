from __future__ import annotations

import json

from .ai_contract import AIRequest, AITransport
from .ai_json import parse_json_object
from .models import AppSpec


REPAIR_SYSTEM_PROMPT = """You are FizFox's repair agent. Fix a generated application using the supplied files and verification diagnostics. Return ONLY JSON in the form {\"files\": {\"relative/path\": \"complete updated UTF-8 source\"}}. Change only files needed to resolve the reported errors. Preserve unrelated functionality. Never use absolute paths, parent traversal, secrets, shell commands, or host-execution instructions."""


class AIProjectRepairer:
    def __init__(self, transport: AITransport) -> None:
        self.transport = transport

    def repair(self, files: dict[str, str], diagnostics: list[object], spec: AppSpec) -> dict[str, str]:
        payload = {
            "spec": spec.model_dump(),
            "files": files,
            "diagnostics": [getattr(item, "__dict__", str(item)) for item in diagnostics],
        }
        response = self.transport.complete(
            AIRequest(REPAIR_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False), temperature=0.0)
        )
        data = parse_json_object(response, label="AI repairer")
        changed = data.get("files")
        if not isinstance(changed, dict) or not changed:
            raise ValueError("AI repairer must return a non-empty files object")
        if len(changed) > 20:
            raise ValueError("AI repairer returned too many changed files")

        updated = dict(files)
        total_size = sum(len(content.encode("utf-8")) for content in updated.values())
        for path, content in changed.items():
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("AI repairer returned an invalid file entry")
            normalized = path.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/"):
                raise ValueError("AI repairer returned an unsafe path")
            size = len(content.encode("utf-8"))
            if size > 512_000:
                raise ValueError(f"AI repairer returned a file that is too large: {normalized}")
            total_size += size - len(updated.get(normalized, "").encode("utf-8"))
            if total_size > 5_000_000:
                raise ValueError("AI repairer returned too much source content")
            updated[normalized] = content
        return updated


def configured_repairer() -> AIProjectRepairer | None:
    from .provider_transport import OpenAICompatibleHTTPTransport

    transport = OpenAICompatibleHTTPTransport()
    return AIProjectRepairer(transport) if transport.config.configured else None
