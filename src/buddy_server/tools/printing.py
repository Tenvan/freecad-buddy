"""3D-Druck (Print): Printer profile, printability check and export."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.tools.base import Doc, Registration

GROUP = Group("printing", "Print", "3D-Druck")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def get_printer_profile() -> dict[str, Any]:
        """Active printer profile (build volume, nozzle, minimum wall, overhang angle, fit clearance)."""
        return await ctx.call("get_printer_profile", "print.get_profile")

    @tool
    async def set_printer_profile(
        updates: Annotated[dict[str, Any], Field(description="Profile values to change, e.g. {nozzle: 0.6}")],
    ) -> dict[str, Any]:
        """Change the printer profile (stored permanently)."""
        return await ctx.call("set_printer_profile", "print.set_profile", updates=updates)

    @tool
    async def check_printability(
        target: Annotated[str | None, Field(description="Body/object; empty = the only body")] = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Check printability: valid solid, build volume, overhangs, wall thickness, too small details."""
        return await ctx.call(
            "check_printability", "print.check", timeout=150, target=target, document=document
        )

    @tool
    async def export_body(
        format: Literal["stl", "3mf", "step"] = "3mf",
        target: Annotated[str | None, Field(description="Body/object; empty = the only body")] = None,
        path: Annotated[
            str | None, Field(description="File or folder; empty = <document folder>/export")
        ] = None,
        place_on_bed: bool = True,
        overwrite: Annotated[bool, Field(description="Overwrite an existing file")] = False,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Export the part (placed on the print bed) and verify the file by re-importing it."""
        return await ctx.call(
            "export_body", "print.export", timeout=150, format=format, target=target, path=path,
            place_on_bed=place_on_bed, overwrite=overwrite, document=document,
        )  # fmt: skip
