from __future__ import annotations

import json
from typing import Dict

from .ai_contract import AIRequest, AITransport
from .models import AppSpec
from .provider_transport import OpenAICompatibleHTTPTransport


EDITOR_SYSTEM_PROMPT = """You are FizFox's project editor.
You modify an existing generated web application from a user's natural-language instruction.
Return ONLY valid JSON in this exact shape: {\"files\": {\"relative/path\": \"complete file contents\"}}.
Return complete contents for every file you change. Preserve unrelated existing files and behavior.
Never use absolute paths, ../ traversal, shell commands, secrets, or executable host instructions.
Prefer small, coherent edits. Use the supplied project files as the source of truth.
"""


class AIProjectEditor:
    def __init__(self, transport: AITransport) -> None:
        self.transport = transport

    def edit(self, files: Dict[str, str], instruction: str, spec: AppSpec | None = None) -> Dict[str, str]:
        context = json.dumps({"instruction": instruction, "spec": spec.model_dump() if spec else None, "files": files}, ensure_ascii=False)
        response = self.transport.complete(AIRequest(system=EDITOR_SYSTEM_PROMPT, user=context, temperature=0.1))
        payload = json.loads(response)
        changed = payload.get("files")
        if not isinstance(changed, dict):
            raise ValueError("AI editor returned an invalid file map")
        updated = dict(files)
        for path, content in changed.items():
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("AI editor returned an invalid file entry")
            if path.startswith("/") or ".." in path.split("/"):
                raise ValueError("AI editor returned an unsafe path")
            updated[path] = content
        return updated


def configured_editor() -> AIProjectEditor | None:
    transport = OpenAICompatibleHTTPTransport()
    return AIProjectEditor(transport) if transport.config.configured else None
