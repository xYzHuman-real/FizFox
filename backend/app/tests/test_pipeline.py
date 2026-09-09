from app.editor import HeuristicProjectEditor
from app.generator import HeuristicCodeGenerator
from app.planner import HeuristicPlanner
from app.preview import StaticPreviewBuilder
from app.sandbox import IsolatedSandbox
from app.verifier import StaticVerifier


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
