"""Tests for the FreeCAD Buddy Textual TUI (BuddyApp).

Self-contained: uses fakes for ServerRunner/Bridge instead of the conftest.py
fixtures in this directory, so no headless FreeCAD bridge is ever started.
"""

from __future__ import annotations

import asyncio
from typing import cast

from textual.widgets import Label, RichLog

from buddy_server.config import Settings
from buddy_server.events import BridgeState, Console, EventBus, SessionsChanged, ToolFinished
from buddy_server.runner import ServerRunner
from buddy_server.tui import BuddyApp


class FakeBridge:
    """Stands in for Bridge: same attributes BuddyApp touches, no network."""

    def __init__(self) -> None:
        self.state = "waiting"
        self.freecad_version: str | None = None
        self.reconnect_calls = 0

    def reconnect(self) -> None:
        self.reconnect_calls += 1


class FakeRunner:
    """Stands in for ServerRunner: run() blocks until stop() sets the event."""

    def __init__(self, settings: Settings, bus: EventBus, bridge: FakeBridge | None = None) -> None:
        self.settings = settings
        self.bus = bus
        self.bridge = bridge or FakeBridge()
        self.tool_names: list[str] = []
        self.started = asyncio.Event()
        self.stop_calls = 0
        self._stop_event = asyncio.Event()

    async def run(self) -> None:
        self.started.set()
        await self._stop_event.wait()

    def stop(self) -> None:
        self.stop_calls += 1
        self._stop_event.set()


def _make_app() -> tuple[BuddyApp, FakeRunner]:
    settings = Settings()
    runner = FakeRunner(settings, EventBus())
    # FakeRunner duck-types ServerRunner (same attributes BuddyApp relies on).
    return BuddyApp(settings, cast(ServerRunner, runner)), runner


def _log_text(log: RichLog) -> str:
    return "\n".join(strip.text for strip in log.lines)


def test_bridge_state_updates_status_bar() -> None:
    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test() as pilot:
            runner.bus.publish(BridgeState("connected", "", "1.2.3"))
            await pilot.pause()
            label = app.query_one("#status-bridge", Label)
            assert "verbunden" in str(label.content)
            assert "1.2.3" in str(label.content)

    asyncio.run(scenario())


def test_sessions_changed_updates_status_bar() -> None:
    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test() as pilot:
            runner.bus.publish(SessionsChanged(7))
            await pilot.pause()
            label = app.query_one("#status-sessions", Label)
            assert "7" in str(label.content)

    asyncio.run(scenario())


def test_tool_finished_appears_in_tool_log() -> None:
    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test() as pilot:
            runner.bus.publish(ToolFinished(1, "pad", 0.012, True, "+Pad_Base"))
            await pilot.pause()
            text = _log_text(app.query_one("#tool-log", RichLog))
            assert "pad" in text
            assert "ok" in text
            assert "+Pad_Base" in text

    asyncio.run(scenario())


def test_tool_log_is_capped_and_reconnect_still_works_afterwards() -> None:
    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test() as pilot:
            for i in range(10_000):
                runner.bus.publish(ToolFinished(i, "pad", 0.001, True, "x"))
            await pilot.pause()
            log = app.query_one("#tool-log", RichLog)
            assert len(log.lines) <= 1000

            await pilot.press("r")
            await pilot.pause()
            assert runner.bridge.reconnect_calls == 1

    asyncio.run(scenario())


def test_markup_injection_in_console_text_is_shown_literally() -> None:
    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test() as pilot:
            runner.bus.publish(Console("info", "[red]x[/red]"))
            await pilot.pause()
            text = _log_text(app.query_one("#message-log", RichLog))
            assert "[red]x[/red]" in text

    asyncio.run(scenario())


def test_q_quits_the_app_and_stops_the_runner() -> None:
    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test() as pilot:
            await pilot.press("q")
            await pilot.pause()
        assert runner.stop_calls == 1

    asyncio.run(scenario())
