from __future__ import annotations

import json
from typing import Dict

from .ai_contract import AIRequest, AITransport
from .generation_contract import parse_json_object
from .models import AppSpec


EDITOR_SYSTEM_PROMPT = """You are FizFox's project editor. Modify an existing application from the user's instruction. Return ONLY JSON in the form {\"files\": {\"relative/path\": \"complete UTF-8 source\"}}. Return complete contents for every changed file. Preserve unrelated files and existing functionality. Never use absolute paths, parent traversal, secrets, host commands, or executable host instructions. Use only safe relative paths."""


class AIProjectEditor:
    """Provider-backed editor. Model output is treated strictly as untrusted data."""

    MAX_CHANGED_FILES = 20
    MAX_FILE_SIZE = 512_000
    MAX_TOTAL_SIZE = 5_000_000
    MAX_CONTEXT_SIZE = 6_000_000

    def __init__(self, transport: AITransport) -> None:
        self.transport = transport

    def edit(self, spec: AppSpec | None, files: Dict[str, str], instruction: str):
        from .edit_contract import EditedProject
        if not instruction.strip():
            raise ValueError("Edit instruction cannot be empty")
        context = json.dumps({"spec": spec.model_dump() if spec else None, "files": files, "instruction": instruction}, ensure_ascii=False)
        if len(context.encode("utf-8")) > self.MAX_CONTEXT_SIZE:
            raise ValueError("Project is too large for the AI editor")
        response = self.transport.complete(AIRequest(EDITOR_SYSTEM_PROMPT, context, 0.1))
        payload = parse_json_object(response, "AI editor")
        changed = payload.get("files")
        if not isinstance(changed, dict) or not changed:
            raise ValueError("AI editor must return a non-empty files object")
        if len(changed) > self.MAX_CHANGED_FILES:
            raise ValueError("AI editor returned too many changed files")
        updated = dict(files)
        total_size = sum(len(value.encode("utf-8")) for value in updated.values())
        for path, content in changed.items():
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("AI editor returned an invalid file entry")
            normalized = path.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/"):
                raise ValueError("AI editor returned an unsafe path")
            size = len(content.encode("utf-8"))
            if size > self.MAX_FILE_SIZE:
                raise ValueError(f"AI editor returned a file that is too large: {normalized}")
            total_size += size - len(updated.get(normalized, "").encode("utf-8"))
            if total_size > self.MAX_TOTAL_SIZE:
                raise ValueError("AI editor returned too much source content")
            updated[normalized] = content
        return EditedProject(updated)


def configured_editor() -> AIProjectEditor | None:
    from .provider_transport import OpenAICompatibleHTTPTransport
    transport = OpenAICompatibleHTTPTransport()
    return AIProjectEditor(transport) if transport.config.configured else None
