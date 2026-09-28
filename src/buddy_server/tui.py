"""Textual terminal UI for the FreeCAD Buddy MCP server.

Runs the server (via ``ServerRunner``) as a Textual worker inside the app's own
asyncio loop and renders the events published on its ``EventBus``.
"""

from __future__ import annotations

import contextlib
import time
from typing import ClassVar

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Footer, Header, Label, RichLog
from textual.worker import Worker

from buddy_server.config import Settings
from buddy_server.events import (
    BridgeState,
    Console,
    Event,
    EventBus,
    ServerFailed,
    ServerStarted,
    SessionsChanged,
    ToolFinished,
)
from buddy_server.runner import ServerRunner

MAX_LOG_LINES = 1000

_BRIDGE_LABELS = {"connected": "verbunden", "waiting": "wartet", "error": "Fehler"}
_BRIDGE_CLASSES = {"connected": "state-connected", "waiting": "state-waiting", "error": "state-error"}


class BusEvent(Message):
    """Carries a server-side ``Event`` from a worker thread into the UI thread.

    The ``EventBus`` subscriber may run on a thread pool thread (e.g. bridge status
    updates from ``asyncio.to_thread``), so it must only hand the event over via
    ``post_message`` (thread-safe) instead of touching widgets directly.
    """

    def __init__(self, event: Event) -> None:
        self.event = event
        super().__init__()


class BuddyApp(App[None]):
    """Terminal front end for the FreeCAD Buddy MCP server."""

    TITLE = "FreeCAD Buddy"

    CSS = """
    #status-bar {
        height: 1;
        background: $panel;
        padding: 0 1;
    }
    #status-bar Label {
        margin-right: 2;
    }
    .state-connected { color: $success; text-style: bold; }
    .state-waiting { color: $warning; text-style: bold; }
    .state-error { color: $error; text-style: bold; }
    #panels { height: 1fr; }
    #tool-log, #message-log {
        width: 100%;
        border: round $primary;
    }
    #tool-log { height: 3fr; }
    #message-log { height: 2fr; }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("r", "reconnect", "Neu verbinden"),
        Binding("c", "copy_claude_command", "Claude-Befehl kopieren"),
        Binding("p", "toggle_python", "execute_python umschalten"),
        Binding("q", "quit_app", "Beenden"),
    ]

    def __init__(self, settings: Settings, runner: ServerRunner | None = None) -> None:
        super().__init__()
        self.settings = settings
        self.runner = runner or ServerRunner(settings, EventBus())
        self._session_count = 0
        self._server_worker: Worker[None] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="status-bar"):
            yield Label("Bridge: wartet", id="status-bridge", classes="state-waiting")
            yield Label(f"MCP: {self.settings.url}", id="status-endpoint")
            yield Label("Sessions: 0", id="status-sessions")
            yield Label(self._python_label_text(), id="status-python")
        with Vertical(id="panels"):
            yield RichLog(id="tool-log", max_lines=MAX_LOG_LINES, markup=False)
            yield RichLog(id="message-log", max_lines=MAX_LOG_LINES, markup=False)
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#tool-log", RichLog).border_title = "Tool-Aufrufe"
        self.query_one("#message-log", RichLog).border_title = "Meldungen"
        self.runner.bus.subscribe(lambda event: self.post_message(BusEvent(event)))
        self._start_server_worker(self.runner)

    def _python_label_text(self) -> str:
        return f"execute_python: {'an' if self.settings.allow_python else 'aus'}"

    def _start_server_worker(self, runner: ServerRunner) -> None:
        self._server_worker = self.run_worker(
            self._serve(runner), exclusive=True, group="server", exit_on_error=False
        )

    async def _serve(self, runner: ServerRunner) -> None:
        try:
            await runner.run()
        except Exception as error:  # a crashing worker must never take the TUI down with it
            runner.bus.publish(Console("error", f"Server beendet: {error}"))

    # -- event handling -----------------------------------------------------

    def on_bus_event(self, message: BusEvent) -> None:
        event = message.event
        match event:
            case BridgeState():
                self._handle_bridge_state(event)
            case SessionsChanged():
                self._session_count = event.count
                self.query_one("#status-sessions", Label).update(f"Sessions: {self._session_count}")
            case ServerStarted():
                self._set_endpoint_ok()
                allow = "an" if event.allow_python else "aus"
                self._write_message(event.at, f"MCP-Server bereit: {event.url} (execute_python: {allow})")
            case ServerFailed():
                self._set_endpoint_failed(event.message)
                self._write_message(event.at, f"FEHLER: {event.message}", error=True)
            case ToolFinished():
                self._write_tool_line(event)
            case Console():
                self._write_message(
                    event.at, event.text, error=event.level == "error", warning=event.level == "warning"
                )

    def _handle_bridge_state(self, event: BridgeState) -> None:
        label = self.query_one("#status-bridge", Label)
        version = f" (FreeCAD {event.freecad_version})" if event.freecad_version else ""
        label.update(f"Bridge: {_BRIDGE_LABELS.get(event.state, event.state)}{version}")
        label.set_classes(_BRIDGE_CLASSES.get(event.state, ""))
        if event.message:
            self._write_message(
                event.at,
                f"Bridge: {event.message}",
                error=event.state == "error",
                warning=event.state == "waiting",
            )

    def _set_endpoint_ok(self) -> None:
        label = self.query_one("#status-endpoint", Label)
        label.update(f"MCP: {self.settings.url}")
        label.set_classes("")

    def _set_endpoint_failed(self, message: str) -> None:
        label = self.query_one("#status-endpoint", Label)
        label.update(f"MCP: {self.settings.url} - FEHLER: {message}")
        label.set_classes("state-error")

    def _write_tool_line(self, event: ToolFinished) -> None:
        stamp = time.strftime("%H:%M:%S", time.localtime(event.at))
        status = "ok" if event.ok else "FEHLER"
        line = f"{stamp}  {event.name}  {status}  {event.duration * 1000:.0f} ms  {event.summary}"
        log = self.query_one("#tool-log", RichLog)
        if event.ok:
            log.write(line)
        else:
            color = self.get_css_variables()["error"]
            log.write(Text(line, style=f"bold {color}"))

    def _write_message(self, at: float, text: str, *, error: bool = False, warning: bool = False) -> None:
        stamp = time.strftime("%H:%M:%S", time.localtime(at))
        line = f"{stamp}  {text}"
        log = self.query_one("#message-log", RichLog)
        if error or warning:
            variables = self.get_css_variables()
            color = variables["error"] if error else variables["warning"]
            log.write(Text(line, style=f"bold {color}"))
        else:
            log.write(line)

    # -- key bindings ---------------------------------------------------------

    def action_reconnect(self) -> None:
        # Bridge.reconnect() itself publishes a BridgeState event, which is how the
        # requested "+ Meldung" ends up in the Meldungen panel.
        self.runner.bridge.reconnect()

    def action_copy_claude_command(self) -> None:
        # The command carries the MCP bearer token: never write it into a log widget.
        self.copy_to_clipboard(self.settings.claude_add_command())
        self.notify("Claude-Befehl in die Zwischenablage kopiert.", title="Zwischenablage")

    async def action_toggle_python(self) -> None:
        old_runner = self.runner
        old_runner.stop()
        if self._server_worker is not None:
            with contextlib.suppress(Exception):
                await self._server_worker.wait()
        self.settings.allow_python = not self.settings.allow_python
        self.query_one("#status-python", Label).update(self._python_label_text())
        self.runner = ServerRunner(self.settings, old_runner.bus, bridge=old_runner.bridge)
        self._start_server_worker(self.runner)

    async def action_quit_app(self) -> None:
        self.runner.stop()
        if self._server_worker is not None:
            with contextlib.suppress(Exception):
                await self._server_worker.wait()
        self.exit()
