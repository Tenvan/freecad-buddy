"""Regression: pressing q in the TUI with a real server, bridge and MCP client must exit promptly."""

import asyncio
import time
from pathlib import Path

from buddy_server.events import EventBus
from buddy_server.runner import ServerRunner
from buddy_server.tui import BuddyApp

from .conftest import make_settings, mcp_session, tool_caller


def test_q_exits_promptly_with_real_server_and_client(bridge_home: tuple[Path, int]) -> None:
    home, bridge_port = bridge_home
    settings = make_settings(home, bridge_port)

    async def scenario() -> float:
        app = BuddyApp(settings, ServerRunner(settings, EventBus()))
        async with app.run_test() as pilot:
            await asyncio.wait_for(app.runner.started.wait(), 15)
            async with mcp_session(settings) as session:
                await tool_caller(session)("get_status")
                await asyncio.sleep(3.5)  # watchdog pings the bridge in the meantime
                started = time.monotonic()
                await pilot.press("q")
                await asyncio.wait_for(_until_exit(app), 20)
                return time.monotonic() - started

    return_value = asyncio.run(asyncio.wait_for(scenario(), 60))
    assert return_value < 5


async def _until_exit(app: BuddyApp) -> None:
    while app.is_running:
        await asyncio.sleep(0.05)
