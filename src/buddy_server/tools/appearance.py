"""Material & Ansicht (Appearance): Material, colour, live view and screenshots."""

from __future__ import annotations

import base64
from typing import Annotated, Any, Literal

from mcp.server.mcpserver.utilities.types import Image
from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.tools.base import Doc, Registration

GROUP = Group("appearance", "Appearance", "Material & Ansicht")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def set_material(
        target: Annotated[str, Field(description="Body, part or link label")],
        material: Annotated[
            str | None, Field(description="Library material: 'PLA', 'ABS', 'PETG', a full name or UUID")
        ] = None,
        color: Annotated[
            str | list[float] | None,
            Field(description="Display colour: name (red, yellow, ...), '#RRGGBB' or [r,g,b]"),
        ] = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Assign a FreeCAD library material (density -> mass) and/or the display colour of a body."""
        return await ctx.call(
            "set_material", "appearance.set_material", target=target, material=material, color=color,
            document=document,
        )  # fmt: skip

    @tool
    async def set_view(
        view: Literal[
            "iso", "dimetric", "trimetric", "front", "back", "top", "bottom", "left", "right", "current"
        ] = "iso",
        fit: Annotated[
            bool, Field(description="Alles einpassen, damit das Bauteil komplett sichtbar ist")
        ] = True,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Live-Ansicht in FreeCAD setzen (bleibt so stehen): Standard iso + alles einpassen. Als letzten
        Schritt aufrufen; nach dem ersten Basis-Feature setzt der Server sie selbst (nur mit FreeCAD-GUI)."""
        return await ctx.call("set_view", "view.set", view=view, fit=fit, document=document)

    @tool
    async def screenshot(
        view: Literal[
            "iso", "dimetric", "trimetric", "front", "back", "top", "bottom", "left", "right", "current"
        ] = "iso",
        width: Annotated[int, Field(ge=16, le=1600)] = 800,
        height: Annotated[int, Field(ge=16, le=1600)] = 600,
        fit: bool = True,
        isolate: Annotated[str | None, Field(description="Nur dieses Objekt zeigen")] = None,
        document: Doc = None,
    ) -> Image:
        """Bild der 3D-Ansicht zur visuellen Kontrolle (nur mit laufender FreeCAD-GUI)."""
        result = await ctx.call(
            "screenshot", "view.screenshot", timeout=90, view=view, width=width, height=height, fit=fit,
            isolate=isolate, document=document,
        )  # fmt: skip
        return Image(data=base64.b64decode(result["data"]), format="png")
