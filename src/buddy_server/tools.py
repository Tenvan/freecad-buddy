"""MCP tools of FreeCAD Buddy. Each tool forwards to one bridge method.

Tool descriptions are written for the agent: they state the intended modelling workflow,
so the model stays PartDesign-first and editable by a human.
"""

from __future__ import annotations

import base64
import itertools
import json
import time
from collections.abc import Awaitable, Callable
from typing import Annotated, Any, Literal, Protocol, TypeVar

from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.mcpserver.utilities.types import Image
from pydantic import Field

from buddy_bridge.protocol import RpcError
from buddy_server import design_rules
from buddy_server.bridge import Bridge, BridgeTimeout, BridgeUnavailable
from buddy_server.events import EventBus, ToolFinished, ToolStarted

Doc = Annotated[str | None, Field(description="Dokumentname oder -label; leer = aktives Dokument")]
Num = Annotated[
    float | str,
    Field(description="Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden)"),
]
Purpose = Annotated[str | None, Field(description="Zweck für das Label, z. B. 'Base' → 'Pad_Base'")]

SELECTOR_HELP = (
    "Semantischer Selektor, z. B. edges:top, edges:vertical, edges:bottom, faces:top, face:top, "
    "edges:circular,radius=2, edges:of_feature=Pocket_Cut. select_geometry zeigt die Treffer vorab."
)

_ids = itertools.count(1)

T = TypeVar("T")


class ToolRegistrar(Protocol):
    def tool(self) -> Callable[[Any], Any]: ...


class NameCollector:
    """Stand-in registrar: collects tool names without an MCP server (for building instructions)."""

    def tool(self) -> Callable[[Any], Any]:
        return lambda fn: fn


def _summary(result: Any) -> tuple[str, tuple[str, ...]]:
    if not isinstance(result, dict):
        return "ok", ()
    parts = []
    for entry in result.get("created", [])[:3]:
        parts.append(f"+{entry['label']}")
    if isinstance(result.get("sketch"), dict):
        parts.append(f"DoF={result['sketch'].get('dof')}")
    return (" ".join(parts) or "ok"), tuple(result.get("warnings", []))


def _error_text(error: RpcError) -> str:
    lines = [f"[{error.name}] {error.message}"]
    hints = error.data.get("hints") or []
    lines.extend(f"Hinweis: {hint}" for hint in hints)
    extra = {k: v for k, v in error.data.items() if k not in ("hints", "state")}
    if extra:
        lines.append("Details: " + json.dumps(extra, ensure_ascii=False, default=str)[:4000])
    return "\n".join(lines)


class ToolContext:
    def __init__(self, bridge: Bridge, bus: EventBus) -> None:
        self.bridge = bridge
        self.bus = bus

    async def call(self, tool: str, method: str, timeout: float | None = None, **params: Any) -> Any:
        call_id = next(_ids)
        self.bus.publish(ToolStarted(call_id, tool))
        started = time.monotonic()
        clean = {key: value for key, value in params.items() if value is not None}
        try:
            result = await self.bridge.call(method, clean, timeout)
        except BridgeUnavailable as error:
            self._finish(call_id, tool, started, False, "bridge_unavailable")
            raise ToolError(f"[bridge_unavailable] {error}") from None
        except BridgeTimeout as error:
            self._finish(call_id, tool, started, False, "timeout")
            raise ToolError(f"[timeout] {error}") from None
        except RpcError as error:
            self._finish(call_id, tool, started, False, error.name)
            raise ToolError(_error_text(error)) from None
        summary, warnings = _summary(result)
        self._finish(call_id, tool, started, True, summary, warnings)
        return result

    async def local(self, tool: str, fn: Callable[[], Awaitable[T]]) -> T:
        """Run a tool that is answered by the server itself, with the same start/finish events."""
        call_id = next(_ids)
        self.bus.publish(ToolStarted(call_id, tool))
        started = time.monotonic()
        try:
            result = await fn()
        except ToolError as error:
            code = str(error).split("]", 1)[0].lstrip("[") if str(error).startswith("[") else "error"
            self._finish(call_id, tool, started, False, code)
            raise
        self._finish(call_id, tool, started, True, "ok")
        return result

    async def printer_profile(self) -> dict[str, Any] | None:
        """Active printer profile from FreeCAD, or ``None`` if the bridge cannot answer."""
        try:
            result = await self.bridge.call("print.get_profile", {}, None)
        except (BridgeUnavailable, BridgeTimeout, RpcError):
            return None
        return result if isinstance(result, dict) else None

    def _finish(
        self, call_id: int, tool: str, started: float, ok: bool, summary: str, warnings: tuple[str, ...] = ()
    ) -> None:
        self.bus.publish(ToolFinished(call_id, tool, time.monotonic() - started, ok, summary, warnings))


def register_tools(mcp: ToolRegistrar, ctx: ToolContext, allow_python: bool) -> list[str]:
    names: list[str] = []

    def tool(fn: Any) -> Any:
        names.append(fn.__name__)
        return mcp.tool()(fn)

    # --- Status & documents --------------------------------------------------------------
    @tool
    async def get_status() -> dict[str, Any]:
        """Status von FreeCAD und Bridge: Version, offene Dokumente, fehlende Objekttypen. Zuerst aufrufen."""
        return await ctx.call("get_status", "system.status")

    @tool
    async def new_document(
        name: Annotated[str, Field(description="Name des neuen Dokuments")],
    ) -> dict[str, Any]:
        """Neues FreeCAD-Dokument anlegen und aktivieren. Workflow danach: set_parameters → create_body →
        create_sketch → add_profile → pad/pocket → Details (fillet, hole, …) → check_printability → export_body."""
        return await ctx.call("new_document", "document.new", name=name)

    @tool
    async def open_document(
        path: Annotated[str, Field(description="Pfad zur .FCStd-Datei")],
    ) -> dict[str, Any]:
        """Vorhandenes Dokument öffnen und aktivieren."""
        return await ctx.call("open_document", "document.open", path=path)

    @tool
    async def save_document(
        path: Annotated[str | None, Field(description="Zielpfad (.FCStd); leer = bisherige Datei")] = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Dokument als .FCStd speichern (ohne path in die bisherige Datei; neue Dokumente brauchen path)."""
        return await ctx.call("save_document", "document.save", path=path, document=document)

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
    async def undo(
        steps: Annotated[int, Field(ge=1, le=20, description="Anzahl Schritte")] = 1, document: Doc = None
    ) -> dict[str, Any]:
        """Letzte Änderung(en) rückgängig machen. Jeder Tool-Aufruf ist genau ein Schritt."""
        return await ctx.call("undo", "document.undo", steps=steps, document=document)

    # --- Parameters & body -----------------------------------------------------------------
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

    # --- Sketches -----------------------------------------------------------------------------
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
            Literal["rectangle", "rounded_rectangle", "slot", "circle", "polygon", "hole_rect", "polyline"],
            Field(description="Profilart"),
        ],
        params: Annotated[
            dict[str, Any],
            Field(
                description=(
                    "rectangle: width, height, [center=[x,y]], [anchor=center|corner]; "
                    "rounded_rectangle: width, height, radius, [center]; slot: length (Mittenabstand), width, [center]; "
                    "circle: diameter, [center]; polygon: sides, diameter|across_flats, [center]; "
                    "hole_rect: width, height (Lochabstände), diameter, [center]; polyline: points=[[x,y],…]. "
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
        sketch: Annotated[str, Field(description="Skizzen-Label")],
        items: Annotated[
            list[dict[str, Any]],
            Field(
                description="Fallback, wenn kein Profil passt. {type: line, start, end} | {type: circle, center, radius} "
                "| {type: arc, center, radius, start_angle, end_angle} (Grad, gegen Uhrzeigersinn) | {type: point, at}; "
                "optional construction: true"
            ),
        ],
        document: Doc = None,
    ) -> dict[str, Any]:
        """Low-Level-Geometrie hinzufügen; Rückgabe sind Referenzen g<N> für add_constraints."""
        return await ctx.call(
            "add_geometry", "sketch.add_geometry", sketch=sketch, items=items, document=document
        )

    @tool
    async def add_constraints(
        sketch: Annotated[str, Field(description="Skizzen-Label")],
        items: Annotated[
            list[dict[str, Any]],
            Field(
                description="{type, a, b?, about?, value?, name?}. Referenzen: g<N>, g<N>.start|end|center, origin, "
                "x_axis, y_axis. Typen: coincident, horizontal, vertical, parallel, perpendicular, equal, tangent, "
                "point_on_object, symmetric, distance, distance_x, distance_y, radius, diameter, angle (Grad). "
                "value: Zahl oder Parametername; Maße immer benennen."
            ),
        ],
        document: Doc = None,
    ) -> dict[str, Any]:
        """Constraints hinzufügen. Widersprüchliche/redundante Constraints werden abgelehnt (Rollback)."""
        return await ctx.call(
            "add_constraints", "sketch.add_constraints", sketch=sketch, items=items, document=document
        )

    @tool
    async def analyze_sketch(
        sketch: Annotated[str, Field(description="Skizzen-Label")], document: Doc = None
    ) -> dict[str, Any]:
        """Skizzenanalyse: DoF, Konflikte, Redundanzen, geschlossene Linienzüge und Stil-Lint."""
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

    # --- Features -------------------------------------------------------------------------------
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
    ) -> dict[str, Any]:
        """Bohrungen (Hole-Feature) an allen Kreismittelpunkten der Skizze."""
        return await ctx.call(
            "hole", "feature.hole", sketch=sketch, size=size, cut=cut, depth=depth, threaded=threaded,
            diameter=diameter, purpose=purpose, document=document,
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

    @tool
    async def screenshot(
        view: Literal["iso", "front", "back", "top", "bottom", "left", "right", "current"] = "iso",
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

    # --- Design rules ---------------------------------------------------------------------------
    @tool
    async def get_design_rules(
        topic: Annotated[
            str | None,
            Field(description=f"Thema: {', '.join(design_rules.TOPIC_KEYS)}; leer = Themenübersicht"),
        ] = None,
    ) -> str:
        """Design-Regelwerk für FreeCAD-Konstruktion und FDM-Druck (Werte aus dem aktiven Druckerprofil).
        Vor einer neuen Konstruktion die passenden Themen lesen, z. B. sketches und printing."""

        async def render() -> str:
            available = set(names)
            if topic is None:
                return design_rules.render_overview(available)
            profile = await ctx.printer_profile()
            try:
                text = design_rules.render_topic(topic, profile, available)
            except KeyError:
                keys = ", ".join(t.key for t in design_rules.visible_topics(available))
                raise ToolError(f"[validation] Unbekanntes Thema '{topic}'. Gültig: {keys}") from None
            if profile is None:
                text += "\n\n(FreeCAD nicht erreichbar – Werte aus dem Standard-Druckerprofil)"
            return text

        return await ctx.local("get_design_rules", render)

    # --- 3D printing ------------------------------------------------------------------------------
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

    if allow_python:

        @tool
        async def execute_python(
            code: Annotated[str, Field(description="Python-Code; Variable 'result' wird zurückgegeben")],
            document: Doc = None,
        ) -> dict[str, Any]:
            """Notausgang (nur mit FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD als ein Undo-Schritt."""
            return await ctx.call(
                "execute_python", "python.execute", timeout=150, code=code, document=document
            )

    return names
