from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .generator import CodeGenerator
from .models import AppSpec
from .verifier import StaticVerifier, VerificationDiagnostic


@dataclass(frozen=True)
class RepairResult:
    changed: bool
    files: Dict[str, str]
    diagnostics: List[VerificationDiagnostic]
    attempts: int


class BoundedRepairEngine:
    """Apply only known-safe deterministic repairs, with a hard attempt limit."""

    def __init__(self, verifier: StaticVerifier, generator: CodeGenerator, max_attempts: int = 2) -> None:
        self.verifier = verifier
        self.generator = generator
        self.max_attempts = max(1, max_attempts)

    def repair(self, files: Dict[str, str], spec: AppSpec) -> RepairResult:
        current = dict(files)
        attempts = 0

        while attempts < self.max_attempts:
            result = self.verifier.verify(current)
            if result.success:
                return RepairResult(attempts > 0, current, result.diagnostics, attempts)

            attempts += 1
            repaired = self._repair_known_errors(current, result.diagnostics, spec)
            if repaired == current:
                return RepairResult(False, current, result.diagnostics, attempts)
            current = repaired

        result = self.verifier.verify(current)
        return RepairResult(attempts > 0, current, result.diagnostics, attempts)

    def _repair_known_errors(
        self,
        files: Dict[str, str],
        diagnostics: List[VerificationDiagnostic],
        spec: AppSpec,
    ) -> Dict[str, str]:
        repaired = dict(files)
        codes = {item.code for item in diagnostics if item.level == "error"}

        if "MISSING_ENTRYPOINT" in codes:
            generated = self.generator.generate(spec)
            repaired["index.html"] = generated["index.html"]

        if "INVALID_HTML_ROOT" in codes or "INVALID_HTML_BODY" in codes:
            html = repaired.get("index.html", "").strip()
            if html and "<html" not in html.lower():
                repaired["index.html"] = (
                    "<!doctype html>\n<html lang=\"en\">\n"
                    "<head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><title>FizFox App</title></head>\n"
                    f"<body>{html}</body>\n</html>\n"
                )

        if "UNBALANCED_JS_BRACES" in codes:
            js = repaired.get("app.js")
            if js is not None:
                delta = js.count("{") - js.count("}")
                if delta > 0:
                    repaired["app.js"] = js + ("\n}" * delta) + "\n"

        if "UNBALANCED_JS_PARENS" in codes:
            js = repaired.get("app.js")
            if js is not None:
                delta = js.count("(") - js.count(")")
                if delta > 0:
                    repaired["app.js"] = js + ("\n)" * delta) + "\n"

        return repaired
