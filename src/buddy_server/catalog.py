"""Tool groups by working phase. Each module in ``buddy_server.tools`` declares its ``GROUP``.

MCP lists tools flat; the ``[<Category>]`` prefix in every description lets the agent see the group.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Group:
    key: str
    prefix: str
    """English category shown to the agent as ``[prefix]`` in front of the tool description."""
    title: str
    """German heading in ``docs/tools.md``."""


def describe(group: Group, description: str) -> str:
    """Description with the category prefix (idempotent)."""
    prefix = f"[{group.prefix}] "
    text = description.strip()
    return text if text.startswith(prefix) else prefix + text
