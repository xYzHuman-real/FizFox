from __future__ import annotations

import base64
from html import escape
from typing import Dict, Protocol


class PreviewBuilder(Protocol):
    def build(self, files: Dict[str, str]) -> str:
        """Build a safe preview representation without executing project code."""


class StaticPreviewBuilder:
    """Creates a self-contained preview document for the static-web MVP.

    Generated JavaScript is intentionally not executed by this builder. The
    preview is therefore a safe artifact, not an executable sandbox.
    """

    def build(self, files: Dict[str, str]) -> str:
        html = files.get("index.html", "")
        css = files.get("styles.css", "")
        if not html:
            return ""

        # Inline only generated HTML/CSS as inert preview content. Strip script
        # blocks so the preview cannot execute generated JavaScript.
        safe_html = self._strip_scripts(html)
        safe_css = css.replace("</style>", "&lt;/style&gt;")
        return f"<!doctype html><html><head><meta charset=\"UTF-8\"><style>{safe_css}</style></head><body>{safe_html}</body></html>"

    @staticmethod
    def _strip_scripts(html: str) -> str:
        import re
        return re.sub(r"<script\b[^>]*>.*?</script>", "", html, flags=re.I | re.S)


def encode_preview(preview_html: str) -> str:
    """Return a base64 representation suitable for a data URL."""
    return base64.b64encode(preview_html.encode("utf-8")).decode("ascii")
