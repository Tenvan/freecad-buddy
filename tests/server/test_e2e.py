"""End to end: MCP client → HTTP (token) → freecad-buddy → bridge → FreeCAD 26.3 (headless)."""

import asyncio
from pathlib import Path

from buddy_server.events import SessionsChanged, ToolFinished

from .conftest import make_settings, mcp_session, running_server, tool_caller


def test_status_and_box_workflow(bridge_home: tuple[Path, int], tmp_path: Path) -> None:
    home, bridge_port = bridge_home
    settings = make_settings(home, bridge_port)
    events: list[object] = []

    async def scenario() -> dict:
        async with running_server(settings) as runner:
            runner.bus.subscribe(events.append)
            async with mcp_session(settings) as session:
                call = tool_caller(session)
                status = await call("get_status")
                assert status["freecad"]["version"].startswith("26.3")
                assert status["missing_types"] == []

                await call("document", action="new", name="E2E Box")
                await call("set_parameters", parameters={"Box_Width": 60, "Box_Depth": 40, "Box_Height": 20})
                await call("create_body", label="Box")
                sketch = await call("create_sketch", plane="XY", purpose="Base")
                profile = await call(
                    "add_profile",
                    sketch=sketch["sketch"]["label"],
                    kind="rectangle",
                    params={"width": "Box_Width", "height": "Box_Depth"},
                )
                assert profile["sketch"]["dof"] == 0
                pad = await call("pad", sketch="Sketch_Base", length="Box_Height", purpose="Base")
                assert abs(pad["volume"] - 60 * 40 * 20) < 1e-6
                await call("fillet", selector="edges:vertical", radius=3)
                await call("shell", selector="face:top", thickness=2)
                check = await call("check_printability")
                assert check["ok"], check["issues"]
                exported = await call("export_body", format="3mf", path=str(tmp_path))
                assert Path(exported["path"]).is_file()
                tree = await call("get_model_tree")
                return tree

    tree = asyncio.run(scenario())

    body = next(node for node in tree["objects"] if node["type"] == "PartDesign::Body")
    assert [f["label"] for f in body["features"]] == [
        "Sketch_Base",
        "Pad_Base",
        "Fillet_Vertical",
        "Shell_Top",
    ]
    assert tree["label_issues"] == []
    finished = [e for e in events if isinstance(e, ToolFinished)]
    assert finished and all(e.ok for e in finished)
    assert any(isinstance(e, SessionsChanged) and e.count == 1 for e in events)


def test_tool_errors_are_readable(bridge_home: tuple[Path, int]) -> None:
    home, bridge_port = bridge_home
    settings = make_settings(home, bridge_port)

    async def scenario() -> str:
        async with running_server(settings), mcp_session(settings) as session:
            await session.call_tool("document", {"action": "new", "name": "E2E Errors"})
            result = await session.call_tool("pad", {"sketch": "DoesNotExist"})
            assert result.is_error
            return "\n".join(getattr(block, "text", "") for block in result.content)

    text = asyncio.run(scenario())

    assert "[not_found]" in text


def test_unreachable_bridge_answers_fast(tmp_path: Path) -> None:
    (tmp_path / "bridge-token").write_text("x", encoding="utf-8")
    settings = make_settings(tmp_path, bridge_port=1)  # nothing listens there

    async def scenario() -> tuple[bool, str, float]:
        async with running_server(settings), mcp_session(settings) as session:
            loop = asyncio.get_running_loop()
            started = loop.time()
            result = await session.call_tool("get_status", {})
            text = "\n".join(getattr(block, "text", "") for block in result.content)
            return result.is_error, text, loop.time() - started

    is_error, text, duration = asyncio.run(scenario())

    assert is_error and "[bridge_unavailable]" in text
    assert duration <= 10
