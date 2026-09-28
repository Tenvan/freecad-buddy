"""Experte (Expert): Escape hatch: Python in FreeCAD (opt-in)."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.tools.base import Doc, Registration

GROUP = Group("expert", "Expert", "Experte")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    if reg.allow_python:

        @tool
        async def execute_python(
            code: Annotated[str, Field(description="Python-Code; Variable 'result' wird zurückgegeben")],
            document: Doc = None,
        ) -> dict[str, Any]:
            """Notausgang (nur mit FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD als ein Undo-Schritt."""
            return await ctx.call(
                "execute_python", "python.execute", timeout=150, code=code, document=document
            )
