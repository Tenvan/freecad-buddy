"""Tests for the FreeCAD Buddy Textual TUI (BuddyApp).

Self-contained: uses fakes for ServerRunner/Bridge instead of the conftest.py
fixtures in this directory, so no headless FreeCAD bridge is ever started.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Callable
from typing import cast

from textual.widgets import Label, RichLog, Static, TextArea

from buddy_server.chat import CallItem, DetailScreen, ToolChat
from buddy_server.config import Settings
from buddy_server.events import BridgeState, Console, EventBus, SessionsChanged, ToolFinished, ToolStarted
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


async def _wait_for(pilot: object, condition: Callable[[], bool], timeout: float = 5.0) -> None:
    """Poll instead of fixed pauses: batching and mounting take longer on a loaded machine."""
    deadline = time.monotonic() + timeout
    while not condition():
        assert time.monotonic() < deadline, "Bedingung nicht rechtzeitig erfüllt"
        await pilot.pause(0.05)  # type: ignore[attr-defined]


def _mounted(record: object) -> bool:
    item = getattr(record, "item", None)
    return item is not None and item.is_mounted


def _chat(app: BuddyApp) -> ToolChat:
    return app.query_one("#tool-log", ToolChat)


def test_request_and_response_bubbles_with_state_colors() -> None:
    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test(size=(140, 50)) as pilot:
            runner.bus.publish(ToolStarted(1, "pad", '{\n  "sketch": "Sketch_Plate"\n}', "claude-code #1"))
            await pilot.pause(0.2)
            item = _chat(app).records[1].item
            assert item is not None and item.has_class("state-running")
            request = item.query_one(".request", Static)
            assert "pad" in str(request.border_title) and "claude-code #1" in str(request.border_title)

            runner.bus.publish(
                ToolFinished(1, "pad", 0.18, True, "+Pad_Plate", response='{\n  "created": "Pad_Plate"\n}')
            )
            runner.bus.publish(ToolStarted(2, "fillet", "{}", "claude-code #1"))
            runner.bus.publish(
                ToolFinished(2, "fillet", 0.05, True, "ok", ("Radius reduziert",), response="{}")
            )
            runner.bus.publish(ToolStarted(3, "pocket", "{}", "claude-code #1"))
            runner.bus.publish(
                ToolFinished(3, "pocket", 0.02, False, "recompute_failed", response="[recompute_failed] kaputt",
                             error_code="recompute_failed")
            )  # fmt: skip
            records = _chat(app).records
            await _wait_for(pilot, lambda: all(_mounted(records.get(i)) for i in (1, 2, 3)))
            assert [records[i].state for i in (1, 2, 3)] == ["ok", "warning", "error"]
            items = {i: records[i].item for i in (1, 2, 3)}
            assert all(item is not None for item in items.values())
            for i, state in ((1, "ok"), (2, "warning"), (3, "error")):
                assert cast(CallItem, items[i]).has_class(f"state-{state}")
            response = cast(CallItem, items[1]).query_one(".response", Static)
            assert "180 ms" in str(response.border_title)
            assert "Sketch_Plate" in records[1].detail() and "Pad_Plate" in records[1].detail()

    asyncio.run(scenario())


def test_enter_opens_full_detail_and_escape_closes() -> None:
    long_response = "\n".join(f'"line_{i}": {i},' for i in range(500))

    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test(size=(140, 50)) as pilot:
            runner.bus.publish(ToolStarted(1, "get_model_tree", "{}", "claude-code #1"))
            runner.bus.publish(ToolFinished(1, "get_model_tree", 0.3, True, "ok", response=long_response))
            await pilot.pause(0.2)
            chat = _chat(app)
            chat.focus()
            chat.index = 0
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, DetailScreen)
            text = app.screen.query_one("#detail-text", TextArea).text
            assert "line_499" in text and "get_model_tree" in text
            await pilot.press("escape")
            await pilot.pause()
            assert not isinstance(app.screen, DetailScreen)

    asyncio.run(scenario())


def test_v_toggles_compact_list() -> None:
    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test() as pilot:
            runner.bus.publish(ToolFinished(1, "pad", 0.012, True, "+Pad_Base"))
            await pilot.pause(0.2)
            await pilot.press("v")
            assert _chat(app).has_class("compact")
            line = _chat(app).records[1].line().plain
            assert "pad" in line and "ok" in line and "+Pad_Base" in line
            await pilot.press("v")
            assert not _chat(app).has_class("compact")

    asyncio.run(scenario())


def test_tool_chat_is_capped_under_load_and_stays_usable() -> None:
    big = "x" * 50_000

    async def scenario() -> None:
        app, runner = _make_app()
        async with app.run_test() as pilot:
            started = time.monotonic()
            for i in range(10_000):
                runner.bus.publish(ToolStarted(i, "pad", "{}", "s"))
                runner.bus.publish(ToolFinished(i, "pad", 0.001, True, "x", response=big))
            await pilot.pause(0.5)
            chat = _chat(app)
            assert len(chat.records) <= 1000
            assert len(chat.query(CallItem)) <= 1000
            assert 9_999 in chat.records

            await pilot.press("r")
            await pilot.pause()
            assert runner.bridge.reconnect_calls == 1
            assert time.monotonic() - started < 60

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


def test_bubble_json_has_no_background_and_the_hint_is_not_highlighted() -> None:
    from rich.console import Console as RichConsole
    from rich.text import Text

    from buddy_server.chat import _code

    long_json = "{\n" + "\n".join(f'  "k{i}": {i},' for i in range(40)) + "\n}"
    body = _code(long_json)
    assert isinstance(body, Text)
    hint_start = body.plain.index("… (+")
    for span in body.spans:
        style = RichConsole().get_style(span.style) if isinstance(span.style, str) else span.style
        assert style.bgcolor is None
        if span.start >= hint_start:
            assert style.italic and style.dim  # neutral hint, no JSON colours
