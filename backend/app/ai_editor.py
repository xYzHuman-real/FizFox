from __future__ import annotations

import json
from typing import Dict

from .ai_contract import AIRequest, AITransport
from .generation_contract import parse_json_object
from .models import AppSpec
from .provider_transport import OpenAICompatibleHTTPTransport


EDITOR_SYSTEM_PROMPT = """You are FizFox's project editor.
Modify an existing generated web application from the user's instruction.
Return ONLY JSON: {\"files\": {\"relative/path\": \"complete updated UTF-8 source\"}}.
Return complete contents for every changed file. Preserve unrelated functionality.
Never use absolute paths, parent traversal, secrets, shell commands, or host-execution instructions.
Prefer the smallest coherent change that satisfies the request.
"""


class AIProjectEditor:
    def __init__(self, transport: AITransport) -> None:
        self.transport = transport

    def edit(self, files: Dict[str, str], instruction: str, spec: AppSpec | None = None) -> Dict[str, str]:
        if not instruction.strip():
            raise ValueError("Edit instruction cannot be empty")
        context = json.dumps(
            {"instruction": instruction, "spec": spec.model_dump() if spec else None, "files": files},
            ensure_ascii=False,
        )
        if len(context.encode("utf-8")) > 6_000_000:
            raise ValueError("Project is too large for the AI editor")
        response = self.transport.complete(AIRequest(system=EDITOR_SYSTEM_PROMPT, user=context, temperature=0.1))
        payload = parse_json_object(response)
        changed = payload.get("files")
        if not isinstance(changed, dict) or not changed:
            raise ValueError("AI editor must return a non-empty files object")
        if len(changed) > 20:
            raise ValueError("AI editor returned too many changed files")
        updated = dict(files)
        total_size = sum(len(content.encode("utf-8")) for content in updated.values())
        for path, content in changed.items():
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("AI editor returned an invalid file entry")
            normalized = path.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/"):
                raise ValueError("AI editor returned an unsafe path")
            size = len(content.encode("utf-8"))
            if size > 512_000:
                raise ValueError(f"AI editor returned a file that is too large: {normalized}")
            total_size += size - len(updated.get(normalized, "").encode("utf-8"))
            if total_size > 5_000_000:
                raise ValueError("AI editor returned too much source content")
            updated[normalized] = content
        return updated


def configured_editor() -> AIProjectEditor | None:
    transport = OpenAICompatibleHTTPTransport()
    return AIProjectEditor(transport) if transport.config.configured else None
