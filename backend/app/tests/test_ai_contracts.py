from __future__ import annotations

import pytest

from app.ai_contract import AIRequest
from app.ai_editor import AIProjectEditor
from app.generation_contract import ModelCodeGenerator, parse_json_object
from app.models import AppSpec


class FakeTransport:
    def __init__(self, response: str):
        self.response = response
        self.requests: list[AIRequest] = []

    def complete(self, request: AIRequest) -> str:
        self.requests.append(request)
        return self.response


def test_parse_json_object_accepts_json_fence():
    assert parse_json_object('```json\n{"files": {"index.html": "ok"}}\n```')["files"]["index.html"] == "ok"


def test_parse_json_object_rejects_non_object():
    with pytest.raises(ValueError):
        parse_json_object("[]")


def test_code_generator_uses_ai_request_and_rejects_unsafe_paths():
    transport = FakeTransport('{"files":{"../escape.js":"bad"}}')
    spec = AppSpec(name="Test", app_type="web")
    with pytest.raises(ValueError, match="Unsafe generated path"):
        ModelCodeGenerator(transport).generate(spec)
    assert transport.requests
    assert isinstance(transport.requests[0], AIRequest)


def test_ai_editor_updates_only_returned_files():
    transport = FakeTransport('{"files":{"styles.css":"body { color: purple; }"}}')
    editor = AIProjectEditor(transport)
    original = {"index.html": "<html></html>", "styles.css": "body { color: black; }"}
    updated = editor.edit(original, "Make the page purple")
    assert updated["index.html"] == original["index.html"]
    assert updated["styles.css"] == "body { color: purple; }"


def test_ai_editor_rejects_unsafe_paths():
    transport = FakeTransport('{"files":{"/tmp/payload":"bad"}}')
    with pytest.raises(ValueError, match="unsafe path"):
        AIProjectEditor(transport).edit({"index.html": "ok"}, "change it")
