"""Chat view of the tool calls: one entry per call with a request and a response bubble.

Events arrive in bursts (thousands per second in stress tests), so they are buffered and applied
in one batch per frame; at most ``MAX_CALLS`` entries are kept, older ones are removed.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import ClassVar

from rich.console import Group, RenderableType
from rich.highlighter import JSONHighlighter
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Label, ListItem, ListView, Static, TextArea

from buddy_server.events import ToolFinished, ToolStarted
from buddy_server.payloads import hidden_hint, preview_parts

MAX_CALLS = 1000


def _clock(at: float) -> str:
    return time.strftime("%H:%M:%S", time.localtime(at))


@dataclass
class CallRecord:
    call_id: int
    name: str
    session: str = ""
    arguments: str = "{}"
    compact_arguments: str = ""
    started_at: float = 0.0
    finished: ToolFinished | None = None
    item: CallItem | None = None

    @property
    def state(self) -> str:
        if self.finished is None:
            return "running"
        if not self.finished.ok:
            return "error"
        return "warning" if self.finished.warnings else "ok"

    def status_text(self) -> str:
        done = self.finished
        if done is None:
            return "läuft …"
        status = "ok" if done.ok else f"FEHLER {done.error_code or ''}".rstrip()
        return f"{status} · {done.duration * 1000:.0f} ms"

    def line(self) -> Text:
        stamp = _clock(self.started_at or (self.finished.at if self.finished else time.time()))
        summary = self.finished.summary if self.finished else ""
        styles = {"running": "", "ok": "green", "warning": "yellow", "error": "bold red"}
        return Text.assemble(
            f"{stamp}  {self.name}  ", (self.status_text(), styles[self.state]), f"  {summary}"
        )

    def detail(self) -> str:
        parts = [
            f"→ Anfrage #{self.call_id}: {self.name}"
            + (f" · {self.session}" if self.session else "")
            + (f" · {_clock(self.started_at)}" if self.started_at else ""),
            self.arguments,
            "",
            f"← Antwort: {self.status_text()}",
        ]
        if self.finished is not None:
            parts += [f"Zusammenfassung: {self.finished.summary}"]
            parts += [f"Warnung: {warning}" for warning in self.finished.warnings]
            parts += [self.finished.response]
        return "\n".join(parts)


_JSON = JSONHighlighter()


def _code(text: str) -> RenderableType:
    """Bubble body: JSON gets foreground-only highlighting (no background box), the hint stays neutral."""
    shown, hidden = preview_parts(text)
    body = Text(shown)
    if shown.lstrip().startswith(("{", "[")):
        _JSON.highlight(body)
    if hidden:
        body.append("\n" + hidden_hint(hidden), style="dim italic")
    return body


class CallItem(ListItem):
    """One tool call; updated in place when its response arrives."""

    def __init__(self, record: CallRecord) -> None:
        super().__init__()
        self.record = record
        self._line = Static(classes="line")
        self._request = Static(classes="request")
        self._response = Static(classes="response")

    def compose(self) -> ComposeResult:
        yield self._line
        yield self._request
        yield self._response

    def on_mount(self) -> None:
        self.refresh_from_record()

    def refresh_from_record(self) -> None:
        record = self.record
        self.set_classes(f"state-{record.state}")
        self._line.update(record.line())
        who = f" · {record.session}" if record.session else ""
        stamp = f" · {_clock(record.started_at)}" if record.started_at else ""
        self._request.border_title = f"→ {record.name}{who}{stamp}"
        if record.compact_arguments:
            self._request.update(Text(record.compact_arguments))
        else:
            self._request.update(_code(record.arguments))
        self._response.border_title = f"← {record.status_text()}"
        done = record.finished
        if done is None:
            self._response.update(Text("⏳ wartet auf FreeCAD …", style="italic"))
            return
        body: list[RenderableType] = []
        if done.warnings:
            body.append(Text("\n".join(f"⚠ {w}" for w in done.warnings), style="yellow"))
        if done.compact:
            body.append(Text(done.compact))
            if done.response and done.response.strip() != done.compact.strip():
                body.append(Text("Enter: vollständige Antwort", style="dim italic"))
        else:
            body.append(_code(done.response) if done.response else Text(done.summary))
        self._response.update(Group(*body))


class ToolChat(ListView):
    """Scrollable chat of tool calls. Enter opens the full request/response."""

    DEFAULT_CSS = """
    ToolChat CallItem { height: auto; padding: 0 1; background: transparent; }
    ToolChat CallItem.-highlight { background: $boost; }
    ToolChat CallItem .request {
        height: auto; margin: 0 16 0 0; padding: 0 1; border: round $accent; border-title-color: $accent;
    }
    ToolChat CallItem .response {
        height: auto; margin: 0 0 1 16; padding: 0 1; border: round $secondary;
        border-title-align: right;
    }
    ToolChat CallItem.state-ok .response { border: round $success; border-title-color: $success; }
    ToolChat CallItem.state-warning .response { border: round $warning; border-title-color: $warning; }
    ToolChat CallItem.state-error .response { border: round $error; border-title-color: $error; }
    ToolChat CallItem .line { display: none; height: 1; }
    ToolChat.compact CallItem { padding: 0; }
    ToolChat.compact CallItem .line { display: block; }
    ToolChat.compact CallItem .request, ToolChat.compact CallItem .response { display: none; }
    """

    def __init__(self, *, id: str | None = None) -> None:
        super().__init__(id=id)
        self.records: OrderedDict[int, CallRecord] = OrderedDict()
        self._pending: list[ToolStarted | ToolFinished] = []
        self._scheduled = False

    def add(self, event: ToolStarted | ToolFinished) -> None:
        self._pending.append(event)
        if not self._scheduled:
            self._scheduled = True
            self.set_timer(0.05, self._flush)

    async def _flush(self) -> None:
        self._scheduled = False
        events, self._pending = self._pending, []
        evicted: list[CallItem] = []
        changed: set[int] = set()
        for event in events:
            record = self.records.get(event.call_id)
            if record is None:
                record = self.records[event.call_id] = CallRecord(event.call_id, event.name)
                while len(self.records) > MAX_CALLS:
                    _, old = self.records.popitem(last=False)
                    if old.item is not None:
                        evicted.append(old.item)
            if isinstance(event, ToolStarted):
                record.session, record.arguments, record.started_at = event.session, event.arguments, event.at
                record.compact_arguments = event.compact
            else:
                record.finished = event
            changed.add(event.call_id)
        follow = self.scroll_y >= self.max_scroll_y
        if evicted:
            await self.remove_children(evicted)
        new = [record for record in self.records.values() if record.item is None]
        for call_id in changed:
            record = self.records.get(call_id)
            if record is not None and record.item is not None:
                record.item.refresh_from_record()
        if new:
            items = [CallItem(record) for record in new]
            for record, item in zip(new, items, strict=True):
                record.item = item
            await self.extend(items)
        if follow:
            self.scroll_end(animate=False)


class DetailScreen(ModalScreen[None]):
    """Full request and response of one call (read-only, selectable, copyable)."""

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("escape", "dismiss", "Schließen"),
        Binding("c", "copy", "Kopieren"),
    ]

    DEFAULT_CSS = """
    DetailScreen { align: center middle; }
    DetailScreen #detail { width: 92%; height: 90%; border: thick $primary; background: $surface; }
    DetailScreen #detail Label { padding: 0 1; }
    DetailScreen #detail TextArea { height: 1fr; }
    """

    def __init__(self, record: CallRecord) -> None:
        super().__init__()
        self.record = record
        self.text = record.detail()

    def compose(self) -> ComposeResult:
        with Vertical(id="detail"):
            yield Label(f"Tool-Aufruf #{self.record.call_id}: {self.record.name} – Esc schließt, c kopiert")
            yield TextArea(self.text, read_only=True, show_line_numbers=True, id="detail-text")

    async def action_dismiss(self, result: None = None) -> None:
        self.dismiss(result)

    def action_copy(self) -> None:
        self.app.copy_to_clipboard(self.text)
        self.notify("Anfrage und Antwort in die Zwischenablage kopiert.")
