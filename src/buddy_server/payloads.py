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


_SKIP_KEYS = {"ok", "created", "modified", "warnings", "hints", "feature", "sketch", "volume", "geometry",
              "constraints", "profile", "path"}  # fmt: skip
MAX_COMPACT_LINES = 6


def _number(value: float) -> str:
    text = f"{value:,.1f}" if abs(value) >= 100 else f"{round(value, 3):g}"
    return text.replace(",", "\u202f").replace(".", ",")


def _scalar(value: Any) -> str | None:
    if isinstance(value, bool):
        return "ja" if value else "nein"
    if isinstance(value, int | float):
        return _number(float(value)) if isinstance(value, float) else str(value)
    if isinstance(value, str):
        if not value:
            return None
        return value if len(value) <= 80 else value[:79] + "…"
    if value is None:
        return "–"
    return None


def _labels(entries: Any) -> str:
    labels = [str(e.get("label", e.get("name", "?"))) for e in entries if isinstance(e, Mapping)]
    return ", ".join(labels[:4]) + (f" (+{len(labels) - 4})" if len(labels) > 4 else "")


def compact_text(result: Any) -> str:
    """Key facts of a tool result as a few lines of plain text (the full JSON stays in the detail view)."""
    if isinstance(result, str):
        lines = [line for line in result.splitlines() if line.strip()]
        return "\n".join(lines[:3]) + (f"\n… (+{len(lines) - 3} Zeilen)" if len(lines) > 3 else "")
    if isinstance(result, list):
        return f"{len(result)} Einträge"
    if not isinstance(result, Mapping):
        return _scalar(result) or "ok"
    lines: list[str] = []
    if result.get("created"):
        lines.append(f"✚ erstellt: {_labels(result['created'])}")
    elif result.get("modified"):
        lines.append(f"✎ geändert: {_labels(result['modified'])}")
    sketch = result.get("sketch")
    if isinstance(sketch, Mapping) and "dof" in sketch:
        state = "vollständig bestimmt" if sketch.get("fully_constrained") else "unterbestimmt"
        lines.append(f"✎ {sketch.get('sketch', 'Skizze')}: DoF {sketch['dof']} ({state})")
    if isinstance(result.get("volume"), int | float):
        lines.append(f"▣ Volumen {_number(float(result['volume']))} mm³")
    if isinstance(result.get("issues"), list):
        issues = result["issues"]
        codes = ", ".join(str(i.get("code", "?")) for i in issues[:4] if isinstance(i, Mapping))
        lines.append(f"{'✓ keine Befunde' if not issues else f'✗ {len(issues)} Befunde: {codes}'}")
    facts: list[str] = []
    for key, value in result.items():
        if key in _SKIP_KEYS or key == "issues":
            continue
        shown = _scalar(value)
        if shown is not None:
            facts.append(f"{key}: {shown}")
        elif isinstance(value, list):
            facts.append(f"{key}: {len(value)} Einträge")
        elif isinstance(value, Mapping):
            inner = [f"{k} {s}" for k, v in value.items() if (s := _scalar(v)) is not None][:3]
            if inner:
                facts.append(f"{key}: {', '.join(inner)}")
    if facts:
        lines.append(" · ".join(facts[:4]))
    lines += [f"→ {hint}" for hint in result.get("hints", [])[:2] if isinstance(result.get("hints"), list)]
    return "\n".join(lines[:MAX_COMPACT_LINES]) or "ok"


def compact_arguments(arguments: Any) -> str:
    """Request arguments as ``key: value`` lines (nested objects on one line, long lists counted)."""
    if not isinstance(arguments, Mapping) or not arguments:
        return "(keine Argumente)"
    lines: list[str] = []
    for key, value in arguments.items():
        shown = _scalar(value)
        if shown is None and isinstance(value, Mapping):
            parts = []
            for inner_key, inner in value.items():
                inner_shown = _scalar(inner)
                if inner_shown is None and isinstance(inner, Mapping):
                    inner_shown = "{" + ", ".join(f"{k} {_scalar(v)}" for k, v in inner.items()) + "}"
                elif inner_shown is None and isinstance(inner, list):
                    inner_shown = _list(inner)
                parts.append(f"{inner_key} {inner_shown}")
            shown = ", ".join(parts)
        elif shown is None and isinstance(value, list):
            shown = _list(value)
        lines.append(f"{key}: {shown}")
    if len(lines) > MAX_COMPACT_LINES:
        lines = [*lines[: MAX_COMPACT_LINES - 1], f"… (+{len(lines) - MAX_COMPACT_LINES + 1} Argumente)"]
    return "\n".join(line if len(line) <= 160 else line[:159] + "…" for line in lines)


def _list(values: list[Any]) -> str:
    scalars = [_scalar(v) for v in values]
    if len(values) <= 5 and all(s is not None for s in scalars):
        return "[" + ", ".join(str(s) for s in scalars) + "]"
    return f"{len(values)} Einträge"


@dataclass(frozen=True)
class Response:
    ok: bool
    text: str
    summary: str
    warnings: tuple[str, ...] = ()
    error_code: str = ""
    compact: str = ""


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
        lines = message.splitlines()
        compact = "\n".join(
            [lines[0], *[line for line in lines[1:] if line.startswith(("Hint", "Hinweis"))][:2]]
        )
        return Response(False, message, code, error_code=code, compact=compact)
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
    compact = mask.text(compact_text(structured))
    if images:
        summary = compact = " ".join(images)
    return Response(True, body, summary, tuple(mask.text(w) for w in warnings), compact=compact)
