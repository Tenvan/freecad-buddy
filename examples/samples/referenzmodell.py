"""Benchmark sample "Referenzmodell": reference build, deterministic check, screenshot.

The model grows in stages (1 = base plate with corner holes, 2 = handle, 3 = box with corner
supports as a second body, …). Every stage adds
parameters, features and checks; earlier stages stay unchanged, so results remain comparable.

Compare LLMs / thinking levels: let each model build the part from the prompt of a stage in
``referenzmodell.md`` (fresh FreeCAD document), then run ``check``. All checks use tool results
only, so scores are reproducible.

    uv run python examples/samples/referenzmodell.py prompt [--stage N]      # print the exact prompt
    uv run python examples/samples/referenzmodell.py build [--stage N]       # reference build
    uv run python examples/samples/referenzmodell.py check [--stage N]       # score the open document
    uv run python examples/samples/referenzmodell.py screenshot              # refresh referenzmodell.png

Needs a running ``freecad-buddy`` and FreeCAD with the bridge.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import math
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from buddy_server.config import Settings

HERE = Path(__file__).resolve().parent
SCREENSHOT = HERE / "referenzmodell.png"
DOCUMENT = "Referenzmodell"
LATEST_STAGE = 5
BOX_STAGE = 3  # from here the document holds a second body "Box"
PIN_STAGE = 4  # pins on the supports, matching holes in the plate
ASSEMBLY_STAGE = 5  # threads, materials, Assembly4 assembly with fasteners, exploded configuration

# Addons a stage needs (ids of search_addons/get_addon); build and check verify them first.
STAGE_ADDONS: dict[int, tuple[str, ...]] = {ASSEMBLY_STAGE: ("fasteners", "Assembly4")}
WASHER_THICKNESS = 2.0  # ISO 7089 M10
EXPLODE_Z = {"Box": 0.0, "Plate": 60.0, "ISO7089": 80.0, "ISO4032": 100.0}
THREAD_TOLERANCE = 0.25  # thread volume vs. the Pappus estimate (the profile end at the pin tip varies)

STAGE_PARAMETERS: dict[int, dict[str, float]] = {
    1: {"Plate_Length": 200, "Plate_Width": 100, "Plate_Thickness": 5},
    2: {"Handle_Diameter": 10, "Handle_Clearance": 30, "Handle_Bend_Radius": 10},
    3: {"Box_Clearance": 0.2, "Box_Wall": 3, "Box_Floor": 3, "Box_Height": 100, "Support_Radius": 35},
    4: {"Pin_Diameter": 10, "Pin_Edge_Distance": 15, "Pin_Protrusion": 15},
    5: {"Thread_Pitch": 1.5},
}
PROMPT_HEADS: dict[int, str] = {
    1: "Erstelle mit FreeCAD Buddy ein neues Dokument „Referenzmodell“ mit genau einem Body „Plate“:",
    BOX_STAGE: "Erstelle mit FreeCAD Buddy ein neues Dokument „Referenzmodell“ mit genau zwei Bodies, "
    "„Plate“ (Deckel) und „Box“ (Kasten):",
}
STAGE_PROMPTS: dict[int, list[str]] = {
    1: ["Grundplatte 200 × 100 × 5 mm, mittig zum Ursprung auf der XY-Ebene, Länge in X."],
    2: [
        "Mittig ein Haltegriff als runde Stange Ø 10 mm mit gerundeten Ecken (Biegeradius 10 mm auf der "
        "Mittellinie). Beinabstand 50 % der Plattenlänge in X-Richtung, lichte Höhe 30 mm über der "
        "Plattenoberseite. Die Beine reichen durch die ganze Platte. Der Beinabstand ist ein Ausdruck von "
        "Plate_Length.",
    ],
    3: [
        "Unter dem Deckel ein Kasten „Box“, außen 100 mm hoch, in den die Platte vertieft eingelegt wird: "
        "Innenmaß gleich Plattenmaß plus 0,2 mm Spiel je Seite, Wand 3 mm, Boden 3 mm. In den vier "
        "Innenecken je eine viertelrunde Auflage mit Radius 35 mm (Mittelpunkt in der Innenecke), vom "
        "Kastenboden bis unter die Platte. Einbaulage: Die Plattenunterseite liegt bei z = 0 auf den "
        "Auflagen, die Plattenoberseite schließt bündig mit dem Kastenrand ab. Alle Kastenmaße sind "
        "Ausdrücke der Plattenmaße und von Box_Height.",
    ],
    4: [
        "Auf jeder der vier Auflagen ein runder Stift Ø 10 mm (M10) nach oben, Mittelpunkt 15 mm von "
        "beiden Plattenrändern. Der Stift ragt 15 mm über die Plattenoberseite hinaus (Überstand für eine "
        "M10-Mutter mit Scheibe, das Gewinde wird nicht modelliert). Danach in der Platte die passenden "
        "Durchgangsbohrungen: Stiftdurchmesser plus Box_Clearance Spiel je Seite, als Ausdruck.",
    ],
    5: [
        "Benötigte Addons: Fasteners Workbench und Assembly4 (fehlt eines: nach Rückfrage installieren, "
        "FreeCAD neu starten und neu beginnen). Auf jeden der vier Stifte oberhalb der Platte ein echtes "
        "Außengewinde M10 × 1,5 (ISO-Profil, Steigung Thread_Pitch) über die ganze Überstandslänge.",
        "Material und Farbe: Deckel ABS rot, Kasten PLA gelb.",
        "Eine Assembly4-Baugruppe „Assembly“ mit Kasten und Deckel in Einbaulage. Auf jeden Stift eine "
        "Scheibe ISO 7089 M10 auf die Plattenoberseite und darauf eine Mutter ISO 4032 M10.",
        "Explosionsansicht als Assembly4-Konfiguration „Exploded“: Deckel +60 mm, Scheiben +80 mm, Muttern "
        "+100 mm in Z; die Einbaulage heißt „Assembled“.",
    ],
}
PROMPT_TAILS: dict[int, str] = {
    1: "Zum Schluss Druckbarkeit prüfen und Ansicht iso. Nicht speichern, nicht exportieren.",
    BOX_STAGE: "Zum Schluss Druckbarkeit beider Bodies prüfen und Ansicht iso. Nicht speichern, nicht "
    "exportieren.",
}

STAGE_FEATURES: dict[int, tuple[str, ...]] = {
    1: ("PartDesign::Pad",),
    2: ("PartDesign::AdditivePipe",),
    3: ("PartDesign::Pocket",),
    4: ("PartDesign::Hole",),
    5: ("PartDesign::SubtractiveHelix", "PartDesign::MultiTransform"),
}


def _for_stage(texts: Mapping[int, str], stage: int) -> str:
    """Text valid for ``stage``: the entry of the highest stage not above it."""
    return texts[max(number for number in texts if number <= stage)]


def parameters(stage: int) -> dict[str, float]:
    merged: dict[str, float] = {}
    for number in range(1, stage + 1):
        merged.update(STAGE_PARAMETERS[number])
    return merged


def prompt(stage: int = LATEST_STAGE) -> str:
    """The exact prompt of a stage: head, the steps of stages 1..N, parameter names, tail."""
    steps = [step for number in range(1, stage + 1) for step in STAGE_PROMPTS[number]]
    names = ", ".join(parameters(stage))
    steps.append(f"Alle Maße als Parameter im VarSet „Parameters“ mit genau diesen Namen: {names}.")
    steps.append(_for_stage(PROMPT_TAILS, stage))
    head = _for_stage(PROMPT_HEADS, stage)
    return "\n".join([head, "", *(f"{index}. {step}" for index, step in enumerate(steps, 1))])


def expected_volume(p: Mapping[str, float], stage: int = LATEST_STAGE) -> float:
    """Plate: block; stage 2 + swept handle (Pappus) - the two leg pieces inside the plate; stage 4 - four
    pin holes with fit clearance."""
    volume = p["Plate_Length"] * p["Plate_Width"] * p["Plate_Thickness"]
    if stage >= 2:
        section = math.pi * (p["Handle_Diameter"] / 2) ** 2
        legs, radius = p["Plate_Length"] / 2, p["Handle_Bend_Radius"]
        height = p["Plate_Thickness"] + p["Handle_Clearance"] + p["Handle_Diameter"] / 2
        centre_line = 2 * height + legs - 4 * radius + math.pi * radius
        volume += section * centre_line - 2 * section * p["Plate_Thickness"]
    if stage >= PIN_STAGE:
        hole = p["Pin_Diameter"] / 2 + p["Box_Clearance"]
        volume -= 4 * math.pi * hole**2 * p["Plate_Thickness"]
    return volume


def expected_size(p: Mapping[str, float], stage: int = LATEST_STAGE) -> list[float]:
    height = p["Plate_Thickness"]
    if stage >= 2:
        height += p["Handle_Clearance"] + p["Handle_Diameter"]
    return [p["Plate_Length"], p["Plate_Width"], height]


def _box_outer(p: Mapping[str, float]) -> tuple[float, float, float]:
    inner_length = p["Plate_Length"] + 2 * p["Box_Clearance"]
    inner_width = p["Plate_Width"] + 2 * p["Box_Clearance"]
    return inner_length + 2 * p["Box_Wall"], inner_width + 2 * p["Box_Wall"], inner_length * inner_width


def _pin_length(p: Mapping[str, float]) -> float:
    """Pins start on the supports (z = 0) and stick out above the plate by Pin_Protrusion."""
    return p["Plate_Thickness"] + p["Pin_Protrusion"]


def expected_box_volume(p: Mapping[str, float], stage: int = LATEST_STAGE) -> float:
    """Stage 3: outer block - cavity (above the floor) + four quarter discs from the floor up to the
    plate = one full disc. Stage 4: + four pins through the plate and beyond it."""
    length, width, inner_area = _box_outer(p)
    cavity = inner_area * (p["Box_Height"] - p["Box_Floor"])
    support_height = p["Box_Height"] - p["Box_Floor"] - p["Plate_Thickness"]
    volume = length * width * p["Box_Height"] - cavity + math.pi * p["Support_Radius"] ** 2 * support_height
    if stage >= PIN_STAGE:
        volume += 4 * math.pi * (p["Pin_Diameter"] / 2) ** 2 * _pin_length(p)
    return volume


def expected_box_z(p: Mapping[str, float], stage: int = LATEST_STAGE) -> list[float]:
    """Assembly position: supports end at z = 0 under the plate, the rim is flush with its top;
    from stage 4 the pins stick out above it."""
    top = p["Plate_Thickness"] + (p["Pin_Protrusion"] if stage >= PIN_STAGE else 0)
    return [p["Plate_Thickness"] - p["Box_Height"], top]


def pin_positions(p: Mapping[str, float]) -> list[tuple[float, float]]:
    x, y = p["Plate_Length"] / 2 - p["Pin_Edge_Distance"], p["Plate_Width"] / 2 - p["Pin_Edge_Distance"]
    return [(sx * x, sy * y) for sx in (-1, 1) for sy in (-1, 1)]


def expected_thread_removal(p: Mapping[str, float]) -> float:
    """Pappus estimate of the four thread grooves: turns x 2 pi x centroid radius x groove area.

    ISO external thread depth h3 = 0.6134 P; the 60° groove inside the major diameter is a triangle of
    area h3² tan 30° whose centroid lies h3/3 inside the major radius.
    """
    pitch = p["Thread_Pitch"]
    depth = 0.6134 * pitch
    area = depth**2 * math.tan(math.radians(30))
    radius = p["Pin_Diameter"] / 2 - depth / 3
    turns = p["Pin_Protrusion"] / pitch
    return 4 * turns * 2 * math.pi * radius * area


def required_addons(stage: int) -> list[str]:
    return [addon for number in range(1, stage + 1) for addon in STAGE_ADDONS.get(number, ())]


def expected_box_size(p: Mapping[str, float], stage: int = LATEST_STAGE) -> list[float]:
    length, width, _ = _box_outer(p)
    bottom, top = expected_box_z(p, stage)
    return [length, width, top - bottom]


class Client:
    def __init__(self, session: ClientSession) -> None:
        self.session = session
        self.calls = 0

    async def __call__(self, tool: str, /, **arguments: Any) -> Any:
        self.calls += 1
        result = await self.session.call_tool(tool, arguments)
        text = "\n".join(getattr(block, "text", "") for block in result.content)
        if result.is_error:
            raise RuntimeError(f"{tool}: {text}")
        content = result.structured_content
        data = content.get("result", content) if content and set(content) == {"result"} else content
        return data if data is not None else (json.loads(text) if text else None)


async def build(call: Client, stage: int = LATEST_STAGE) -> None:
    """Reference solution - the baseline the models are compared against (tool calls: see the MD)."""
    missing = [addon for addon, ok in (await _addon_status(call, stage)).items() if not ok]
    if missing:
        raise RuntimeError(f"Addons fehlen: {', '.join(missing)} - install_addon, dann FreeCAD neu starten")
    await call("new_document", name=DOCUMENT)
    await call("set_parameters", parameters=STAGE_PARAMETERS[1])
    await call("create_body", label="Plate")
    await call("create_sketch", plane="XY", purpose="Plate")
    await call("add_profile", sketch="Sketch_Plate", kind="rectangle",
               params={"width": "Plate_Length", "height": "Plate_Width"}, prefix="Plate")  # fmt: skip
    await call("pad", sketch="Sketch_Plate", length="Plate_Thickness", purpose="Plate")
    if stage >= 2:
        await call("set_parameters", parameters=STAGE_PARAMETERS[2])
        await call("create_sketch", plane="XZ", purpose="HandlePath")
        await call("add_profile", sketch="Sketch_HandlePath", kind="u_path", prefix="Handle", params={
            "length": "Plate_Length / 2", "height": "Plate_Thickness + Handle_Clearance + Handle_Diameter / 2",
            "radius": "Handle_Bend_Radius"})  # fmt: skip
        await call("create_sketch", plane="XY", purpose="HandleSection")
        await call("add_profile", sketch="Sketch_HandleSection", kind="circle", prefix="Handle",
                   params={"diameter": "Handle_Diameter", "center": ["-Plate_Length / 4", 0]})  # fmt: skip
        await call("sweep", profile="Sketch_HandleSection", path="Sketch_HandlePath", purpose="Handle")
    if stage >= BOX_STAGE:
        await _build_box(call)
    if stage >= PIN_STAGE:
        await _build_pins(call)
    if stage >= ASSEMBLY_STAGE:
        await _build_assembly(call)
    if stage >= BOX_STAGE:
        await call("check_printability", target="Plate")
        await call("check_printability", target="Box")
    else:
        await call("check_printability")
    await call("set_view", view="iso")


def _quarter_disc(corner_x: float, corner_y: float, radius: float, start: float) -> list[dict[str, Any]]:
    """Arc (90°) around an inner box corner plus its two radii, as add_geometry items."""
    ends = [(corner_x + radius * math.cos(math.radians(a)), corner_y + radius * math.sin(math.radians(a)))
            for a in (start, start + 90)]  # fmt: skip
    return [
        {
            "type": "arc",
            "center": [corner_x, corner_y],
            "radius": radius,
            "start_angle": start,
            "end_angle": start + 90,
        },
        {"type": "line", "start": [corner_x, corner_y], "end": list(ends[0])},
        {"type": "line", "start": [corner_x, corner_y], "end": list(ends[1])},
    ]


def _quarter_disc_constraints(index: int, start: float, mirror: str | None) -> list[dict[str, Any]]:
    """Close quarter disc ``index`` and tie it to disc 0 (equal radius, symmetric centre)."""
    arc, first, second = (f"g{3 * index + k}" for k in range(3))
    horizontal, vertical = (first, second) if start % 180 == 0 else (second, first)
    items: list[dict[str, Any]] = [
        {"type": "coincident", "a": f"{first}.start", "b": f"{arc}.center"},
        {"type": "coincident", "a": f"{second}.start", "b": f"{arc}.center"},
        {"type": "coincident", "a": f"{first}.end", "b": f"{arc}.start"},
        {"type": "coincident", "a": f"{second}.end", "b": f"{arc}.end"},
        {"type": "horizontal", "a": horizontal},
        {"type": "vertical", "a": vertical},
    ]
    if mirror is None:
        items += [
            {"type": "radius", "a": arc, "value": "Support_Radius", "name": "Support_Radius"},
            {
                "type": "distance_x",
                "a": "origin",
                "b": f"{arc}.center",
                "value": "Plate_Length / 2 + Box_Clearance",
                "name": "Support_Corner_X",
            },
            {
                "type": "distance_y",
                "a": "origin",
                "b": f"{arc}.center",
                "value": "Plate_Width / 2 + Box_Clearance",
                "name": "Support_Corner_Y",
            },
        ]
    else:
        items += [
            {"type": "equal", "a": arc, "b": "g0"},
            {"type": "symmetric", "a": "g0.center", "b": f"{arc}.center", "about": mirror},
        ]
    return items


# Inner box corners (stage values) with the start angle of their quarter arc and the symmetry to disc 0.
SUPPORT_CORNERS = ((1, 1, 180, None), (-1, 1, 270, "y_axis"), (-1, -1, 0, "origin"), (1, -1, 90, "x_axis"))


async def _build_box(call: Client) -> None:
    """Stage 3: box shell below the plate, cavity with fit clearance, four quarter-round supports.

    The supports are drawn in one sketch (four symmetric quarter discs); mirroring one support twice
    is an equally valid way and gives the same volume.
    """
    await call("set_parameters", parameters=STAGE_PARAMETERS[3])
    await call("create_body", label="Box")
    await call("create_sketch", body="Box", plane="XY", offset="Plate_Thickness", purpose="BoxOuter")
    await call("add_profile", sketch="Sketch_BoxOuter", kind="rectangle", prefix="BoxOuter", params={
        "width": "Plate_Length + 2*Box_Clearance + 2*Box_Wall",
        "height": "Plate_Width + 2*Box_Clearance + 2*Box_Wall"})  # fmt: skip
    await call("pad", sketch="Sketch_BoxOuter", length="Box_Height",
               reversed=True, purpose="BoxShell")  # fmt: skip
    await call("create_sketch", body="Box", plane="XY", offset="Plate_Thickness", purpose="BoxCavity")
    await call("add_profile", sketch="Sketch_BoxCavity", kind="rectangle", prefix="BoxInner", params={
        "width": "Plate_Length + 2*Box_Clearance", "height": "Plate_Width + 2*Box_Clearance"})  # fmt: skip
    await call("pocket", sketch="Sketch_BoxCavity", depth="Box_Height - Box_Floor",
               purpose="BoxCavity")  # fmt: skip
    await call("create_sketch", body="Box", plane="XY", purpose="Support")
    p = parameters(3)
    x, y = p["Plate_Length"] / 2 + p["Box_Clearance"], p["Plate_Width"] / 2 + p["Box_Clearance"]
    geometry, constraints = [], []
    for index, (sx, sy, start, mirror) in enumerate(SUPPORT_CORNERS):
        geometry += _quarter_disc(sx * x, sy * y, p["Support_Radius"], start)
        constraints += _quarter_disc_constraints(index, start, mirror)
    await call("add_geometry", sketch="Sketch_Support", items=geometry)
    await call("add_constraints", sketch="Sketch_Support", items=constraints)
    await call("pad", sketch="Sketch_Support", length="Box_Height - Box_Floor - Plate_Thickness", reversed=True,
               purpose="Support")  # fmt: skip


async def _build_pins(call: Client) -> None:
    """Stage 4: four pins up from the supports (Box), then the matching holes in the plate (Plate)."""
    await call("set_parameters", parameters=STAGE_PARAMETERS[4])
    pitch = {"width": "Plate_Length - 2*Pin_Edge_Distance", "height": "Plate_Width - 2*Pin_Edge_Distance"}
    await call("create_sketch", body="Box", plane="XY", purpose="Pins")
    await call("add_profile", sketch="Sketch_Pins", kind="hole_rect", prefix="Pins",
               params={**pitch, "diameter": "Pin_Diameter"})  # fmt: skip
    await call("pad", sketch="Sketch_Pins", length="Plate_Thickness + Pin_Protrusion", purpose="Pins")
    await call("create_sketch", body="Plate", plane="XY", offset="Plate_Thickness", purpose="PinHoles")
    await call("add_profile", sketch="Sketch_PinHoles", kind="hole_rect", prefix="PinHoles",
               params={**pitch, "diameter": "Pin_Diameter + 2*Box_Clearance"})  # fmt: skip
    await call("hole", sketch="Sketch_PinHoles", size="M10", diameter="Pin_Diameter + 2*Box_Clearance",
               purpose="PinHoles")  # fmt: skip


async def _addon_status(call: Client, stage: int) -> dict[str, bool]:
    status = {}
    for addon in required_addons(stage):
        status[addon] = bool((await call("get_addon", addon_id=addon, readme=False))["installed"])
    return status


async def _build_assembly(call: Client) -> None:
    """Stage 5: threads on the pins, materials, Assembly4 assembly with washers and nuts, exploded view."""
    await call("set_parameters", parameters=STAGE_PARAMETERS[5])
    corner = ["-(Plate_Length / 2 - Pin_Edge_Distance)", "-(Plate_Width / 2 - Pin_Edge_Distance)"]
    thread = await call("thread", center=corner, diameter="Pin_Diameter", pitch="Thread_Pitch",
                        length="Pin_Protrusion", z_start="Plate_Thickness", body="Box", purpose="Pin")  # fmt: skip
    await call("pattern", features=[thread["feature"]["label"]], kind="grid", count=2, count2=2,
               length="Plate_Length - 2*Pin_Edge_Distance", length2="Plate_Width - 2*Pin_Edge_Distance",
               purpose="PinThreads")  # fmt: skip
    await call("set_material", target="Plate", material="ABS", color="red")
    await call("set_material", target="Box", material="PLA", color="yellow")
    await call("create_assembly")
    await call("add_to_assembly", part="Box")
    await call("add_to_assembly", part="Plate")
    p = parameters(ASSEMBLY_STAGE)
    top = p["Plate_Thickness"]
    washers = await call("add_fastener", type="ISO7089", diameter="M10", purpose="Pin",
                         positions=[[x, y, top] for x, y in pin_positions(p)])  # fmt: skip
    nuts = await call("add_fastener", type="ISO4032", diameter="M10", purpose="Pin",
                      positions=[[x, y, top + WASHER_THICKNESS] for x, y in pin_positions(p)])  # fmt: skip
    moves = {"Plate": [0, 0, EXPLODE_Z["Plate"]]}
    moves |= {f["label"]: [0, 0, EXPLODE_Z["ISO7089"]] for f in washers["fasteners"]}
    moves |= {f["label"]: [0, 0, EXPLODE_Z["ISO4032"]] for f in nuts["fasteners"]}
    await call("explode_assembly", moves=moves, name="Exploded")


def _check(results: list[dict[str, Any]], stage: int, name: str, ok: bool, detail: str) -> None:
    results.append({"stage": stage, "check": name, "ok": bool(ok), "detail": detail})


def _close(actual: list[float], expected: list[float], tolerance: float = 0.01) -> bool:
    return len(actual) == len(expected) and all(
        abs(a - b) <= tolerance for a, b in zip(actual, expected, strict=True)
    )


async def _shape(call: Client, ref: str) -> dict[str, Any] | None:
    """Shape data (volume, bound_box) of a body, or None if it is missing - the check then fails."""
    try:
        return (await call("get_object", ref=ref, document=DOCUMENT)).get("shape")
    except RuntimeError:
        return None


async def check(call: Client, stage: int = LATEST_STAGE) -> dict[str, Any]:
    """Score the open document up to ``stage`` (read-only except one undone parameter probe)."""
    results: list[dict[str, Any]] = []
    expected = parameters(stage)
    tree = await call("get_model_tree", document=DOCUMENT)
    bodies = [o for o in tree["objects"] if o["type"] == "PartDesign::Body"]
    if stage >= BOX_STAGE:
        labels = sorted(b["label"] for b in bodies)
        _check(results, BOX_STAGE, "Bodies Plate und Box", labels == ["Box", "Plate"], ", ".join(labels))
        features = [f for b in bodies for f in b["features"]]
    else:
        _check(results, 1, "ein Body", len(bodies) == 1, f"{len(bodies)} Bodies")
        features = bodies[0]["features"] if bodies else []
    sketches = [f for f in features if f["type"] == "Sketcher::SketchObject"]
    _check(results, 1, "alle Skizzen DoF 0", bool(sketches) and all(s.get("dof") == 0 for s in sketches),
           ", ".join(f"{s['label']}={s.get('dof')}" for s in sketches))  # fmt: skip
    _check(results, 1, "alle Features gültig", all(f["valid"] for f in features), f"{len(features)} Objekte")
    _check(results, 1, "keine Label-Probleme", not tree["label_issues"], str(tree["label_issues"]))
    types = {f["type"] for f in features}
    for number in range(1, stage + 1):
        for type_id in STAGE_FEATURES[number]:
            _check(results, number, f"Feature {type_id.split('::')[1]}", type_id in types, type_id)

    listed = {p["name"]: p["value"] for p in await call("list_parameters", document=DOCUMENT)}
    for number in range(1, stage + 1):
        own = STAGE_PARAMETERS[number]
        missing = [k for k in own if k not in listed]
        wrong = [k for k in own if k in listed and abs(float(listed[k]) - own[k]) > 1e-6]
        _check(results, number, "Parameter vollständig und korrekt", not missing and not wrong,
               f"fehlend={missing} falsch={wrong}")  # fmt: skip

    plate = "Plate" if stage >= BOX_STAGE else None  # two bodies: check_printability needs a target
    stats = (await call("check_printability", document=DOCUMENT, target=plate))["stats"]
    volume, target = stats["volume"], expected_volume(expected, stage)
    _check(results, stage, "Volumen", abs(volume - target) <= 1.0, f"{volume:.1f} (Soll {target:.1f} ± 1)")
    size, target_size = stats["size"], expected_size(expected, stage)
    _check(results, stage, "Abmessungen", _close(size, target_size), f"{size} (Soll {target_size})")
    box_volume = 0.0
    if stage >= BOX_STAGE:
        box = await _shape(call, "Box")
        box_volume = (box or {}).get("volume", 0.0)
        if stage >= ASSEMBLY_STAGE:
            removal = expected_box_volume(expected, stage) - box_volume
            target = expected_thread_removal(expected)
            _check(results, stage, "Kasten Volumen (Gewinde)", abs(removal - target) <= THREAD_TOLERANCE * target,
                   f"Gewinde {removal:.1f} mm³ (Soll {target:.1f} ± {THREAD_TOLERANCE:.0%})")  # fmt: skip
        else:
            target = expected_box_volume(expected, stage)
            _check(results, stage, "Kasten Volumen", abs(box_volume - target) <= 1.0,
                   f"{box_volume:.1f} (Soll {target:.1f} ± 1)")  # fmt: skip
        bound = (box or {}).get("bound_box", {"size": [0, 0, 0], "z": [0, 0]})
        _check(results, stage, "Kasten Abmessungen", _close(bound["size"], expected_box_size(expected, stage)),
               f"{bound['size']} (Soll {expected_box_size(expected, stage)})")  # fmt: skip
        _check(results, stage, "Kasten Einbaulage (z)", _close(bound["z"], expected_box_z(expected, stage)),
               f"{bound['z']} (Soll {expected_box_z(expected, stage)})")  # fmt: skip

    # Parametrics: longer plate -> everything follows (expressions on Plate_Length); undone afterwards.
    probe = {**expected, "Plate_Length": 240}
    await call("set_parameters", parameters={"Plate_Length": 240}, document=DOCUMENT)
    try:
        probe_volume = (await call("check_printability", document=DOCUMENT, target=plate))["stats"]["volume"]
        probe_box = await _shape(call, "Box") if stage >= BOX_STAGE else None
    finally:
        await call("undo", steps=1, document=DOCUMENT)
    target = expected_volume(probe, stage)
    _check(results, stage, "Parametrik (Plate_Length 240)", abs(probe_volume - target) <= 1.0,
           f"{probe_volume:.1f} (Soll {target:.1f} ± 1)")  # fmt: skip
    if stage >= BOX_STAGE:
        volume, target = (probe_box or {}).get("volume", 0.0), expected_box_volume(probe, stage)
        if stage >= ASSEMBLY_STAGE:  # the threads follow the pins: the same volume is cut after the probe
            target -= expected_box_volume(expected, stage) - box_volume
        _check(results, stage, "Kasten Parametrik (Plate_Length 240)", abs(volume - target) <= 1.0,
               f"{volume:.1f} (Soll {target:.1f} ± 1)")  # fmt: skip
    if stage >= ASSEMBLY_STAGE:
        await _check_assembly(call, results, expected)

    passed = sum(r["ok"] for r in results)
    return {
        "sample": "referenzmodell",
        "stage": stage,
        "score": f"{passed}/{len(results)}",
        "checks": results,
    }


def _is_color(rgb: list[float] | None, wanted: tuple[bool, bool, bool]) -> bool:
    """Coarse colour test: each channel above 0.6 exactly where wanted (red = T,F,F; yellow = T,T,F)."""
    return rgb is not None and all((value > 0.6) == on for value, on in zip(rgb, wanted, strict=True))


def _kind(member: dict[str, Any]) -> str:
    return member.get("fastener", {}).get("type") or member.get("linked_object", {}).get("label", "")


async def _placements(call: Client, members: list[dict[str, Any]], configuration: str) -> dict[str, float]:
    """Z of every placed assembly member after applying a configuration (one undoable step)."""
    await call("apply_configuration", name=configuration, document=DOCUMENT)
    heights = {}
    for member in members:
        info = await call("get_object", ref=member["name"], document=DOCUMENT)
        if "placement" in info:
            heights[member["name"]] = info["placement"][2]
    return heights


async def _check_assembly(call: Client, results: list[dict[str, Any]], p: Mapping[str, float]) -> None:
    """Stage 5: addons, materials/colours, assembly content, fastener positions, exploded configuration."""
    stage = ASSEMBLY_STAGE
    status = await _addon_status(call, stage)
    _check(results, stage, "Addons installiert", all(status.values()), str(status))
    plate = await call("get_object", ref="Plate", document=DOCUMENT)
    box = await call("get_object", ref="Box", document=DOCUMENT)
    materials = (plate.get("material"), box.get("material"))
    _check(results, stage, "Material Deckel ABS, Kasten PLA", materials == ("ABS-Generic", "PLA-Generic"),
           f"Deckel {materials[0]}, Kasten {materials[1]}")  # fmt: skip
    colors = (plate.get("color"), box.get("color"))
    _check(results, stage, "Farbe Deckel rot, Kasten gelb",
           _is_color(colors[0], (True, False, False)) and _is_color(colors[1], (True, True, False)),
           f"Deckel {colors[0]}, Kasten {colors[1]}")  # fmt: skip
    try:
        group = (await call("get_object", ref="Assembly", document=DOCUMENT)).get("group", [])
    except RuntimeError:
        group = []
    members = [await call("get_object", ref=m["name"], document=DOCUMENT) for m in group]
    linked = sorted(m["linked_object"]["label"] for m in members if "linked_object" in m)
    _check(results, stage, "Assembly mit Kasten und Deckel", linked == ["Box", "Plate"], str(linked))
    # heights are measured in the assembled state - the build leaves the exploded configuration active
    try:
        assembled = await _placements(call, members, "Assembled")
        exploded = await _placements(call, members, "Exploded")
        await call("undo", steps=2, document=DOCUMENT)
    except RuntimeError as error:
        assembled, exploded = {}, {}
        _check(results, stage, "Konfigurationen Assembled/Exploded", False, str(error)[:200])
    top = p["Plate_Thickness"]
    wanted = sorted((round(x, 2), round(y, 2)) for x, y in pin_positions(p))
    for kind, z in (("ISO7089", top), ("ISO4032", top + WASHER_THICKNESS)):
        parts = [m for m in members if _kind(m) == kind and m["fastener"]["diameter"] == "M10"]
        places = sorted((round(m["placement"][0], 2), round(m["placement"][1], 2)) for m in parts)
        heights = sorted({round(assembled[m["name"]], 2) for m in parts if m["name"] in assembled})
        _check(results, stage, f"4 × {kind} M10 auf den Stiften", places == wanted,
               f"{len(parts)} Stück, Lagen {places}")  # fmt: skip
        _check(results, stage, f"{kind} Einbauhöhe", heights == [round(z, 2)], f"z {heights} (Soll {z})")
    if not exploded:
        return
    rises: dict[str, set[float]] = {}
    for member in members:
        if member["name"] in exploded:
            rise = exploded[member["name"]] - assembled.get(member["name"], 0.0)
            rises.setdefault(_kind(member), set()).add(round(rise, 2))
    ok = all(rises.get(kind) == {value} for kind, value in EXPLODE_Z.items())
    _check(results, stage, "Explosionsansicht „Exploded“", ok,
           f"{ {k: sorted(v) for k, v in rises.items()} } (Soll {EXPLODE_Z})")  # fmt: skip


async def screenshot(call: Client) -> Path:
    result = await call.session.call_tool("screenshot", {"view": "iso", "width": 1200, "height": 800,
                                                         "document": DOCUMENT})  # fmt: skip
    image = next(block for block in result.content if getattr(block, "type", "") == "image")
    SCREENSHOT.write_bytes(base64.b64decode(image.data))  # type: ignore[attr-defined]
    return SCREENSHOT


async def main(command: str, stage: int) -> int:
    settings = Settings()
    headers = {"Authorization": f"Bearer {settings.mcp_token()}"}
    async with (
        httpx2.AsyncClient(headers=headers, timeout=httpx2.Timeout(30, read=600)) as http,
        streamable_http_client(settings.url, http_client=http) as streams,
        ClientSession(streams[0], streams[1]) as session,
    ):
        await session.initialize()
        call = Client(session)
        if command == "build":
            await build(call, stage)
            print(f"Referenz Stufe {stage} gebaut ({call.calls} Tool-Aufrufe)")
        elif command == "check":
            report = await check(call, stage)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            passed, total = report["score"].split("/")
            return 0 if passed == total else 1
        else:
            print(f"Screenshot: {await screenshot(call)}")
    return 0


def _run(command: str, stage: int) -> int:
    if command == "prompt":  # offline: no server needed
        print(prompt(stage))
        return 0
    return asyncio.run(main(command, stage))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", choices=["prompt", "build", "check", "screenshot"])
    parser.add_argument("--stage", type=int, choices=sorted(STAGE_PARAMETERS), default=LATEST_STAGE)
    args = parser.parse_args()
    sys.exit(_run(args.command, args.stage))
