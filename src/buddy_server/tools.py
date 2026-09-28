"""MCP tools of FreeCAD Buddy. Each tool forwards to one bridge method.

Tool descriptions are written for the agent: they state the intended modelling workflow,
so the model stays PartDesign-first and editable by a human.
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from collections.abc import Callable
from typing import Annotated, Any, Literal, Protocol

from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.mcpserver.utilities.types import Image
from pydantic import Field

from buddy_bridge.protocol import RpcError
from buddy_server import design_rules
from buddy_server.addon_catalog import AddonEntry, search
from buddy_server.addon_service import UNTRUSTED_NOTE, AddonCatalogService, CatalogError
from buddy_server.bridge import Bridge, BridgeTimeout, BridgeUnavailable
from buddy_server.events import EventBus

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


class ToolRegistrar(Protocol):
    def tool(self) -> Callable[[Any], Any]: ...


class NameCollector:
    """Stand-in registrar: collects tool names without an MCP server (for building instructions)."""

    def tool(self) -> Callable[[Any], Any]:
        return lambda fn: fn


def _error_text(error: RpcError) -> str:
    lines = [f"[{error.name}] {error.message}"]
    hints = error.data.get("hints") or []
    lines.extend(f"Hinweis: {hint}" for hint in hints)
    extra = {k: v for k, v in error.data.items() if k not in ("hints", "state")}
    if extra:
        lines.append("Details: " + json.dumps(extra, ensure_ascii=False, default=str)[:4000])
    return "\n".join(lines)


class ToolContext:
    """Forwards tool calls to the bridge and turns bridge failures into MCP tool errors.

    Request/response logging happens in ``calllog.ToolCallLog`` (MCP middleware), not here.
    """

    def __init__(self, bridge: Bridge, bus: EventBus, addons: AddonCatalogService | None = None) -> None:
        self.bridge = bridge
        self.bus = bus
        self.addons = addons

    async def installed(self) -> dict[str, Any] | None:
        """Installed addons/macros and FreeCAD version from the bridge, ``None`` if it cannot answer."""
        try:
            result = await self.bridge.call("addons.status", {}, None)
        except (BridgeUnavailable, BridgeTimeout, RpcError):
            return None
        return result if isinstance(result, dict) else None

    async def catalog(self, refresh: bool = False) -> tuple[AddonCatalogService, dict[str, Any]]:
        if self.addons is None:
            raise ToolError("[unsupported] Addon-Katalog ist in diesem Server nicht konfiguriert")
        try:
            state = await self.addons.ensure(refresh)
        except CatalogError as error:
            hint = "Netz/Proxy prüfen" if error.code == "catalog_unavailable" else "später erneut versuchen"
            raise ToolError(f"[{error.code}] {error}\nHinweis: {hint}") from None
        return self.addons, state.as_dict()

    async def call(self, tool: str, method: str, timeout: float | None = None, **params: Any) -> Any:
        clean = {key: value for key, value in params.items() if value is not None}
        try:
            return await self.bridge.call(method, clean, timeout)
        except BridgeUnavailable as error:
            raise ToolError(f"[bridge_unavailable] {error}") from None
        except BridgeTimeout as error:
            raise ToolError(f"[timeout] {error}") from None
        except RpcError as error:
            raise ToolError(_error_text(error)) from None

    async def printer_profile(self) -> dict[str, Any] | None:
        """Active printer profile from FreeCAD, or ``None`` if the bridge cannot answer."""
        try:
            result = await self.bridge.call("print.get_profile", {}, None)
        except (BridgeUnavailable, BridgeTimeout, RpcError):
            return None
        return result if isinstance(result, dict) else None


def _installed_flag(entry: AddonEntry, status: dict[str, Any] | None) -> bool | None:
    if status is None:
        return None
    if entry.kind == "macro":
        return entry.filename in status["macros"] or f"Macro_{entry.filename}" in status["macros"]
    return entry.id in status["addons"]


def _version(status: dict[str, Any] | None) -> tuple[int, int, int] | None:
    if status is None:
        return None
    major, minor, patch = (int(part) for part in status["freecad_version"][:3])
    return major, minor, patch


def _install_blocker(entry: AddonEntry, status: dict[str, Any]) -> str | None:
    """Why Buddy refuses to install ``entry`` (the Addon Manager can still do it), or ``None``."""
    version = _version(status)
    if _installed_flag(entry, status):
        return f"'{entry.id}' is already installed (updates stay with the Addon Manager)"
    if version is not None and not entry.compatible_with(version):
        return f"'{entry.id}' is not compatible with FreeCAD {'.'.join(map(str, version))}"
    if entry.python_dependencies:
        packages = ", ".join(entry.python_dependencies[:5])
        return f"'{entry.id}' needs Python packages ({packages}); Buddy does not run pip"
    if entry.addon_dependencies:
        return f"'{entry.id}' depends on other addons ({', '.join(entry.addon_dependencies[:5])})"
    if entry.kind == "preference_pack":
        return "Preference packs can only be searched, not installed, through Buddy"
    if entry.sparse:
        return f"'{entry.id}' is installed via git only"
    return None


def register_tools(
    mcp: ToolRegistrar, ctx: ToolContext, allow_python: bool, allow_addon_install: bool = False
) -> list[str]:
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
    async def close_document(
        unsaved: Annotated[
            Literal["refuse", "save", "discard"],
            Field(description="Unsaved changes: refuse (default, error), save first, or discard them"),
        ] = "refuse",
        path: Annotated[
            str | None, Field(description="Target path (.FCStd) for unsaved='save' on a never-saved document")
        ] = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Close a document. With unsaved changes it refuses unless unsaved='save' or 'discard' - ask the
        user before discarding. Returns the documents that stay open."""
        return await ctx.call(
            "close_document", "document.close", unsaved=unsaved, path=path, document=document
        )

    @tool
    async def revert_document(document: Doc = None) -> dict[str, Any]:
        """Discard all changes since the last save (reopens the saved .FCStd). Ask the user first; for a
        never-saved document use close_document(unsaved='discard')."""
        return await ctx.call("revert_document", "document.revert", document=document)

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

    # --- Material & appearance --------------------------------------------------------------------
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

    # --- Assembly (Assembly4 convention) ----------------------------------------------------------
    @tool
    async def create_assembly(
        label: Annotated[str, Field(description="Assembly label")] = "Assembly",
        document: Doc = None,
    ) -> dict[str, Any]:
        """Create an Assembly4 assembly in the document (bodies move into a 'Parts' group). Then
        add_to_assembly for each body, add_fastener for standard parts, explode_assembly for an exploded view."""
        return await ctx.call("create_assembly", "assembly.create", label=label, document=document)

    @tool
    async def add_to_assembly(
        part: Annotated[str, Field(description="Body or App::Part label")],
        label: Annotated[str | None, Field(description="Link label; empty = part label")] = None,
        offset: Annotated[
            list[float] | None, Field(description="[x, y, z] from the modelled position; empty = in place")
        ] = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Insert a body into the assembly as App::Link placed by Assembly4 (LCS_Origin * AttachmentOffset)."""
        return await ctx.call(
            "add_to_assembly", "assembly.add", part=part, label=label, offset=offset, document=document
        )

    @tool
    async def add_fastener(
        type: Annotated[
            str,
            Field(description="Fasteners type, e.g. ISO4032 (hex nut), ISO7089 (washer), ISO4762 (screw)"),
        ],
        diameter: Annotated[str, Field(description="Size, e.g. 'M10'")],
        positions: Annotated[
            list[list[float]], Field(description="One [x, y, z] per fastener (bottom face)")
        ],
        thread: Annotated[bool, Field(description="Model the real thread (slower)")] = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Standard parts from the Fasteners workbench (needs the addon), placed in the assembly if there
        is one. Stack e.g. a washer on the plate and the nut on top of the washer."""
        return await ctx.call(
            "add_fastener", "assembly.fastener", type=type, diameter=diameter, positions=positions,
            thread=thread, purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def explode_assembly(
        moves: Annotated[
            dict[str, list[float]], Field(description="Label -> [dx, dy, dz] from the assembled position")
        ],
        name: Annotated[str, Field(description="Configuration name")] = "Exploded",
        document: Doc = None,
    ) -> dict[str, Any]:
        """Exploded view as Assembly4 configuration: saves 'Assembled' once, moves the listed parts and
        saves the result. Switch back and forth with apply_configuration."""
        return await ctx.call(
            "explode_assembly", "assembly.explode", moves=moves, name=name, document=document
        )

    @tool
    async def apply_configuration(
        name: Annotated[str, Field(description="Configuration, e.g. 'Assembled' or 'Exploded'")],
        document: Doc = None,
    ) -> dict[str, Any]:
        """Apply a saved Assembly4 configuration (positions of all assembly parts)."""
        return await ctx.call("apply_configuration", "assembly.configuration", name=name, document=document)

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

    # --- Addons ----------------------------------------------------------------------------------
    @tool
    async def search_addons(
        query: Annotated[
            str, Field(description="Suchbegriffe, alle müssen passen, z. B. 'grid' oder 'honeycomb'")
        ],
        kind: Literal["any", "workbench", "macro", "preference_pack"] = "any",
        limit: Annotated[int, Field(ge=1, le=50)] = 10,
        refresh: Annotated[
            bool, Field(description="Katalog sofort neu laden (sonst höchstens täglich)")
        ] = False,
    ) -> dict[str, Any]:
        """Offiziellen FreeCAD-Addon-Katalog durchsuchen (Workbenches, Makros, Preference Packs): Treffer mit
        Kompatibilität zum laufenden FreeCAD und Installationsstatus. Vor einem eigenen Design-Tool prüfen."""
        service, state = await ctx.catalog(refresh)
        status = await ctx.installed()
        version = _version(status)
        hits = search(service.entries(), query, None if kind == "any" else kind, limit)
        results = [
            {**e.summary(version), "installed": _installed_flag(e, status), "score": s} for e, s in hits
        ]
        warnings = [state["warning"]] if "warning" in state else []
        if status is None:
            warnings.append("FreeCAD nicht erreichbar: Kompatibilität und Installationsstatus unbekannt")
        return {"catalog": state, "freecad_version": status and status["freecad_version"], "query": query,
                "count": len(results), "results": results, "warnings": warnings}  # fmt: skip

    @tool
    async def get_addon(
        addon_id: Annotated[str, Field(description="Id oder Name aus search_addons, z. B. 'lattice2'")],
        readme: Annotated[bool, Field(description="README-Auszug aus dem Repository laden")] = True,
    ) -> dict[str, Any]:
        """Details eines Addons oder Makros: Lizenz, Maintainer, Repository, letzte Aktualisierung,
        Abhängigkeiten (FreeCAD, Addons, Python), Kompatibilität, Installationsstatus und README-Auszug."""
        service, state = await ctx.catalog()
        entry = service.find(addon_id)
        if entry is None:
            raise ToolError(
                f"[not_found] Kein Addon '{addon_id}' im Katalog\nHinweis: search_addons verwenden"
            )
        status = await ctx.installed()
        details = {**entry.details(_version(status)), "installed": _installed_flag(entry, status),
                   "catalog": state}  # fmt: skip
        if readme:
            text = await service.readme(entry)
            details["readme"] = text
            details["readme_note"] = UNTRUSTED_NOTE if text else "README nicht abrufbar"
        return details

    if allow_addon_install:

        @tool
        async def install_addon(
            addon_id: Annotated[str, Field(description="Id from search_addons/get_addon")],
            wait_seconds: Annotated[
                int, Field(ge=0, le=900, description="How long to wait for completion")
            ] = 300,
        ) -> dict[str, Any]:
            """Install an addon or macro through FreeCAD's Addon Manager (needs FreeCAD's opt-in). FreeCAD shows the user
            a confirmation dialog - ask in the chat first. Workbenches need a FreeCAD restart afterwards."""
            service, state = await ctx.catalog()
            entry = service.find(addon_id)
            if entry is None:
                raise ToolError(f"[not_found] No addon '{addon_id}' in the catalog\nHint: use search_addons")
            status = await ctx.installed()
            if status is None:
                raise ToolError("[bridge_unavailable] FreeCAD is not reachable - cannot install")
            reason = _install_blocker(entry, status)
            if reason:
                raise ToolError(
                    f"[validation] {reason}\nHint: install it with FreeCAD's Addon Manager instead"
                )
            job = await ctx.call(
                "install_addon", "addons.install", addon_id=entry.id, kind=entry.kind, entry=service.raw(entry),
                details=entry.details(_version(status)), branch=entry.branch,
            )  # fmt: skip
            deadline = time.monotonic() + wait_seconds
            while not job["done"] and time.monotonic() < deadline:
                await asyncio.sleep(1)
                job = await ctx.call("install_addon", "addons.install_status", job_id=job["job_id"])
            if not job["done"]:
                job["hint"] = (
                    "Still running (dialog open or downloading) - call install_addon again for the status."
                )
            if job["state"] == "declined":
                raise ToolError(
                    "[user_declined] Installation declined in the FreeCAD dialog - nothing changed"
                )
            if job["state"] == "failed":
                raise ToolError(
                    f"[install_failed] {job['message']}\nHint: retry with FreeCAD's Addon Manager"
                )
            return {**job, "catalog": state}

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
