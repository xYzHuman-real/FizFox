import json

import pytest

from app.ai_contract import AIRequest, ModelPlanner
from app.ai_editor import AIProjectEditor
from app.editor import HeuristicProjectEditor
from app.generation_contract import ModelCodeGenerator, parse_json_object
from app.generator import HeuristicCodeGenerator
from app.planner import HeuristicPlanner
from app.preview import StaticPreviewBuilder
from app.sandbox import IsolatedSandbox
from app.verifier import StaticVerifier


class FakeTransport:
    def __init__(self, response: str):
        self.response = response
        self.requests: list[AIRequest] = []

    def complete(self, request: AIRequest) -> str:
        self.requests.append(request)
        return self.response


def planner_payload(name="Demo"):
    return json.dumps({
        "name": name,
        "app_type": "web",
        "pages": [],
        "components": [],
        "features": [],
        "routes": [],
        "data_requirements": [],
        "dependencies": [],
        "styling_direction": "minimal",
        "constraints": [],
    })


def test_pipeline_plan_generate_verify_preview():
    spec = HeuristicPlanner().plan("Build a restaurant website with a menu and contact form")
    files = HeuristicCodeGenerator().generate(spec)
    assert "index.html" in files
    assert StaticVerifier().verify(files).success
    preview = StaticPreviewBuilder().build(files)
    assert "<html" in preview
    assert "<script" not in preview.lower()


def test_sandbox_rejects_unsafe_paths():
    result = IsolatedSandbox().validate({"../escape.js": "alert(1)"})
    assert not result.success
    assert any(d.code == "UNSAFE_PATH" for d in result.diagnostics)


def test_editor_preserves_project_files():
    spec = HeuristicPlanner().plan("Build a portfolio website")
    files = HeuristicCodeGenerator().generate(spec)
    updated = HeuristicProjectEditor().edit(files, "Make the homepage darker and add a hero section")
    assert updated["index.html"] != files["index.html"]
    assert updated["styles.css"] != files["styles.css"]


def test_parse_json_object_accepts_json_fence():
    assert parse_json_object("```json\n{\"files\": {}}\n```") == {"files": {}}


def test_parse_json_object_rejects_invalid_json():
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_json_object("not json")


def test_model_planner_uses_ai_request_and_validates_app_spec():
    transport = FakeTransport(planner_payload())
    spec = ModelPlanner(transport).plan("Build Demo")
    assert spec.name == "Demo"
    assert isinstance(transport.requests[0], AIRequest)


def test_model_generator_rejects_unsafe_path():
    spec = ModelPlanner(FakeTransport(planner_payload())).plan("Build Demo")
    transport = FakeTransport('{"files":{"../escape.js":"bad"}}')
    with pytest.raises(ValueError, match="Unsafe generated path"):
        ModelCodeGenerator(transport).generate(spec)


def test_ai_editor_only_replaces_returned_files():
    transport = FakeTransport('{"files":{"styles.css":"body { color: purple; }"}}')
    files = {"index.html": "<html></html>", "styles.css": "body {}"}
    updated = AIProjectEditor(transport).edit(files, "Make it purple")
    assert updated["index.html"] == files["index.html"]
    assert updated["styles.css"] == "body { color: purple; }"


def test_ai_editor_rejects_unsafe_path():
    transport = FakeTransport('{"files":{"../../escape":"bad"}}')
    with pytest.raises(ValueError, match="unsafe path"):
        AIProjectEditor(transport).edit({"index.html": "<html></html>"}, "change it")
