"""Referenzen (Reference): Stable references: datum planes, shape binders, selectors."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.tools.base import SELECTOR_HELP, Doc, Num, Purpose, Registration

GROUP = Group("reference", "Reference", "Referenzen")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def datum_plane(
        base: Annotated[str, Field(description="XY, XZ oder YZ")] = "XY",
        offset: Num = 0,
        angle: Num = 0,
        rotation_axis: Annotated[str, Field(description="X, Y oder Z")] = "X",
        body: Annotated[str | None, Field(description="Body-Label")] = None,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Bezugsebene als stabile Skizzenbasis (statt Skizze auf Körperfläche)."""
        return await ctx.call(
            "datum_plane", "feature.datum_plane", base=base, offset=offset, angle=angle,
            rotation_axis=rotation_axis, body=body, purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def shape_binder(
        sources: Annotated[
            list[str],
            Field(
                description="Objects or elements of OTHER bodies: 'Object', 'Object:Element' or "
                "'Body:Object[:Element]'; Element is EdgeN/FaceN/VertexN or g<N> of a sketch"
            ),
        ],
        body: Annotated[str | None, Field(description="Target body label")] = None,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Bind geometry of another body into this body (SubShapeBinder, follows its source). Use it as
        source for add_geometry type 'external' - the PartDesign way to reference across bodies."""
        return await ctx.call(
            "shape_binder", "feature.shape_binder", sources=sources, body=body, purpose=purpose,
            document=document,
        )  # fmt: skip

    @tool
    async def select_geometry(
        selector: Annotated[str, Field(description=SELECTOR_HELP)],
        target: Annotated[str | None, Field(description="Feature-Label; leer = Tip des Bodys")] = None,
        body: Annotated[str | None, Field(description="Body-Label")] = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Vorschau: welche Flächen/Kanten ein Selektor trifft (mit Mittelpunkt, Normale, Länge, Radius)."""
        return await ctx.call(
            "select_geometry",
            "select.preview",
            selector=selector,
            target=target,
            body=body,
            document=document,
        )
