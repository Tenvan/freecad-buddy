"""Prepare tool requests and responses for display: mask secrets, replace binaries, limit size.

Everything a front end (TUI, headless log, JSONL file) shows of a tool call passes through here
once, so no front end ever sees raw payloads or secrets.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

MASK = "***"
MAX_DETAIL_CHARS = 200_000
"""Upper bound for one rendered payload kept in memory (full view / JSONL)."""

_SECRET_KEY = re.compile(r"token|authorization|password|passwd|secret|api[_-]?key|cookie", re.IGNORECASE)
_BEARER = re.compile(r"(Bearer\s+)\S+", re.IGNORECASE)
# Random tokens (e.g. secrets.token_urlsafe): long, mixed case and digits, no spaces or dots.
_TOKENISH = re.compile(r"(?<![A-Za-z0-9_\-])(?=[A-Za-z0-9_\-]*[a-z])(?=[A-Za-z0-9_\-]*[A-Z])"
                       r"(?=[A-Za-z0-9_\-]*\d)[A-Za-z0-9_\-]{32,}(?![A-Za-z0-9_\-])")  # fmt: skip
_ERROR_CODE = re.compile(r"^\[([a-z_]+)\]")


class Masker:
    """Replaces secrets in nested JSON-like data: secret-looking keys, known secrets, token-like strings."""

    def __init__(self, secrets: Iterable[str] = ()) -> None:
        self._secrets = sorted({s for s in secrets if len(s) >= 8}, key=len, reverse=True)

    def __call__(self, value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(key): MASK if _SECRET_KEY.search(str(key)) and value[key] else self(value[key])
                for key in value
            }
        if isinstance(value, list | tuple):
            return [self(item) for item in value]
        if isinstance(value, str):
            return self.text(value)
        return value

    def text(self, text: str) -> str:
        for secret in self._secrets:
            text = text.replace(secret, MASK)
        text = _BEARER.sub(rf"\g<1>{MASK}", text)
        return _TOKENISH.sub(MASK, text)


def render_json(value: Any) -> str:
    """Pretty JSON (or plain text for strings), capped at ``MAX_DETAIL_CHARS``."""
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) > MAX_DETAIL_CHARS:
        text = text[:MAX_DETAIL_CHARS] + f"\n… (gekürzt, {len(text):,} Zeichen gesamt)".replace(",", ".")
    return text


def preview_parts(text: str, max_lines: int = 8, width: int = 160) -> tuple[str, int]:
    """First lines of ``text`` for a chat bubble and the number of hidden lines."""
    lines = text.splitlines() or [""]
    shown = [line if len(line) <= width else line[: width - 1] + "…" for line in lines[:max_lines]]
    return "\n".join(shown), max(0, len(lines) - max_lines)


def hidden_hint(hidden: int) -> str:
    return f"… (+{hidden} Zeilen, Enter = alles)"


def preview(text: str, max_lines: int = 8, width: int = 160) -> str:
    """Plain-text preview with the hidden-lines hint appended (headless output, tests)."""
    shown, hidden = preview_parts(text, max_lines, width)
    return shown + (f"\n{hidden_hint(hidden)}" if hidden else "")


def summarize(result: Any) -> tuple[str, tuple[str, ...]]:
    """Short summary of a tool result: created labels and sketch DoF, plus warnings."""
    if not isinstance(result, dict):
        return "ok", ()
    parts = [f"+{entry['label']}" for entry in result.get("created", [])[:3] if isinstance(entry, dict)]
    if isinstance(result.get("sketch"), dict):
        parts.append(f"DoF={result['sketch'].get('dof')}")
    warnings = tuple(str(w) for w in result.get("warnings", []) if isinstance(result.get("warnings"), list))
    return (" ".join(parts) or "ok"), warnings


@dataclass(frozen=True)
class Response:
    ok: bool
    text: str
    summary: str
    warnings: tuple[str, ...] = ()
    error_code: str = ""


def _image_placeholder(item: Mapping[str, Any]) -> str:
    size = len(str(item.get("data", ""))) * 3 // 4
    kind = str(item.get("mimeType", "image/png")).split("/")[-1].upper()
    return f"[{kind} {size / 1024:.0f} KB]"


def describe_result(result: Any, mask: Masker) -> Response:
    """Turn an MCP ``CallToolResult`` (model or dict) into display text, status and summary."""
    data: Any = (
        result.model_dump(by_alias=True, exclude_none=True) if isinstance(result, BaseModel) else result
    )
    if not isinstance(data, Mapping):
        return Response(True, render_json(mask(data)), "ok")
    texts: list[str] = []
    images: list[str] = []
    for item in data.get("content", []) or []:
        if isinstance(item, Mapping) and item.get("type") == "image":
            images.append(_image_placeholder(item))
        elif isinstance(item, Mapping) and item.get("type") == "text":
            texts.append(str(item.get("text", "")))
    if data.get("isError"):
        message = mask.text("\n".join(texts))
        match = _ERROR_CODE.match(message)
        code = match.group(1) if match else "error"
        return Response(False, message, code, error_code=code)
    structured = data.get("structuredContent")
    if isinstance(structured, Mapping) and set(structured) == {"result"}:
        structured = structured["result"]
    if structured is None and len(texts) == 1:
        try:
            structured = json.loads(texts[0])
        except ValueError:
            structured = texts[0]
    elif structured is None:
        structured = texts
    body = images[0] if images and not texts else render_json(mask(structured))
    summary, warnings = summarize(structured)
    if images:
        summary = " ".join(images)
    return Response(True, body, summary, tuple(mask.text(w) for w in warnings))
