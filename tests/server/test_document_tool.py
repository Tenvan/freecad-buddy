"""AC-14 (freecad-buddy-referenzen): document(action=...) reports missing required values readably."""

import asyncio
from pathlib import Path

import pytest

from buddy_server.app import build_mcp
from buddy_server.bridge import Bridge
from buddy_server.config import Settings
from buddy_server.events import EventBus


@pytest.mark.parametrize(
    ("arguments", "missing"), [({"action": "new"}, "name"), ({"action": "open"}, "path")]
)
def test_missing_required_value_is_a_readable_tool_error(
    tmp_path: Path, arguments: dict[str, str], missing: str
) -> None:
    settings = Settings(home=tmp_path)
    bus = EventBus()
    mcp, _ = build_mcp(settings, Bridge(settings, bus), bus)

    with pytest.raises(Exception) as info:  # raised before the bridge is contacted
        asyncio.run(mcp.call_tool("document", arguments))

    assert f"needs '{missing}'" in str(info.value)
    assert "[validation]" in str(info.value)
