from __future__ import annotations

import json

import pytest

from app.ai_contract import AIRequest
from app.ai_repair import AIProjectRepairer
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
        name="Repair Test",
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


def test_ai_repair_updates_only_returned_files():
    transport = FakeTransport(json.dumps({"files": {"index.html": "<html><body>fixed</body></html>"}}))
    files = {"index.html": "broken", "styles.css": "body{}"}
    diagnostics = [{"code": "INVALID_HTML_ROOT", "level": "error"}]
    updated = AIProjectRepairer(transport).repair(files, diagnostics, sample_spec())
    assert updated["index.html"] == "<html><body>fixed</body></html>"
    assert updated["styles.css"] == "body{}"
    assert isinstance(transport.requests[0], AIRequest)


def test_ai_repair_rejects_unsafe_paths():
    transport = FakeTransport(json.dumps({"files": {"../escape.js": "bad"}}))
    with pytest.raises(ValueError, match="unsafe path"):
        AIProjectRepairer(transport).repair({"index.html": "broken"}, [], sample_spec())
