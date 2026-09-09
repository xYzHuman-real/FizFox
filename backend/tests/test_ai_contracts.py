from app.ai_contract import AIRequest
from app.generation_contract import ModelCodeGenerator, parse_json_object
from app.models import AppSpec


class FakeTransport:
    def __init__(self, response: str):
        self.response = response
        self.requests = []

    def complete(self, request: AIRequest) -> str:
        self.requests.append(request)
        return self.response


def minimal_spec() -> AppSpec:
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
    assert parse_json_object('```json\n{"files": {"index.html": "<html></html>"}}\n```')["files"]


def test_model_generator_uses_ai_request_and_validates_files():
    transport = FakeTransport('{"files":{"index.html":"<html></html>"}}')
    generated = ModelCodeGenerator(transport).generate(minimal_spec())
    assert generated.files["index.html"] == "<html></html>"
    assert isinstance(transport.requests[0], AIRequest)


def test_model_generator_rejects_unsafe_path():
    transport = FakeTransport('{"files":{"../escape.html":"bad"}}')
    try:
        ModelCodeGenerator(transport).generate(minimal_spec())
    except ValueError as exc:
        assert "Unsafe generated path" in str(exc)
    else:
        raise AssertionError("unsafe path was accepted")
