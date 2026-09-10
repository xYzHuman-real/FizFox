from __future__ import annotations

import json
import re


_FENCE_RE = re.compile(r"\A\s*```(?:json)?\s*(.*?)\s*```\s*\Z", re.IGNORECASE | re.DOTALL)


def parse_json_object(response: str, *, label: str = "AI response") -> dict:
    """Parse a JSON object, allowing one optional markdown JSON fence."""
    if not isinstance(response, str):
        raise ValueError(f"{label} must be text")
    text = response.strip()
    match = _FENCE_RE.match(text)
    if match:
        text = match.group(1).strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must return a JSON object")
    return value
