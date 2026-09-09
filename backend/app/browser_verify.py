from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser


@dataclass
class BrowserCheckResult:
    success: bool
    checks: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)


class _PreviewParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        self.tags.append(tag.lower())


class StaticBrowserVerifier:
    """Browser-like smoke verification without executing generated scripts."""

    def verify(self, html: str) -> BrowserCheckResult:
        parser = _PreviewParser()
        try:
            parser.feed(html)
            parser.close()
        except Exception as exc:
            return BrowserCheckResult(False, diagnostics=[f"HTML parser failed: {exc}"])

        checks: list[str] = []
        diagnostics: list[str] = []
        required = [("html", "document root"), ("head", "head"), ("body", "body")]
        for tag, label in required:
            if tag in parser.tags:
                checks.append(f"{label}: pass")
            else:
                diagnostics.append(f"Missing {label} element")

        if "title" in parser.tags:
            checks.append("document title: pass")
        else:
            diagnostics.append("Missing document title")

        # Preview verification intentionally refuses executable script tags.
        if "script" in parser.tags:
            diagnostics.append("Executable script tags are not allowed in static preview verification")

        return BrowserCheckResult(not diagnostics, checks, diagnostics)
