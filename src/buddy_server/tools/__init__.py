"""MCP tools of FreeCAD Buddy - one module per working phase (tool group).

Each tool forwards to one bridge method. Tool descriptions are written for the agent: they state
the intended modelling workflow, so the model stays PartDesign-first and editable by a human.
The group of a tool is the module that registers it; its description starts with ``[<Category>]``.
"""

from __future__ import annotations

from typing import Any, cast

from buddy_server import catalog
from buddy_server.catalog import Group
from buddy_server.tools import (
    appearance,
    assembly,
    design,
    expert,
    feature,
    model,
    printing,
    reference,
    rules,
    session,
    sketch,
)
from buddy_server.tools.base import NameCollector, Registration, ToolContext, ToolRegistrar

__all__ = ["MODULES", "NameCollector", "ToolContext", "ToolRegistrar", "register_tools", "tool_groups"]

MODULES = (session, model, sketch, reference, feature, design, assembly, appearance, printing, rules, expert)
"""Tool modules in working-phase order (the order of ``docs/tools.md``)."""


def register_tools(
    mcp: ToolRegistrar, ctx: ToolContext, allow_python: bool, allow_addon_install: bool = False
) -> list[str]:
    names: list[str] = []
    for module in MODULES:

        def tool(fn: Any, group: Group = module.GROUP) -> Any:
            names.append(fn.__name__)
            fn.__doc__ = catalog.describe(group, fn.__doc__ or "")
            return mcp.tool()(fn)

        module.register(Registration(tool, ctx, names, allow_python, allow_addon_install))
    return names


def tool_groups(allow_python: bool = True, allow_addon_install: bool = True) -> list[tuple[Group, list[str]]]:
    """Groups with their tool names in registration order (for docs and tests; nothing is called)."""
    groups: list[tuple[Group, list[str]]] = []
    for module in MODULES:
        names: list[str] = []

        def collect(fn: Any, names: list[str] = names) -> Any:
            names.append(fn.__name__)
            return fn

        module.register(
            Registration(collect, cast(ToolContext, None), names, allow_python, allow_addon_install)
        )
        groups.append((module.GROUP, names))
    return groups
