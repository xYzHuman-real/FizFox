from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIErrorInfo:
    code: str
    message: str
    retryable: bool = False


class FizFoxAIError(RuntimeError):
    def __init__(self, info: AIErrorInfo, cause: Exception | None = None) -> None:
        super().__init__(info.message)
        self.info = info
        self.__cause__ = cause
