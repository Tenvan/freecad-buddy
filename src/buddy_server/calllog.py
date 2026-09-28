"""Tool-call logging: an MCP middleware that publishes every request/response pair on the bus,
plus an optional JSONL file writer. Front ends render these events as a chat.
"""

from __future__ import annotations

import itertools
import json
import threading
import time
from pathlib import Path
from typing import Any

from mcp.server.context import CallNext, HandlerResult, ServerRequestContext

from buddy_server.events import Event, EventBus, ToolFinished, ToolStarted
from buddy_server.payloads import Masker, describe_result, render_json

# Module-wide, so ids stay unique when the server is rebuilt (e.g. toggling execute_python).
_call_ids = itertools.count(1)


class ToolCallLog:
    """``ServerMiddleware``: observes ``tools/call`` requests without changing them."""

    def __init__(self, bus: EventBus, mask: Masker) -> None:
        self._bus = bus
        self._mask = mask
        self._sessions: dict[int, str] = {}

    async def __call__(self, ctx: ServerRequestContext[Any, Any], call_next: CallNext) -> HandlerResult:
        if ctx.method != "tools/call" or ctx.request_id is None:
            return await call_next(ctx)
        params = dict(ctx.params or {})
        name = str(params.get("name", "?"))
        call_id = next(_call_ids)
        arguments = render_json(self._mask(params.get("arguments") or {}))
        self._bus.publish(ToolStarted(call_id, name, arguments, self._session_label(ctx)))
        started = time.monotonic()
        try:
            result = await call_next(ctx)
        except Exception as error:  # protocol-level failure (unknown tool, invalid params)
            text = self._mask.text(str(error))
            self._bus.publish(
                ToolFinished(call_id, name, time.monotonic() - started, False, "protocol_error",
                             response=text, error_code="protocol_error")
            )  # fmt: skip
            raise
        response = describe_result(result, self._mask)
        self._bus.publish(
            ToolFinished(call_id, name, time.monotonic() - started, response.ok, response.summary,
                         response.warnings, response=response.text, error_code=response.error_code,
                         compact=response.compact)
        )  # fmt: skip
        return result

    def _session_label(self, ctx: ServerRequestContext[Any, Any]) -> str:
        key = id(ctx.session)
        if key not in self._sessions:
            client = "Client"
            try:
                params = ctx.session.client_params
                if params is not None and params.client_info.name:
                    client = params.client_info.name
            except AttributeError:
                pass
            self._sessions[key] = f"{client} #{len(self._sessions) + 1}"
        return self._sessions[key]


class JsonlLog:
    """Bus subscriber writing tool calls as JSON lines; rotates to ``<file>.1`` beyond ``max_bytes``."""

    def __init__(self, path: Path, max_bytes: int = 10 * 1024 * 1024) -> None:
        self.path = path
        self.max_bytes = max_bytes
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)

    def __call__(self, event: Event) -> None:
        match event:
            case ToolStarted():
                record: dict[str, Any] = {"type": "request", "call_id": event.call_id, "tool": event.name,
                                          "session": event.session, "arguments": event.arguments}  # fmt: skip
            case ToolFinished():
                record = {"type": "response", "call_id": event.call_id, "tool": event.name, "ok": event.ok,
                          "duration_ms": round(event.duration * 1000, 1), "summary": event.summary,
                          "warnings": list(event.warnings), "error_code": event.error_code,
                          "response": event.response}  # fmt: skip
            case _:
                return
        record["at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(event.at))
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with self._lock:
            if self.path.exists() and self.path.stat().st_size + len(line) > self.max_bytes:
                self.path.replace(self.path.with_name(self.path.name + ".1"))
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(line)
