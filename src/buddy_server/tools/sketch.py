"""Skizze (Sketch): Fully constrained sketches: profiles, low-level geometry, constraints."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.tools.base import Doc, Num, Purpose, Registration

GROUP = Group("sketch", "Sketch", "Skizze")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def create_sketch(
        plane: Annotated[
            str,
            Field(description="XY, XZ, YZ (Body-Ursprung), Label einer Datum-Ebene oder face:<selector>"),
        ] = "XY",
        purpose: Purpose = None,
        offset: Num = 0,
        body: Annotated[str | None, Field(description="Body-Label; leer bei nur einem Body")] = None,
        reversed: bool = False,
        allow_face_attachment: Annotated[
            bool, Field(description="Nur wenn nötig: Flächenbezug ist anfällig für Topologie-Änderungen")
        ] = False,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Skizze auf stabiler Referenz anlegen. Bevorzugt Ursprungsebenen mit offset oder datum_plane."""
        return await ctx.call(
            "create_sketch",
            "sketch.create",
            plane=plane,
            purpose=purpose,
            offset=offset,
            body=body,
            reversed=reversed,
            allow_face_attachment=allow_face_attachment,
            document=document,
        )

    @tool
    async def add_profile(
        sketch: Annotated[str, Field(description="Skizzen-Label")],
        kind: Annotated[
            Literal[
                "rectangle",
                "rounded_rectangle",
                "slot",
                "circle",
                "polygon",
                "hole_rect",
                "polyline",
                "u_path",
            ],
            Field(description="Profilart"),
        ],
        params: Annotated[
            dict[str, Any],
            Field(
                description=(
                    "rectangle: width, height, [center=[x,y]], [anchor=center|corner]; "
                    "rounded_rectangle: width, height, radius, [center]; slot: length (Mittenabstand), width, [center]; "
                    "circle: diameter, [center]; polygon: sides, diameter|across_flats, [center]; "
                    "hole_rect: width, height (Lochabstände), diameter, [center]; polyline: points=[[x,y],…]; "
                    "u_path (offener Bügel-Pfad für sweep): length (Beinabstand), height, radius. "
                    "Werte: Zahl oder Parametername."
                )
            ),
        ],
        prefix: Annotated[
            str | None, Field(description="Präfix für Maßnamen, z. B. 'Base' → Base_Width")
        ] = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Vollständig bestimmtes Profil zeichnen wie ein Mensch: symmetrisch zum Ursprung, Equal statt
        Doppelmaß, benannte Maße. Ergebnis enthält die Skizzenanalyse (DoF muss 0 sein)."""
        return await ctx.call(
            "add_profile",
            "sketch.add_profile",
            sketch=sketch,
            kind=kind,
            params=params,
            prefix=prefix,
            document=document,
        )

    @tool
    async def add_geometry(
        sketch: Annotated[str, Field(description="Sketch label")],
        items: Annotated[
            list[dict[str, Any]],
            Field(
                description="{type: line, start, end} | {type: circle, center, radius} | {type: arc, center, radius, "
                "start_angle, end_angle} (degrees, counter-clockwise) | {type: point, at}; optional construction: true. "
                "External geometry: {type: external, source, element, defining?, allow_face_reference?} - source is "
                "an earlier sketch, datum or shape_binder in the same body; element is g<N>[.start|end|center] of a "
                "source sketch (real geometry, not construction) or EdgeN/VertexN/edge selector otherwise; "
                "defining: true makes the edge part of the profile"
            ),
        ],
        document: Doc = None,
    ) -> dict[str, Any]:
        """Add low-level geometry or external references. Returns g<N> (own) and x<N> (external) references
        for add_constraints. Define hole patterns once in a layout sketch and reference them here."""
        return await ctx.call(
            "add_geometry", "sketch.add_geometry", sketch=sketch, items=items, document=document
        )

    @tool
    async def add_constraints(
        sketch: Annotated[str, Field(description="Sketch label")],
        items: Annotated[
            list[dict[str, Any]],
            Field(
                description="{type, a, b?, about?, value?, name?}. References: g<N> (own), x<N> (external), each with "
                ".start|end|center, origin, x_axis, y_axis. Types: coincident, horizontal, vertical, parallel, "
                "perpendicular, equal, tangent, point_on_object, symmetric, distance, distance_x, distance_y, radius, "
                "diameter, angle (degrees). value: number, parameter name or expression; always name dimensions."
            ),
        ],
        document: Doc = None,
    ) -> dict[str, Any]:
        """Add constraints. Conflicting/redundant constraints are rejected (rollback)."""
        return await ctx.call(
            "add_constraints", "sketch.add_constraints", sketch=sketch, items=items, document=document
        )

    @tool
    async def analyze_sketch(
        sketch: Annotated[str, Field(description="Sketch label")], document: Doc = None
    ) -> dict[str, Any]:
        """Sketch analysis: DoF, conflicts, redundancies, closed wires, external geometry (x<N> with source)
        and style lint (incl. broken external references)."""
        return await ctx.call("analyze_sketch", "sketch.analyze", sketch=sketch, document=document)

    @tool
    async def fully_constrain_sketch(
        sketch: Annotated[str, Field(description="Skizzen-Label")],
        apply: Annotated[bool, Field(description="false = nur Vorschläge, true = anwenden")] = False,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Restliche Freiheitsgrade finden bzw. schließen (Koinzidenzen, H/V, dann benannte X/Y-Maße). Nie Block."""
        return await ctx.call(
            "fully_constrain_sketch", "sketch.fully_constrain", sketch=sketch, apply=apply, document=document
        )
