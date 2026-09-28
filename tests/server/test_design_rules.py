"""AC-01 to AC-04: design rulebook, compact instructions, tool, resource and prompt from one source."""

import asyncio
import re
from pathlib import Path

import pytest

from buddy_server import design_rules
from buddy_server.app import build_mcp
from buddy_server.bridge import Bridge
from buddy_server.config import Settings
from buddy_server.events import EventBus

from .conftest import make_settings, mcp_session, running_server, tool_caller

_IDENTIFIER = re.compile(r"\b[a-z]+(?:_[a-z]+)+\b")


def _registered(allow_python: bool = False) -> tuple[str, set[str]]:
    settings = Settings(allow_python=allow_python)
    bus = EventBus()
    mcp, names = build_mcp(settings, Bridge(settings, bus), bus)
    return mcp.instructions or "", set(names)


def test_instructions_are_compact_and_complete() -> None:
    instructions, names = _registered()

    assert len(instructions) <= design_rules.INSTRUCTIONS_BUDGET
    assert "get_design_rules" in names
    assert "get_design_rules(topic)" in instructions
    assert "Wiederkehrend-komplex" in instructions  # AC-04: design-tool rule is a core rule
    for rule in (r for t in design_rules.TOPICS for r in t.rules if r.core and not r.requires):
        assert rule.text.format_map(design_rules.profile_values(None)) in instructions


def test_instructions_stay_in_budget_with_every_planned_tool() -> None:
    assert len(design_rules.build_instructions(None)) <= design_rules.INSTRUCTIONS_BUDGET


def _profile_kinds() -> set[str]:
    """Profile kinds of add_profile (e.g. u_path) are valid identifiers in the rules, too."""
    settings = Settings()
    bus = EventBus()
    mcp, _ = build_mcp(settings, Bridge(settings, bus), bus)
    tools = {tool.name: tool for tool in asyncio.run(mcp.list_tools())}
    return set(tools["add_profile"].input_schema["properties"]["kind"]["enum"])


@pytest.mark.parametrize("allow_python", [False, True])
def test_rules_only_name_registered_tools(allow_python: bool) -> None:
    instructions, names = _registered(allow_python)
    text = instructions + design_rules.render_all(None, names)

    mentioned = set(_IDENTIFIER.findall(text)) - set(design_rules.TOPIC_KEYS) - _profile_kinds()
    assert mentioned <= names, sorted(mentioned - names)
    assert ("execute_python" in text) == allow_python


def test_every_topic_of_r03_is_covered() -> None:
    expected = {"workflow", "parameters", "sketches", "references", "features", "naming", "printing"}
    expected |= {"design_tools", "addons", "assembly"}
    assert set(design_rules.TOPIC_KEYS) == expected
    assert all(topic.rules for topic in design_rules.TOPICS)


def test_printing_numbers_follow_the_profile() -> None:
    default = design_rules.render_topic("printing")
    coarse = design_rules.render_topic("printing", {"nozzle": 0.6, "clearance_fit": 0.3})

    assert "Düse 0.4 mm" in default and "tragende Wände ≥ 1.6 mm" in default and "M3 → 3.4 mm" in default
    assert "Düse 0.6 mm" in coarse and "tragende Wände ≥ 2.4 mm" in coarse and "M3 → 3.6 mm" in coarse


def test_topics_that_need_missing_tools_are_hidden() -> None:
    names = {"get_design_rules", "pad"}
    keys = [topic.key for topic in design_rules.visible_topics(names)]

    assert "addons" not in keys
    with pytest.raises(KeyError):
        design_rules.render_topic("addons", None, names)
    assert "hole_grid" not in design_rules.render_topic("design_tools", None, names)
    assert "hole_grid" in design_rules.render_topic("design_tools", None, names | {"hole_grid"})


def test_tool_resource_and_prompt_over_mcp(bridge_home: tuple[Path, int]) -> None:
    home, bridge_port = bridge_home
    settings = make_settings(home, bridge_port)

    async def scenario() -> None:
        async with running_server(settings), mcp_session(settings) as session:
            call = tool_caller(session)
            overview = await call("get_design_rules")
            assert "printing:" in overview and "sketches:" in overview

            printing = await call("get_design_rules", topic="printing")
            assert printing == design_rules.render_topic(
                "printing", _profile(await call("get_printer_profile")), _names(await session.list_tools())
            )

            result = await session.call_tool("get_design_rules", {"topic": "nonsense"})
            assert result.is_error
            assert "[validation]" in result.content[0].text  # type: ignore[union-attr]

            templates = await session.list_resource_templates()
            assert any(t.uri_template == "buddy://design-rules/{topic}" for t in templates.resource_templates)
            read = await session.read_resource("buddy://design-rules/sketches")
            assert "Symmetrie" in read.contents[0].text  # type: ignore[union-attr]

            prompt = await session.get_prompt("human_modeling_guide")
            assert "## 3D-Druck (FDM) (printing)" in prompt.messages[0].content.text  # type: ignore[union-attr]

    asyncio.run(scenario())


def _profile(result: dict) -> dict:
    return {key: value for key, value in result.items() if key != "path"}


def _names(tools: object) -> set[str]:
    return {tool.name for tool in tools.tools}  # type: ignore[attr-defined]


def test_view_rule_is_first_core_rule_after_reading_the_tree() -> None:
    instructions, names = _registered()

    assert "set_view" in names
    assert "Nach dem ersten Basis-Feature" in instructions and "letzter Schritt set_view" in instructions
    assert instructions.index("get_model_tree lesen") < instructions.index("set_view")
