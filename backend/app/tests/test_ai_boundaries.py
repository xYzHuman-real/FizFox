from app.ai_contract import AIRequest, ModelPlanner
from app.ai_editor import AIProjectEditor
from app.generation_contract import ModelCodeGenerator, parse_json_object
from app.models import AppSpec
from app.providers import JsonAppSpecParser


class FakeTransport:
    def __init__(self, response: str):
        self.response = response
        self.requests = []

    def complete(self, request: AIRequest) -> str:
        self.requests.append(request)
        return self.response


def test_json_object_parser_accepts_fenced_json():
    payload = parse_json_object('```json\n{"files":{"index.html":"<html><body>ok</body></html>"}}\n```')
    assert payload["files"]["index.html"].startswith("<html")


def test_planner_validates_model_output():
    spec = {
        "name": "Demo",
        "app_type": "web application",
        "pages": [{"name": "Home", "route": "/"}],
        "components": [],
        "features": [],
        "routes": ["/"],
        "data_requirements": [],
        "dependencies": [],
        "styling_direction": "minimal",
        "constraints": [],
    }
    planner = ModelPlanner(FakeTransport(__import__("json").dumps(spec)))
    result = planner.plan("Build Demo")
    assert isinstance(result, AppSpec)
    assert result.name == "Demo"


def test_generator_rejects_parent_traversal():
    spec = AppSpec(name="Demo", app_type="web application")
    generator = ModelCodeGenerator(FakeTransport('{"files":{"../escape.js":"bad"}}'))
    try:
        generator.generate(spec)
    except ValueError as exc:
        assert "Unsafe generated path" in str(exc)
    else:
        raise AssertionError("unsafe path was accepted")


def test_editor_rejects_parent_traversal():
    editor = AIProjectEditor(FakeTransport('{"files":{"../escape.js":"bad"}}'))
    try:
        editor.edit({"index.html": "<html><body>ok</body></html>"}, "change it")
    except ValueError as exc:
        assert "unsafe path" in str(exc).lower()
    else:
        raise AssertionError("unsafe path was accepted")
