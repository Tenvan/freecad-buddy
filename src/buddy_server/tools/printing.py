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
        """Aktives Druckerprofil (Bauraum, Düse, Mindestwand, Überhangwinkel, Passungsspiel)."""
        return await ctx.call("get_printer_profile", "print.get_profile")

    @tool
    async def set_printer_profile(
        updates: Annotated[dict[str, Any], Field(description="Zu ändernde Profilwerte, z. B. {nozzle: 0.6}")],
    ) -> dict[str, Any]:
        """Druckerprofil ändern (dauerhaft gespeichert)."""
        return await ctx.call("set_printer_profile", "print.set_profile", updates=updates)

    @tool
    async def check_printability(
        target: Annotated[str | None, Field(description="Body/Objekt; leer = einziger Body")] = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Druckbarkeit prüfen: gültiger Solid, Bauraum, Überhänge, Wandstärke, zu kleine Details."""
        return await ctx.call(
            "check_printability", "print.check", timeout=150, target=target, document=document
        )

    @tool
    async def export_body(
        format: Literal["stl", "3mf", "step"] = "3mf",
        target: Annotated[str | None, Field(description="Body/Objekt; leer = einziger Body")] = None,
        path: Annotated[
            str | None, Field(description="Datei oder Ordner; leer = <Dokumentordner>/export")
        ] = None,
        place_on_bed: bool = True,
        overwrite: Annotated[bool, Field(description="Vorhandene Datei überschreiben")] = False,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Bauteil exportieren (auf das Druckbett gelegt) und die Datei per Reimport prüfen."""
        return await ctx.call(
            "export_body", "print.export", timeout=150, format=format, target=target, path=path,
            place_on_bed=place_on_bed, overwrite=overwrite, document=document,
        )  # fmt: skip
