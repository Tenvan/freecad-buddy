"""Features (Feature): PartDesign features: additive, subtractive, dress-up, patterns."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.tools.base import SELECTOR_HELP, Doc, Num, Purpose, Registration

GROUP = Group("feature", "Feature", "Features")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def pad(
        sketch: Annotated[str, Field(description="Sketch label with a closed profile")],
        length: Num = 10,
        mode: Literal["length", "symmetric", "two_sides", "up_to_last"] = "length",
        length2: Num | None = None,
        reversed: bool = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Extrude a profile (additive)."""
        return await ctx.call(
            "pad", "feature.pad", sketch=sketch, length=length, mode=mode, length2=length2,
            reversed=reversed, purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def pocket(
        sketch: Annotated[str, Field(description="Sketch label with a closed profile")],
        depth: Num = 5,
        mode: Literal["length", "symmetric", "through_all"] = "length",
        reversed: Annotated[
            bool, Field(description="Direction; reversed automatically if nothing is cut")
        ] = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Cut a pocket (subtractive)."""
        return await ctx.call(
            "pocket", "feature.pocket", sketch=sketch, depth=depth, mode=mode, reversed=reversed,
            purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def revolve(
        sketch: Annotated[str, Field(description="Skizzen-Label")],
        axis: Annotated[
            str, Field(description="V_Axis/H_Axis (sketch axis) or X/Y/Z (body axis)")
        ] = "V_Axis",
        angle: Num = 360,
        subtractive: Annotated[bool, Field(description="true = Nut (Groove)")] = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Solid of revolution (Revolution) or rotational groove (Groove)."""
        return await ctx.call(
            "revolve", "feature.revolve", sketch=sketch, axis=axis, angle=angle, subtractive=subtractive,
            purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def sweep(
        profile: Annotated[
            str, Field(description="Sketch with a closed cross-section at the path start, e.g. a circle")
        ],
        path: Annotated[str, Field(description="Path sketch, e.g. add_profile kind='u_path'")],
        subtractive: Annotated[bool, Field(description="true = remove material along the path")] = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Sweep a cross-section along a path (PartDesign AdditivePipe/SubtractivePipe): round handles,
        brackets, cable ducts. Place the cross-section perpendicular to the path start
        (path starts vertically → circle on XY)."""
        return await ctx.call(
            "sweep", "feature.sweep", profile=profile, path=path, subtractive=subtractive, purpose=purpose,
            document=document,
        )  # fmt: skip

    @tool
    async def loft(
        sketches: Annotated[
            list[str],
            Field(
                description="Two or more sketches in transition order, each on its own plane "
                "(e.g. circle on XY, smaller circle on a datum_plane at Funnel_Height)"
            ),
        ],
        subtractive: Annotated[
            bool, Field(description="true = remove material through the sections")
        ] = False,
        ruled: Annotated[
            bool, Field(description="Straight surfaces between sections instead of smooth")
        ] = False,
        closed: Annotated[bool, Field(description="Close the loft back to the first sketch")] = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Loft through two or more sketches (PartDesign AdditiveLoft/SubtractiveLoft): funnels,
        adapters, transitions between cross-sections. Put every section on its own plane
        (origin plane or datum_plane with an offset parameter)."""
        return await ctx.call(
            "loft", "feature.loft", sketches=sketches, subtractive=subtractive, ruled=ruled, closed=closed,
            purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def hole(
        sketch: Annotated[
            str, Field(description="Sketch with circles at the hole positions (e.g. hole_rect)")
        ],
        size: Annotated[str, Field(description="ISO-Metrisch, z. B. M3, M4")] = "M3",
        cut: Literal["none", "countersink", "counterbore"] = "none",
        depth: Annotated[float | str | None, Field(description="empty = through all")] = None,
        threaded: bool = False,
        diameter: Annotated[
            float | str | None, Field(description="Diameter override, e.g. 3.4 for M3 clearance")
        ] = None,
        purpose: Purpose = None,
        document: Doc = None,
        cut_diameter: Annotated[
            float | str | None,
            Field(description="Custom counterbore/countersink diameter (number, parameter or expression)"),
        ] = None,
        cut_depth: Annotated[
            float | str | None, Field(description="Custom counterbore depth (counterbore only)")
        ] = None,
        countersink_angle: Annotated[
            float | str | None, Field(description="Custom countersink angle in degrees (countersink only)")
        ] = None,
    ) -> dict[str, Any]:
        """Holes (Hole feature) at every circle centre of the sketch. Cuts without cut_* use ISO defaults;
        cut_diameter/cut_depth/countersink_angle set custom, parametric values."""
        return await ctx.call(
            "hole", "feature.hole", sketch=sketch, size=size, cut=cut, depth=depth, threaded=threaded,
            diameter=diameter, purpose=purpose, document=document, cut_diameter=cut_diameter,
            cut_depth=cut_depth, countersink_angle=countersink_angle,
        )  # fmt: skip

    @tool
    async def fillet(
        selector: Annotated[str, Field(description=SELECTOR_HELP)] = "edges:top",
        radius: Num = 1,
        body: Annotated[str | None, Field(description="Body-Label")] = None,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Round edges. The selector is stored and resolved again after parameter changes."""
        return await ctx.call(
            "fillet",
            "feature.fillet",
            selector=selector,
            radius=radius,
            body=body,
            purpose=purpose,
            document=document,
        )

    @tool
    async def chamfer(
        selector: Annotated[str, Field(description=SELECTOR_HELP)] = "edges:bottom",
        size: Num = 0.5,
        body: Annotated[str | None, Field(description="Body-Label")] = None,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Chamfer edges (on the bed side better than a fillet - against elephant foot)."""
        return await ctx.call(
            "chamfer",
            "feature.chamfer",
            selector=selector,
            size=size,
            body=body,
            purpose=purpose,
            document=document,
        )

    @tool
    async def shell(
        selector: Annotated[str, Field(description="Opening face(s), e.g. face:top")] = "face:top",
        thickness: Num = 2,
        outward: bool = False,
        body: Annotated[str | None, Field(description="Body-Label")] = None,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Hollow the solid (Thickness) with a wall thickness; the selected faces become the openings."""
        return await ctx.call(
            "shell", "feature.shell", selector=selector, thickness=thickness, outward=outward, body=body,
            purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def pattern(
        features: Annotated[list[str], Field(description="Labels of the features to repeat")],
        kind: Annotated[
            Literal["mirrored", "linear", "polar", "grid"],
            Field(description="grid = 2D raster (MultiTransform); PartDesign cannot pattern a pattern"),
        ],
        plane: Annotated[str, Field(description="mirrored: XY/XZ/YZ")] = "YZ",
        direction: Annotated[str, Field(description="linear/grid: X/Y/Z")] = "X",
        axis: Annotated[str, Field(description="polar: X/Y/Z")] = "Z",
        length: Annotated[
            float | str, Field(description="linear/grid: total length (mm, parameter, expression)")
        ] = 20,
        angle: Annotated[float | str, Field(description="polar: Gesamtwinkel")] = 360,
        count: Annotated[
            int | str, Field(description="Count (linear/polar/grid), number or integer parameter")
        ] = 2,
        direction2: Annotated[str, Field(description="grid: second direction X/Y/Z")] = "Y",
        length2: Annotated[float | str, Field(description="grid: total length of the second direction")] = 20,
        count2: Annotated[int | str, Field(description="grid: count in the second direction")] = 2,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Mirror features or repeat them linearly/polar/as a raster (instead of drawing geometry several times)."""
        return await ctx.call(
            "pattern", "feature.pattern", features=features, kind=kind, plane=plane, direction=direction,
            axis=axis, length=length, angle=angle, count=count, direction2=direction2, length2=length2,
            count2=count2, purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def thread(
        center: Annotated[
            list[float | str],
            Field(description="[x, y] of the vertical cylinder axis (numbers or parameters)"),
        ],
        diameter: Annotated[
            float | str, Field(description="Major diameter, e.g. 10 for M10 or 'Pin_Diameter'")
        ],
        pitch: Annotated[float | str, Field(description="Thread pitch, ISO coarse: M3 0.5, M5 0.8, M10 1.5")],
        length: Num,
        z_start: Annotated[float | str, Field(description="Height where the thread starts")] = 0,
        left_handed: bool = False,
        body: Annotated[
            str | None, Field(description="Body label; empty when there is only one body")
        ] = None,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Cut a real external metric thread (ISO 60° profile, native SubtractiveHelix) into an existing
        vertical cylinder of the body. Fully constrained and parametric; repeat it with pattern."""
        return await ctx.call(
            "thread", "feature.thread", center=center, diameter=diameter, pitch=pitch, length=length,
            z_start=z_start, left_handed=left_handed, body=body, purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def add_gear(
        kind: Literal["involute", "internal", "rack", "cycloid", "bevel", "worm", "timing"] = "involute",
        teeth: Annotated[int | str, Field(description="Number of teeth (number or integer parameter)")] = 15,
        module: Annotated[
            float | str | None, Field(description="Module in mm; empty = addon default")
        ] = None,
        height: Annotated[
            float | str | None, Field(description="Gear width in mm; empty = addon default")
        ] = None,
        properties: Annotated[
            dict[str, Any] | None,
            Field(
                description="Further gear properties, e.g. {pressure_angle: 20, backlash: 0.1, axle_hole: true, "
                "axle_holesize: 5, helix_angle: 15}"
            ),
        ] = None,
        body: Annotated[
            str | None, Field(description="Body label; empty when there is only one body")
        ] = None,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Parametric gear from the freecad.gears workbench (needs the addon) as feature of a body; one gear per
        body. Values accept parameter names/expressions. Returns pitch/addendum/root diameter."""
        return await ctx.call(
            "add_gear", "feature.gear", timeout=120, kind=kind, teeth=teeth, module=module, height=height,
            properties=properties, body=body, purpose=purpose, document=document,
        )  # fmt: skip
