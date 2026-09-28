import asyncio
from pathlib import Path

import httpx2
import pytest

from buddy_server.app import build_mcp
from buddy_server.bridge import Bridge, BridgeUnavailable
from buddy_server.cli import format_event, parse_args, settings_from
from buddy_server.events import EventBus, ToolFinished

from .conftest import free_port, make_settings, running_server


def _settings(tmp_path: Path, **overrides: object):
    return make_settings(tmp_path, free_port(), **overrides)


def test_tool_catalogue_is_small_and_documented(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    bus = EventBus()
    mcp, names = build_mcp(settings, Bridge(settings, bus), bus)
    tools = asyncio.run(mcp.list_tools())

    assert len(names) <= 40
    assert "execute_python" not in names
    assert all(tool.description and len(tool.description) > 20 for tool in tools)
    assert {"get_status", "add_profile", "pad", "check_printability", "export_body"} <= set(names)


def test_execute_python_only_with_opt_in(tmp_path: Path) -> None:
    settings = _settings(tmp_path, allow_python=True)
    bus = EventBus()
    _, names = build_mcp(settings, Bridge(settings, bus), bus)

    assert "execute_python" in names
    assert len(names) <= 40


def test_missing_bridge_token_gives_actionable_error(tmp_path: Path) -> None:
    settings = _settings(tmp_path)
    bridge = Bridge(settings, EventBus())

    with pytest.raises(BridgeUnavailable, match="Bridge starten"):
        asyncio.run(bridge.call("system.ping"))
    assert bridge.state == "waiting"


def test_http_requires_token_and_local_host(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    async def scenario() -> tuple[int, int, int]:
        async with running_server(settings), httpx2.AsyncClient() as http:
            body = {"jsonrpc": "2.0", "id": 1, "method": "ping"}
            headers = {"accept": "application/json, text/event-stream"}
            no_token = await http.post(settings.url, json=body, headers=headers)
            wrong = await http.post(
                settings.url, json=body, headers={**headers, "authorization": "Bearer nope"}
            )
            foreign_host = await http.post(
                settings.url,
                json=body,
                headers={
                    **headers,
                    "authorization": f"Bearer {settings.mcp_token()}",
                    "host": "evil.example",
                },
            )
            return no_token.status_code, wrong.status_code, foreign_host.status_code

    no_token, wrong, foreign_host = asyncio.run(scenario())

    assert no_token == 401
    assert wrong == 401
    assert foreign_host in (400, 403, 421)


def test_port_in_use_is_reported(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    async def scenario() -> None:
        async with running_server(settings):
            with pytest.raises(Exception, match="belegt"):
                await running_server(settings).__aenter__()

    asyncio.run(scenario())


def test_cli_parsing_and_event_formatting(tmp_path: Path) -> None:
    args = parse_args(["--port", "9000", "--headless", "--allow-python"])
    settings = settings_from(args)

    assert (settings.port, settings.allow_python, args.headless) == (9000, True, True)
    line = format_event(ToolFinished(1, "pad", 0.012, True, "+Pad_Base"))
    assert line is not None and "pad ok (12 ms) +Pad_Base" in line


def test_claude_command_contains_url_and_token(tmp_path: Path) -> None:
    settings = _settings(tmp_path)

    command = settings.claude_add_command()

    assert settings.url in command and settings.mcp_token() in command
    assert (tmp_path / "mcp-token").read_text(encoding="utf-8").strip() == settings.mcp_token()
