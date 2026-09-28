"""AC-14 (automated part): the three reference projects run end to end via MCP (headless FreeCAD)."""

import asyncio
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "examples"))

from reference_projects import PROJECTS

from .conftest import make_settings, mcp_session, running_server, tool_caller


def _run(project: str, bridge_home: tuple[Path, int], out: Path) -> dict[str, Any]:
    home, bridge_port = bridge_home
    settings = make_settings(home, bridge_port)

    async def scenario() -> dict[str, Any]:
        async with running_server(settings), mcp_session(settings) as session:
            return await PROJECTS[project](tool_caller(session), out)

    return asyncio.run(scenario())


def _bodies(tree: dict[str, Any]) -> dict[str, list[str]]:
    return {
        node["label"]: [f["label"] for f in node["features"]]
        for node in tree["objects"]
        if node["type"] == "PartDesign::Body"
    }


@pytest.mark.parametrize("project", sorted(PROJECTS))
def test_reference_project(project: str, bridge_home: tuple[Path, int], tmp_path: Path) -> None:
    summary = _run(project, bridge_home, tmp_path)

    tree = summary["tree"]
    assert tree["label_issues"] == []
    for body, features in _bodies(tree).items():
        assert features, body
        assert all("_" in label for label in features), features
    checks = summary.get("checks") or {"": summary["check"]}
    for name, check in checks.items():
        errors = [issue for issue in check["issues"] if issue["severity"] == "error"]
        assert check["ok"] and not errors, (name, errors)
    exports = summary.get("exports") or {"": summary["export"]}
    for exported in exports.values():
        assert Path(exported["path"]).is_file()
        assert exported["deviation_percent"] < 1
    for node in tree["objects"]:
        for feature in node.get("features", []):
            assert feature["valid"], feature
            if feature["type"] == "Sketcher::SketchObject":
                assert feature["dof"] == 0, feature
