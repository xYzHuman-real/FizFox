from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Protocol


@dataclass(frozen=True)
class VerificationDiagnostic:
    level: str
    code: str
    message: str
    file: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    success: bool
    diagnostics: List[VerificationDiagnostic]


class Verifier(Protocol):
    def verify(self, files: Dict[str, str]) -> VerificationResult:
        """Verify generated project files without executing untrusted code."""


class StaticVerifier:
    """Deterministic verifier for the static-web MVP.

    This layer performs syntax/contract checks only. It never executes generated
    JavaScript or starts a generated application on the FizFox host.
    """

    def verify(self, files: Dict[str, str]) -> VerificationResult:
        diagnostics: List[VerificationDiagnostic] = []

        if not files:
            return VerificationResult(False, [VerificationDiagnostic("error", "NO_FILES", "Nothing was generated to verify.")])

        index = files.get("index.html")
        if index is None:
            diagnostics.append(VerificationDiagnostic("error", "MISSING_ENTRYPOINT", "Generated project must contain index.html.", "index.html"))
        else:
            diagnostics.extend(self._verify_html(index))

        css = files.get("styles.css")
        if css is not None and "{" not in css:
            diagnostics.append(VerificationDiagnostic("warning", "EMPTY_CSS_RULES", "styles.css contains no CSS rule blocks.", "styles.css"))

        js = files.get("app.js")
        if js is not None:
            diagnostics.extend(self._verify_js(js))

        return VerificationResult(
            success=not any(item.level == "error" for item in diagnostics),
            diagnostics=diagnostics,
        )

    @staticmethod
    def _verify_html(content: str) -> List[VerificationDiagnostic]:
        diagnostics: List[VerificationDiagnostic] = []
        lowered = content.lower()
        if "<!doctype html>" not in lowered:
            diagnostics.append(VerificationDiagnostic("warning", "MISSING_DOCTYPE", "index.html does not declare an HTML5 doctype.", "index.html"))
        if not re.search(r"<html(?:\s|>)", lowered):
            diagnostics.append(VerificationDiagnostic("error", "INVALID_HTML_ROOT", "index.html is missing the <html> root element.", "index.html"))
        if "<body" not in lowered or "</body>" not in lowered:
            diagnostics.append(VerificationDiagnostic("error", "INVALID_HTML_BODY", "index.html must contain a complete body element.", "index.html"))
        return diagnostics

    @staticmethod
    def _verify_js(content: str) -> List[VerificationDiagnostic]:
        diagnostics: List[VerificationDiagnostic] = []
        if content.count("{") != content.count("}"):
            diagnostics.append(VerificationDiagnostic("error", "UNBALANCED_JS_BRACES", "app.js has unbalanced curly braces.", "app.js"))
        if content.count("(") != content.count(")"):
            diagnostics.append(VerificationDiagnostic("error", "UNBALANCED_JS_PARENS", "app.js has unbalanced parentheses.", "app.js"))
        return diagnostics
