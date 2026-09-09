from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from .models import AppSpec


@dataclass(frozen=True)
class EditedProject:
    files: dict[str, str]


class EditProvider(Protocol):
    def edit(self, spec: AppSpec | None, files: dict[str, str], instruction: str) -> EditedProject: ...


EDIT_SYSTEM_PROMPT = """You are the FizFox project editor. Modify an existing application in response to the user's instruction. Return JSON only in the form {\"files\": {\"relative/path\": \"complete updated UTF-8 source\"}}. Preserve existing functionality unless the instruction asks to change it. Return complete file contents for every changed file. Use only safe relative paths; never use absolute paths, parent traversal, secrets, host commands, or executable instructions. Do not modify files unnecessarily."""


class ModelProjectEditor:
    def __init__(self, transport) -> None:
        self.transport = transport

    def edit(self, spec: AppSpec | None, files: dict[str, str], instruction: str) -> EditedProject:
        from .ai_contract import AIRequest

        payload = {
            "spec": spec.model_dump() if spec else None,
            "files": files,
            "instruction": instruction,
        }
        response = self.transport.complete(AIRequest(EDIT_SYSTEM_PROMPT, json.dumps(payload, ensure_ascii=False)))
        data = json.loads(response)
        changed = data.get("files")
        if not isinstance(changed, dict) or not changed:
            raise ValueError("AI editor response must contain a non-empty files object")

        updated = dict(files)
        for path, content in changed.items():
            if not isinstance(path, str) or not isinstance(content, str):
                raise ValueError("Edited files must map string paths to string contents")
            normalized = path.replace("\\", "/")
            if normalized.startswith("/") or ".." in normalized.split("/"):
                raise ValueError(f"Unsafe edited path: {path}")
            updated[normalized] = content
        return EditedProject(updated)
