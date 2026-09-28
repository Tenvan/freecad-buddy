"""Modell & Parameter (Model): Bodies, model tree, objects and central parameters."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.tools.base import Doc, Registration

GROUP = Group("model", "Model", "Modell & Parameter")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def get_model_tree(document: Doc = None) -> dict[str, Any]:
        """Modellbaum lesen: Bodies mit Features in Reihenfolge, Gültigkeit, DoF der Skizzen, Undo-Liste und
        Label-Probleme. Vor Änderungen aufrufen – der Nutzer kann parallel in FreeCAD arbeiten."""
        return await ctx.call("get_model_tree", "document.tree", document=document)

    @tool
    async def get_object(
        ref: Annotated[str, Field(description="Objektname oder Label")], document: Doc = None
    ) -> dict[str, Any]:
        """Details eines Objekts: Status, Expressions, bei Skizzen die Analyse, bei Körpern Volumen und Maße."""
        return await ctx.call("get_object", "document.object", ref=ref, document=document)

    @tool
    async def delete_object(
        ref: Annotated[str, Field(description="Objektname oder Label")], document: Doc = None
    ) -> dict[str, Any]:
        """Objekt löschen (ein Undo-Schritt)."""
        return await ctx.call("delete_object", "document.delete", ref=ref, document=document)

    @tool
    async def set_parameters(
        parameters: Annotated[
            dict[str, Any],
            Field(
                description="Name → Wert oder {value, type, description}; type: length (Standard), distance, "
                "angle, integer, float, bool. Namen englisch/ASCII, z. B. Box_Width."
            ),
        ],
        document: Doc = None,
    ) -> dict[str, Any]:
        """Zentrale Parameter im VarSet 'Parameters' anlegen/ändern. Maße in Skizzen und Features können den
        Parameternamen statt einer Zahl nutzen – so bleibt das Modell in FreeCAD per Parameter änderbar."""
        return await ctx.call("set_parameters", "parameters.set", parameters=parameters, document=document)

    @tool
    async def list_parameters(document: Doc = None) -> list[dict[str, Any]]:
        """Alle Parameter mit Typ, Wert und Expression-Referenz."""
        return await ctx.call("list_parameters", "parameters.list", document=document)

    @tool
    async def create_body(
        label: Annotated[str, Field(description="Bauteilname, z. B. 'Box' oder 'Lid'")], document: Doc = None
    ) -> dict[str, Any]:
        """PartDesign-Body für ein Bauteil anlegen (ein Body = ein druckbares Teil)."""
        return await ctx.call("create_body", "body.create", label=label, document=document)
