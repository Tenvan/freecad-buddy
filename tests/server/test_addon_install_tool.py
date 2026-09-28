"""AC-08/AC-09 (server side): opt-in, pre-checks and the double opt-in against a headless bridge."""

import asyncio
import json
import shutil
import time
from pathlib import Path
from typing import Any

import pytest

from buddy_server import addon_catalog, addon_service
from buddy_server.app import build_mcp
from buddy_server.bridge import Bridge
from buddy_server.config import Settings
from buddy_server.events import EventBus
from buddy_server.tools import _install_blocker

from .conftest import make_settings, mcp_session, running_server

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "addon_catalog"


def _tool_names(**overrides: Any) -> set[str]:
    settings = Settings(**overrides)
    bus = EventBus()
    _, names = build_mcp(settings, Bridge(settings, bus), bus)
    return set(names)


def test_install_addon_exists_only_with_the_server_opt_in() -> None:
    assert "install_addon" not in _tool_names(allow_addon_install=False)
    assert "install_addon" in _tool_names(allow_addon_install=True)


@pytest.fixture(scope="module")
def entries() -> dict[str, addon_catalog.AddonEntry]:
    return {entry.id: entry for entry in addon_catalog.load_cache(FIXTURE)}


STATUS = {"freecad_version": [26, 3, 0], "addons": ["Gridfinity"], "macros": ["Macro_Foto.FCMacro"]}


@pytest.mark.parametrize(
    ("addon_id", "reason"),
    [
        ("lattice2", None),
        ("FCHoneycombMaker", None),
        ("Gridfinity", "already installed"),
        ("btl", "not compatible"),
        ("parts_library", "git only"),
    ],
)
def test_install_blockers(
    entries: dict[str, addon_catalog.AddonEntry], addon_id: str, reason: str | None
) -> None:
    blocker = _install_blocker(entries[addon_id], STATUS)
    assert (blocker is None) if reason is None else (blocker is not None and reason in blocker)


def test_python_dependencies_block_the_install(entries: dict[str, addon_catalog.AddonEntry]) -> None:
    btl = entries["btl"]
    blocker = _install_blocker(btl, {**STATUS, "freecad_version": [1, 0, 0]})  # compatible version
    assert blocker is not None and "Python packages" in blocker


def _seed_cache(home: Path) -> None:
    target = home / "addon-catalog"
    target.mkdir(parents=True, exist_ok=True)
    for member in addon_service.CACHES:
        shutil.copy(FIXTURE / member, target / member)
    (target / "catalog-meta.json").write_text(json.dumps({"fetched_at": time.time()}), encoding="utf-8")


def test_double_opt_in_over_mcp(bridge_home: tuple[Path, int]) -> None:
    """Server opt-in alone is not enough: the headless bridge has no FreeCAD opt-in (and no GUI)."""
    home, bridge_port = bridge_home
    _seed_cache(home)
    settings = make_settings(home, bridge_port, allow_addon_install=True)

    async def scenario() -> None:
        async with running_server(settings), mcp_session(settings) as session:
            blocked = await session.call_tool("install_addon", {"addon_id": "btl"})
            assert blocked.is_error and "[validation]" in blocked.content[0].text  # type: ignore[union-attr]

            refused = await session.call_tool("install_addon", {"addon_id": "lattice2", "wait_seconds": 0})
            text = refused.content[0].text  # type: ignore[union-attr]
            assert refused.is_error and "method_not_found" in text

    asyncio.run(scenario())
