"""AC-05 (proposal list) and AC-11 (fill_pattern over MCP)."""

import asyncio
import json
from pathlib import Path

from buddy_server.events import DesignToolProposed
from buddy_server.proposals import ProposalStore

from .conftest import make_settings, mcp_session, running_server, tool_caller


def test_proposals_with_the_same_name_are_merged_and_counted(tmp_path: Path) -> None:
    store = ProposalStore(tmp_path / "proposals.json")

    store.propose("Screw Boss", "bosses in housings", ["diameter"], ["pad", "pocket"], "screw_boss(d=7)")
    entry = store.propose("screw_boss", "bosses in lids", ["diameter", "height"], [], "screw_boss(d=7)")

    assert [p["name"] for p in store.all()] == ["screw_boss"]
    assert entry["count"] == 2
    assert entry["problems"] == ["bosses in housings", "bosses in lids"]
    assert entry["inputs"] == ["diameter", "height"] and entry["steps"] == ["pad", "pocket"]
    assert entry["examples"] == ["screw_boss(d=7)"]
    assert json.loads((tmp_path / "proposals.json").read_text(encoding="utf-8"))[0]["count"] == 2


def test_fill_pattern_and_proposals_over_mcp(bridge_home: tuple[Path, int]) -> None:
    home, bridge_port = bridge_home
    settings = make_settings(home, bridge_port)
    events: list[object] = []

    async def scenario() -> tuple[dict, dict, dict]:
        async with running_server(settings) as runner:
            runner.bus.subscribe(events.append)
            async with mcp_session(settings) as session:
                call = tool_caller(session)
                await call("document", action="new", name="E2E Sieve")
                await call("set_parameters", parameters={"Plate_Thickness": 2})
                await call("create_body", label="Plate")
                await call("create_sketch", plane="XY", purpose="Plate")
                await call(
                    "add_profile",
                    sketch="Sketch_Plate",
                    kind="rectangle",
                    params={"width": 110, "height": 90},
                )
                await call("pad", sketch="Sketch_Plate", length="Plate_Thickness", purpose="Plate")
                grid = await call(
                    "fill_pattern", size=1, pitch=3, count=[34, 27], offset="Plate_Thickness", name="Sieve"
                )
                await call("propose_design_tool", name="snap_hook", problem="clips on lids", inputs=["width"],
                           steps=["create_sketch", "pad"], example="snap_hook(width=8)")  # fmt: skip
                again = await call("propose_design_tool", name="snap_hook", problem="clips on boxes",
                                   inputs=["length"], steps=[], example="snap_hook(width=8)")  # fmt: skip
                listed = await call("list_design_tool_proposals")
                return grid, again, listed

    grid, again, listed = asyncio.run(scenario())

    assert grid["cells"] == 918 and grid["feature"]["label"] == "Grid_Sieve"
    assert again["merged"] and again["proposal"]["count"] == 2
    assert next(p for p in listed["proposals"] if p["name"] == "snap_hook")["count"] == 2
    proposed = [e for e in events if isinstance(e, DesignToolProposed)]
    assert [(e.name, e.count) for e in proposed] == [("snap_hook", 1), ("snap_hook", 2)]
