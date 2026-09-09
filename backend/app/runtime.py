from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Protocol


@dataclass(frozen=True)
class RuntimeDiagnostic:
    level: str
    code: str
    message: str
    file: str | None = None


@dataclass(frozen=True)
class RuntimeResult:
    success: bool
    diagnostics: List[RuntimeDiagnostic]


class SandboxRuntime(Protocol):
    def build(self, files: Dict[str, str]) -> RuntimeResult:
        """Validate/build generated files inside a runtime boundary."""


class SafeStaticRuntime:
    """MVP runtime boundary that performs static validation only.

    It deliberately does not execute generated code on the FizFox host.
    A container-backed implementation can replace this interface later.
    """

    MAX_FILES = 100
    MAX_FILE_SIZE = 512_000
    ALLOWED_FILES = {".html", ".css", ".js", ".json", ".md", ".txt"}

    def build(self, files: Dict[str, str]) -> RuntimeResult:
        diagnostics: List[RuntimeDiagnostic] = []

        if not files:
            return RuntimeResult(
                success=False,
                diagnostics=[RuntimeDiagnostic("error", "NO_FILES", "Project contains no generated files.")],
            )

        if len(files) > self.MAX_FILES:
            diagnostics.append(
                RuntimeDiagnostic("error", "FILE_LIMIT", f"Project exceeds the {self.MAX_FILES}-file runtime limit.")
            )

        for path, content in files.items():
            diagnostics.extend(self._validate_file(path, content))

        if "index.html" not in files:
            diagnostics.append(
                RuntimeDiagnostic("error", "MISSING_ENTRYPOINT", "Generated project must contain index.html.")
            )

        return RuntimeResult(
            success=not any(item.level == "error" for item in diagnostics),
            diagnostics=diagnostics,
        )

    def _validate_file(self, path: str, content: str) -> List[RuntimeDiagnostic]:
        diagnostics: List[RuntimeDiagnostic] = []
        normalized = path.replace("\\", "/")

        if normalized.startswith("/") or "../" in normalized or normalized == "..":
            diagnostics.append(RuntimeDiagnostic("error", "UNSAFE_PATH", "File path escapes the project boundary.", path))
            return diagnostics

        suffix = "." + normalized.rsplit(".", 1)[-1].lower() if "." in normalized else ""
        if suffix not in self.ALLOWED_FILES:
            diagnostics.append(
                RuntimeDiagnostic("error", "UNSUPPORTED_FILE", f"File type '{suffix or 'unknown'}' is not allowed.", path)
            )

        if len(content.encode("utf-8")) > self.MAX_FILE_SIZE:
            diagnostics.append(
                RuntimeDiagnostic("error", "FILE_SIZE_LIMIT", "File exceeds the runtime file-size limit.", path)
            )

        if "index.html" == normalized and "<html" not in content.lower():
            diagnostics.append(
                RuntimeDiagnostic("error", "INVALID_HTML", "index.html does not contain an HTML document root.", path)
            )

        return diagnostics
