"""Second reference model "Lüfterrahmen": the reference build reaches the full score over MCP (headless)."""

import asyncio
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

from .conftest import make_settings, mcp_session, running_server, tool_caller

SAMPLE = Path(__file__).resolve().parents[2] / "examples" / "samples" / "luefterrahmen.py"


def _sample() -> ModuleType:
    spec = importlib.util.spec_from_file_location("luefterrahmen", SAMPLE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_reference_build_reaches_the_full_score(bridge_home: tuple[Path, int]) -> None:
    sample = _sample()
    home, bridge_port = bridge_home
    settings = make_settings(home, bridge_port)

    async def scenario() -> dict[str, Any]:
        async with running_server(settings), mcp_session(settings) as session:
            call = tool_caller(session)
            await sample.build(call, view=False)  # headless: no 3D view
            report = await sample.check(call)
            await call("document", action="close", unsaved="discard", document=sample.DOCUMENT)
            return report

    report = asyncio.run(scenario())

    failed = [c for c in report["checks"] if not c["ok"]]
    assert not failed, failed
    passed, total = report["score"].split("/")
    assert passed == total and int(total) >= 15
