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
        sketch: Annotated[str, Field(description="Skizzen-Label mit geschlossenem Profil")],
        length: Num = 10,
        mode: Literal["length", "symmetric", "two_sides", "up_to_last"] = "length",
        length2: Num | None = None,
        reversed: bool = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Profil aufpolstern (additiv)."""
        return await ctx.call(
            "pad", "feature.pad", sketch=sketch, length=length, mode=mode, length2=length2,
            reversed=reversed, purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def pocket(
        sketch: Annotated[str, Field(description="Skizzen-Label mit geschlossenem Profil")],
        depth: Num = 5,
        mode: Literal["length", "symmetric", "through_all"] = "length",
        reversed: Annotated[
            bool, Field(description="Richtung; wird automatisch umgekehrt, falls nichts geschnitten")
        ] = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Tasche schneiden (subtraktiv)."""
        return await ctx.call(
            "pocket", "feature.pocket", sketch=sketch, depth=depth, mode=mode, reversed=reversed,
            purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def revolve(
        sketch: Annotated[str, Field(description="Skizzen-Label")],
        axis: Annotated[
            str, Field(description="V_Axis/H_Axis (Skizzenachse) oder X/Y/Z (Body-Achse)")
        ] = "V_Axis",
        angle: Num = 360,
        subtractive: Annotated[bool, Field(description="true = Nut (Groove)")] = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Rotationskörper (Revolution) oder Rotationsnut (Groove)."""
        return await ctx.call(
            "revolve", "feature.revolve", sketch=sketch, axis=axis, angle=angle, subtractive=subtractive,
            purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def sweep(
        profile: Annotated[
            str, Field(description="Skizze mit geschlossenem Querschnitt am Pfadanfang, z. B. Kreis")
        ],
        path: Annotated[str, Field(description="Pfad-Skizze, z. B. add_profile kind='u_path'")],
        subtractive: Annotated[
            bool, Field(description="true = Material entlang des Pfads entfernen")
        ] = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Querschnitt entlang eines Pfads ziehen (PartDesign AdditivePipe/SubtractivePipe): runde Griffe,
        Bügel, Kabelkanäle. Querschnitt senkrecht zum Pfadanfang legen (Pfad startet vertikal → Kreis auf XY)."""
        return await ctx.call(
            "sweep", "feature.sweep", profile=profile, path=path, subtractive=subtractive, purpose=purpose,
            document=document,
        )  # fmt: skip

    @tool
    async def hole(
        sketch: Annotated[
            str, Field(description="Skizze mit Kreisen an den Bohrungspositionen (z. B. hole_rect)")
        ],
        size: Annotated[str, Field(description="ISO-Metrisch, z. B. M3, M4")] = "M3",
        cut: Literal["none", "countersink", "counterbore"] = "none",
        depth: Annotated[float | str | None, Field(description="leer = durch alles")] = None,
        threaded: bool = False,
        diameter: Annotated[
            float | str | None, Field(description="Durchmesser-Override, z. B. 3.4 für M3-Spiel")
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
        """Kanten verrunden. Der Selektor wird gespeichert und nach Parameteränderungen neu aufgelöst."""
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
        """Kanten fasen (an der Druckbett-Unterseite besser als Verrundung – gegen Elefantenfuß)."""
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
        selector: Annotated[str, Field(description="Öffnungsfläche(n), z. B. face:top")] = "face:top",
        thickness: Num = 2,
        outward: bool = False,
        body: Annotated[str | None, Field(description="Body-Label")] = None,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Körper aushöhlen (Thickness) mit Wandstärke; gewählte Flächen werden zur Öffnung."""
        return await ctx.call(
            "shell", "feature.shell", selector=selector, thickness=thickness, outward=outward, body=body,
            purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def pattern(
        features: Annotated[list[str], Field(description="Labels der zu vervielfältigenden Features")],
        kind: Annotated[
            Literal["mirrored", "linear", "polar", "grid"],
            Field(
                description="grid = 2D-Raster (MultiTransform); Muster auf Muster ist in PartDesign nicht möglich"
            ),
        ],
        plane: Annotated[str, Field(description="mirrored: XY/XZ/YZ")] = "YZ",
        direction: Annotated[str, Field(description="linear/grid: X/Y/Z")] = "X",
        axis: Annotated[str, Field(description="polar: X/Y/Z")] = "Z",
        length: Annotated[
            float | str, Field(description="linear/grid: Gesamtlänge (mm, Parameter, Ausdruck)")
        ] = 20,
        angle: Annotated[float | str, Field(description="polar: Gesamtwinkel")] = 360,
        count: Annotated[
            int | str, Field(description="Anzahl (linear/polar/grid), Zahl oder Integer-Parameter")
        ] = 2,
        direction2: Annotated[str, Field(description="grid: zweite Richtung X/Y/Z")] = "Y",
        length2: Annotated[float | str, Field(description="grid: Gesamtlänge der zweiten Richtung")] = 20,
        count2: Annotated[int | str, Field(description="grid: Anzahl in der zweiten Richtung")] = 2,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Features spiegeln oder linear/polar/als Raster vervielfältigen (statt Geometrie mehrfach zu zeichnen)."""
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
