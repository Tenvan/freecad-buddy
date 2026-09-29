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
        """Read the model tree: bodies with features in order, validity, sketch DoF, undo list and label
        issues. Call before changes - the user may work in FreeCAD at the same time."""
        return await ctx.call("get_model_tree", "document.tree", document=document)

    @tool
    async def get_object(
        ref: Annotated[str, Field(description="Object name or label")], document: Doc = None
    ) -> dict[str, Any]:
        """Details of an object: status, expressions, the analysis for sketches, volume and size for solids."""
        return await ctx.call("get_object", "document.object", ref=ref, document=document)

    @tool
    async def delete_object(
        ref: Annotated[str, Field(description="Object name or label")], document: Doc = None
    ) -> dict[str, Any]:
        """Delete an object (one undo step)."""
        return await ctx.call("delete_object", "document.delete", ref=ref, document=document)

    @tool
    async def set_parameters(
        parameters: Annotated[
            dict[str, Any],
            Field(
                description="Name → value or {value, type, description}; type: length (default), distance, "
                "angle, integer, float, bool. Names in English/ASCII, e.g. Box_Width."
            ),
        ],
        document: Doc = None,
    ) -> dict[str, Any]:
        """Create/change central parameters in the VarSet 'Parameters'. Dimensions in sketches and features can use
        the parameter name instead of a number - so the model stays editable by parameter in FreeCAD."""
        return await ctx.call("set_parameters", "parameters.set", parameters=parameters, document=document)

    @tool
    async def list_parameters(document: Doc = None) -> list[dict[str, Any]]:
        """All parameters with type, value and expression reference."""
        return await ctx.call("list_parameters", "parameters.list", document=document)

    @tool
    async def create_body(
        label: Annotated[str, Field(description="Part name, e.g. 'Box' or 'Lid'")], document: Doc = None
    ) -> dict[str, Any]:
        """Create a PartDesign body for a part (one body = one printable part)."""
        return await ctx.call("create_body", "body.create", label=label, document=document)
