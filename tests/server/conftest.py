import asyncio
import contextlib
import json
import socket
import sys
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from pathlib import Path
from typing import Any

import httpx2
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from buddy_server.config import Settings
from buddy_server.events import EventBus
from buddy_server.runner import ServerRunner
from freecad_env import start_headless_bridge


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


@pytest.fixture(scope="session")
def bridge_home(tmp_path_factory: pytest.TempPathFactory) -> Iterator[tuple[Path, int]]:
    """A headless FreeCAD bridge for the whole test session (FreeCAD 26.3 without GUI)."""
    home = tmp_path_factory.mktemp("buddy-home")
    process = start_headless_bridge(port=0, extra_env={"FREECAD_BUDDY_HOME": str(home)})
    assert process.stdout is not None
    port = None
    for _ in range(200):
        line = process.stdout.readline()
        if line.startswith("BRIDGE_READY"):
            port = int(line.split()[1])
            break
        if not line and process.poll() is not None:
            break
    if port is None:
        process.kill()
        pytest.fail("Headless-Bridge ist nicht gestartet")
    yield home, port
    assert process.stdin is not None
    process.stdin.close()
    try:
        process.wait(timeout=10)
    except Exception:
        process.kill()


def make_settings(home: Path, bridge_port: int, **overrides: Any) -> Settings:
    settings = Settings(port=free_port(), bridge_port=bridge_port, home=home, watchdog_interval=0.5)
    for key, value in overrides.items():
        setattr(settings, key, value)
    return settings


@contextlib.asynccontextmanager
async def running_server(settings: Settings) -> AsyncIterator[ServerRunner]:
    runner = ServerRunner(settings, EventBus())
    task = asyncio.create_task(runner.run())
    started = asyncio.create_task(runner.started.wait())
    await asyncio.wait({task, started}, timeout=15, return_when=asyncio.FIRST_COMPLETED)
    if task.done():
        started.cancel()
        task.result()  # re-raises the startup error (e.g. PortInUse)
    try:
        yield runner
    finally:
        runner.stop()
        await asyncio.wait_for(task, 15)


@contextlib.asynccontextmanager
async def mcp_session(settings: Settings, token: str | None = None) -> AsyncIterator[ClientSession]:
    headers = {"Authorization": f"Bearer {token or settings.mcp_token()}"}
    async with (
        httpx2.AsyncClient(headers=headers, timeout=httpx2.Timeout(30, read=300)) as http,
        streamable_http_client(settings.url, http_client=http) as streams,
        ClientSession(streams[0], streams[1]) as session,
    ):
        await session.initialize()
        yield session


Call = Callable[..., Awaitable[Any]]


def tool_caller(session: ClientSession) -> Call:
    """``await call("pad", sketch=...)`` → parsed JSON result; raises AssertionError on tool errors."""

    async def call(tool: str, /, **arguments: Any) -> Any:
        result = await session.call_tool(tool, arguments)
        text = "\n".join(getattr(block, "text", "") for block in result.content)
        if result.is_error:
            raise AssertionError(f"{tool} fehlgeschlagen: {text}")
        if result.structured_content is not None:
            content = result.structured_content
            return content.get("result", content) if set(content) == {"result"} else content
        return json.loads(text) if text else None

    return call
