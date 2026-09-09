from __future__ import annotations

from typing import Dict, Protocol


class ProjectEditor(Protocol):
    def edit(self, files: Dict[str, str], instruction: str) -> Dict[str, str]:
        """Apply a user-directed edit without executing project code."""


class HeuristicProjectEditor:
    """Small deterministic editor for the MVP iteration loop.

    This is intentionally conservative: it only changes known static-web
    presentation details and leaves arbitrary code execution out of scope.
    """

    def edit(self, files: Dict[str, str], instruction: str) -> Dict[str, str]:
        updated = dict(files)
        text = instruction.strip().lower()

        if "dark" in text:
            updated["styles.css"] = self._darken(updated.get("styles.css", ""))

        if "purple" in text:
            updated["styles.css"] = self._add_purple_accent(updated.get("styles.css", ""))

        if any(term in text for term in ("hero", "hero section")):
            updated["index.html"] = self._ensure_hero(updated.get("index.html", ""))

        if any(term in text for term in ("bigger heading", "larger heading", "larger title")):
            updated["styles.css"] = updated.get("styles.css", "") + "\nh1 { font-size: clamp(52px, 10vw, 96px); }\n"

        return updated

    @staticmethod
    def _darken(css: str) -> str:
        if not css:
            return css
        replacements = {
            "#ffffff": "#111018",
            "#faf9ff": "#111018",
            "#f6f2ff": "#191522",
            "#17131f": "#f7f4ff",
            "#6e6878": "#c5bdd2",
        }
        for old, new in replacements.items():
            css = css.replace(old, new)
        return css + "\nbody { background: #111018; color: #f7f4ff; }\n"

    @staticmethod
    def _add_purple_accent(css: str) -> str:
        if not css:
            return css
        return css + "\n:root { --fizfox-purple: #7356e8; }\nbutton { background: var(--fizfox-purple); }\n"

    @staticmethod
    def _ensure_hero(html: str) -> str:
        if not html or "class=\"hero\"" in html:
            return html
        marker = "<main>"
        if marker not in html:
            return html
        hero = "\n      <section class=\"hero\"><p class=\"eyebrow\">Built with FizFox</p><h1>Made for your idea.</h1><p>Turn your concept into a real product.</p><button type=\"button\">Get started</button></section>\n"
        return html.replace(marker, marker + hero, 1)
