from __future__ import annotations

import json

import pytest

from app.ai_contract import AIRequest, ModelPlanner
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


def sample_spec() -> AppSpec:
    return AppSpec(
        name="Test App",
        app_type="web",
        pages=[],
        components=[],
        features=[],
        routes=[],
        data_requirements=[],
        dependencies=[],
        styling_direction="minimal",
        constraints=[],
    )


def test_parse_json_object_accepts_json_fence():
    assert parse_json_object("```json\n{\"files\": {\"index.html\": \"ok\"}}\n```") == {
        "files": {"index.html": "ok"}
    }


def test_parse_json_object_rejects_invalid_json():
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_json_object("not json")


def test_model_generator_uses_ai_request_and_validates_files():
    transport = FakeTransport(json.dumps({"files": {"index.html": "<html></html>"}}))
    generated = ModelCodeGenerator(transport).generate(sample_spec())
    assert generated.files["index.html"] == "<html></html>"
    assert isinstance(transport.requests[0], AIRequest)


def test_model_generator_rejects_parent_traversal():
    transport = FakeTransport(json.dumps({"files": {"../escape.js": "bad"}}))
    with pytest.raises(ValueError, match="Unsafe generated path"):
        ModelCodeGenerator(transport).generate(sample_spec())


def test_model_planner_uses_structured_request():
    payload = sample_spec().model_dump()
    transport = FakeTransport(json.dumps(payload))
    planned = ModelPlanner(transport).plan("Build a test app")
    assert planned.name == "Test App"
    assert isinstance(transport.requests[0], AIRequest)


def test_ai_editor_preserves_unmodified_files():
    transport = FakeTransport(json.dumps({"files": {"styles.css": "body { color: purple; }"}}))
    files = {"index.html": "<html></html>", "styles.css": "body { color: black; }"}
    updated = AIProjectEditor(transport).edit(files, "Make it purple", sample_spec())
    assert updated["index.html"] == files["index.html"]
    assert updated["styles.css"] == "body { color: purple; }"


def test_ai_editor_rejects_unsafe_path():
    transport = FakeTransport(json.dumps({"files": {"../../secret.txt": "bad"}}))
    with pytest.raises(ValueError, match="unsafe path"):
        AIProjectEditor(transport).edit({"index.html": "ok"}, "change it", sample_spec())
