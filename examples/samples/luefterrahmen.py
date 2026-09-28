"""Benchmark sample "Lüfterrahmen": clamp frame 50 mm fan -> 60 mm holder, layout sketch as single source.

Second reference model next to ``referenzmodell.py``. It checks the reference workflow: the mounting
hole pattern is defined exactly once in a layout sketch (construction line of length Mount_Diag
symmetric to the origin, hole circles at its ends, one distance to the frame aligns it); lugs and
screw-head pockets take the hole positions as external geometry, the holes are drilled straight
from the layout sketch. The model grows in stages like the first sample.

    uv run python examples/samples/luefterrahmen.py prompt [--stage N]      # print the exact prompt
    uv run python examples/samples/luefterrahmen.py build [--stage N]       # reference build
    uv run python examples/samples/luefterrahmen.py check [--stage N]       # score the open document
    uv run python examples/samples/luefterrahmen.py screenshot              # refresh luefterrahmen.png

Needs a running ``freecad-buddy`` and FreeCAD with the bridge.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import math
import sys
from collections.abc import Awaitable, Callable, Mapping
from pathlib import Path
from typing import Any

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from buddy_server.config import Settings

HERE = Path(__file__).resolve().parent
SCREENSHOT = HERE / "luefterrahmen.png"
DOCUMENT = "Luefterrahmen"
BODY = "Frame"
LATEST_STAGE = 1
POSITION_TOLERANCE = 0.01  # mm, hole positions, distances, flat outer faces
ARC_SIZE_TOLERANCE = 0.1  # mm, outer X size over the lug arcs (GUI bounding boxes follow the tessellation)

STAGE_PARAMETERS: dict[int, dict[str, float]] = {
    1: {
        "Fan_W": 50,
        "Fan_H": 12,
        "Fit": 0.15,
        "Wall": 2,
        "Corner_R": 3,
        "Rim_T": 1.2,
        "Rim_W": 1.5,
        "Notch_W": 4,
        "Notch_Offset": 10,
        "Mount_Diag": 70,
        "Mount_Hole_D": 3.4,
        "Head_D": 6.5,
        "Lug_D": 10,
        "Lug_Floor": 3,
    },
}
PROBES: tuple[dict[str, float], ...] = ({"Mount_Diag": 74}, {"Wall": 2.5})
"""Parametric probes of the check (one at a time, undone afterwards)."""

PROMPT_HEADS: dict[int, str] = {
    1: "Erstelle mit FreeCAD Buddy ein neues Dokument „Luefterrahmen“ mit genau einem Body „Frame“: einen "
    "Klemmrahmen, in den ein 50-mm-CPU-Lüfter (50 × 50 × 12 mm) von oben gesteckt wird und der mit zwei "
    "Schrauben (Abstand 70 mm) auf eine 60-mm-Lüfterhalterung geschraubt wird.",
}
STAGE_PROMPTS: dict[int, list[str]] = {
    1: [
        "Rahmen außen quadratisch, mittig zum Ursprung auf der XY-Ebene: Innenmaß Lüfterbreite plus 0,15 mm "
        "Spiel je Seite, Wand 2 mm, äußere Ecken R 3 mm. Höhe = Lüfterhöhe plus Innenrand.",
        "Unten ein umlaufender Innenrand als Anschlag, 1,5 mm breit und 1,2 mm dick; darüber die Lüftertasche "
        "12 mm tief von oben.",
        "Kabelkerbe 4 mm breit durch die Wand auf der +Y-Seite, Mitte 10 mm von der inneren Ecke bei −X, von "
        "oben bis auf den Innenrand.",
        "Lochbild genau einmal in einer Layout-Skizze: eine Konstruktionslinie der Länge Mount_Diag symmetrisch "
        "zum Ursprung, an ihren Enden die zwei Bohrungskreise Ø 3,4 mm. Ein Maß legt den Abstand der "
        "Bohrungsmitte zur Rahmenaußenkante in X auf Wall + Head_D/2 fest, damit richtet sich die Linie aus. "
        "Die Bohrung auf der +X-Seite liegt bei positivem Y.",
        "Außen zwei D-förmige Schraubenlaschen, 10 mm breit, rund um die Bohrungen, bis zur Wandmitte und über "
        "die ganze Rahmenhöhe. Von oben je eine Kopftasche Ø 6,5 mm bis 3 mm über der Unterseite, darunter die "
        "Durchgangsbohrung Ø 3,4 mm als Hole-Feature direkt aus der Layout-Skizze.",
        "Laschen und Kopftaschen übernehmen die Bohrungslage als externe Geometrie aus der Layout-Skizze; keine "
        "andere Skizze enthält ein Lagemaß des Lochbilds.",
        "Keine Fasen und Verrundungen außer den Rahmenecken.",
    ],
}
PROMPT_TAILS: dict[int, list[str]] = {
    1: [
        "Alle Maße als Parameter im VarSet „Parameters“ mit genau diesen Namen: {names}.",
        "Zum Schluss Druckbarkeit prüfen und Ansicht iso. Nicht speichern, nicht exportieren.",
    ],
}
STAGE_FEATURES: dict[int, tuple[str, ...]] = {
    1: ("PartDesign::Pad", "PartDesign::Pocket", "PartDesign::Hole"),
}


def _for_stage(texts: Mapping[int, Any], stage: int) -> Any:
    """Text of the latest stage <= ``stage`` (heads and tails change rarely)."""
    return texts[max(number for number in texts if number <= stage)]


def parameters(stage: int = LATEST_STAGE) -> dict[str, float]:
    values: dict[str, float] = {}
    for number in range(1, stage + 1):
        values.update(STAGE_PARAMETERS[number])
    return values


def prompt(stage: int = LATEST_STAGE) -> str:
    items = [item for number in range(1, stage + 1) for item in STAGE_PROMPTS[number]]
    tail = [line.format(names=", ".join(parameters(stage))) for line in _for_stage(PROMPT_TAILS, stage)]
    lines = [_for_stage(PROMPT_HEADS, stage), ""]
    lines += [f"{index}. {text}" for index, text in enumerate([*items, *tail], 1)]
    return "\n".join(lines)


# --- expected values ------------------------------------------------------------------------------
def frame_size(p: Mapping[str, float]) -> float:
    return p["Fan_W"] + 2 * p["Fit"] + 2 * p["Wall"]


def height(p: Mapping[str, float]) -> float:
    return p["Fan_H"] + p["Rim_T"]


def mount_point(p: Mapping[str, float]) -> tuple[float, float]:
    """Hole centre on the +X side (the -X hole is point-symmetric)."""
    x = p["Fan_W"] / 2 + p["Fit"] + 2 * p["Wall"] + p["Head_D"] / 2
    return x, math.sqrt((p["Mount_Diag"] / 2) ** 2 - x**2)


def _lug_fits_straight_wall(p: Mapping[str, float]) -> bool:
    """The volume formula assumes the lugs sit on the straight wall, clear of the corner rounding."""
    _, y = mount_point(p)
    return y + p["Lug_D"] / 2 <= frame_size(p) / 2 - p["Corner_R"]


def expected_volume(p: Mapping[str, float], stage: int = LATEST_STAGE) -> float:
    del stage  # one stage so far; later stages add their terms here
    if not _lug_fits_straight_wall(p):
        raise ValueError("lugs reach into the frame corner rounding - formula not valid")
    s, h, r = frame_size(p), height(p), p["Corner_R"]
    x, _ = mount_point(p)
    lug_outside = math.pi * (p["Lug_D"] / 2) ** 2 / 2 + (x - s / 2) * p["Lug_D"]
    solid = (s**2 - (4 - math.pi) * r**2 + 2 * lug_outside) * h
    inner = p["Fan_W"] + 2 * p["Fit"]
    cuts = (
        inner**2 * p["Fan_H"]  # fan pocket
        + (inner - 2 * p["Rim_W"]) ** 2 * p["Rim_T"]  # opening inside the rim
        + p["Notch_W"] * p["Wall"] * p["Fan_H"]  # cable notch
        + 2 * math.pi * (p["Head_D"] / 2) ** 2 * (h - p["Lug_Floor"])  # screw-head pockets
        + 2 * math.pi * (p["Mount_Hole_D"] / 2) ** 2 * p["Lug_Floor"]  # through holes below
    )
    return solid - cuts


def expected_size(p: Mapping[str, float], stage: int = LATEST_STAGE) -> list[float]:
    del stage
    x, _ = mount_point(p)
    return [2 * (x + p["Lug_D"] / 2), frame_size(p), height(p)]


# --- MCP client -------------------------------------------------------------------------------------
Call = Callable[..., Awaitable[Any]]


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


# --- reference build --------------------------------------------------------------------------------
TOP = "Fan_H + Rim_T"


def _lug(sign: int, x: float, y: float, p: Mapping[str, float]) -> list[dict[str, Any]]:
    """D-shaped lug around (sign*x, sign*y): arc away from the frame, straight root inside the wall."""
    r, root = p["Lug_D"] / 2, p["Fan_W"] / 2 + p["Fit"] + p["Wall"] / 2
    cx, cy = sign * x, sign * y
    start, end = (-90, 90) if sign > 0 else (90, 270)
    return [
        {"type": "arc", "center": [cx, cy], "radius": r, "start_angle": start, "end_angle": end},
        {"type": "line", "start": [cx, cy + sign * r], "end": [sign * root, cy + sign * r]},
        {"type": "line", "start": [sign * root, cy + sign * r], "end": [sign * root, cy - sign * r]},
        {"type": "line", "start": [sign * root, cy - sign * r], "end": [cx, cy - sign * r]},
    ]


def _lug_constraints(base: int, external: str, sign: int) -> list[dict[str, Any]]:
    arc, top, side, bottom = (f"g{base + i}" for i in range(4))
    root = {"a": "origin", "b": f"{side}.start"} if sign > 0 else {"a": f"{side}.start", "b": "origin"}
    suffix = "" if sign > 0 else "_Neg"
    return [
        {"type": "coincident", "a": f"{arc}.end", "b": f"{top}.start"},
        {"type": "coincident", "a": f"{top}.end", "b": f"{side}.start"},
        {"type": "coincident", "a": f"{side}.end", "b": f"{bottom}.start"},
        {"type": "coincident", "a": f"{bottom}.end", "b": f"{arc}.start"},
        {"type": "horizontal", "a": top},
        {"type": "horizontal", "a": bottom},
        {"type": "vertical", "a": side},
        {"type": "vertical", "a": f"{arc}.center", "b": f"{arc}.end"},
        {"type": "vertical", "a": f"{arc}.center", "b": f"{arc}.start"},
        {"type": "radius", "a": arc, "value": "Lug_D / 2", "name": f"Lug_R{suffix}"},
        {"type": "coincident", "a": f"{arc}.center", "b": f"{external}.center"},
        {"type": "distance_x", **root, "value": "Fan_W / 2 + Fit + Wall / 2", "name": f"Lug_Root{suffix}"},
    ]


async def build(call: Call, stage: int = LATEST_STAGE, view: bool = True) -> None:
    """Reference solution - the baseline the models are compared against (tool calls: see the MD).

    ``view=False`` skips the final ``set_view`` (headless FreeCAD has no 3D view).
    """
    p = parameters(stage)
    x, y = mount_point(p)
    edge = frame_size(p) / 2
    await call("document", action="new", name=DOCUMENT)
    await call("set_parameters", parameters=dict(p))
    await call("create_body", label=BODY)
    # layout sketch: the only source of the hole pattern
    await call("create_sketch", plane="XY", purpose="Layout", offset=TOP)
    await call("add_geometry", sketch="Sketch_Layout", items=[
        {"type": "line", "start": [-x, -y], "end": [x, y], "construction": True},
        {"type": "circle", "center": [x, y], "radius": p["Mount_Hole_D"] / 2},
        {"type": "circle", "center": [-x, -y], "radius": p["Mount_Hole_D"] / 2},
        {"type": "line", "start": [edge, -5], "end": [edge, 5], "construction": True},
    ])  # fmt: skip
    await call("add_constraints", sketch="Sketch_Layout", items=[
        {"type": "symmetric", "a": "g0.start", "b": "g0.end", "about": "origin"},
        {"type": "distance", "a": "g0", "value": "Mount_Diag", "name": "Mount_Diag"},
        {"type": "coincident", "a": "g1.center", "b": "g0.end"},
        {"type": "coincident", "a": "g2.center", "b": "g0.start"},
        {"type": "diameter", "a": "g1", "value": "Mount_Hole_D", "name": "Mount_Hole_D"},
        {"type": "equal", "a": "g1", "b": "g2"},
        {"type": "symmetric", "a": "g3.start", "b": "g3.end", "about": "x_axis"},
        {"type": "distance", "a": "g3", "value": 10, "name": "Frame_Edge_Length"},
        {"type": "distance_x", "a": "origin", "b": "g3.start", "value": "Fan_W / 2 + Fit + Wall", "name": "Frame_X"},
        {"type": "distance_x", "a": "g3.start", "b": "g1.center", "value": "Wall + Head_D / 2",
         "name": "Hole_To_Frame"},
    ])  # fmt: skip
    # frame and lugs
    size = "Fan_W + 2 * Fit + 2 * Wall"
    await call("create_sketch", plane="XY", purpose="Frame")
    await call("add_profile", sketch="Sketch_Frame", kind="rounded_rectangle",
               params={"width": size, "height": size, "radius": "Corner_R"}, prefix="Frame")  # fmt: skip
    await call("pad", sketch="Sketch_Frame", length=TOP, purpose="Frame")
    await call("create_sketch", plane="XY", purpose="Lugs")
    await call("add_geometry", sketch="Sketch_Lugs", items=[
        {"type": "external", "source": "Sketch_Layout", "element": "g1"},
        {"type": "external", "source": "Sketch_Layout", "element": "g2"},
        *_lug(1, x, y, p), *_lug(-1, x, y, p),
    ])  # fmt: skip
    await call("add_constraints", sketch="Sketch_Lugs",
               items=[*_lug_constraints(0, "x0", 1), *_lug_constraints(4, "x1", -1)])  # fmt: skip
    await call("pad", sketch="Sketch_Lugs", length=TOP, purpose="Lugs")
    # fan pocket, rim, cable notch
    inner = "Fan_W + 2 * Fit"
    await call("create_sketch", plane="XY", purpose="FanPocket", offset=TOP)
    await call("add_profile", sketch="Sketch_FanPocket", kind="rectangle",
               params={"width": inner, "height": inner}, prefix="FanPocket")  # fmt: skip
    await call("pocket", sketch="Sketch_FanPocket", depth="Fan_H", purpose="FanPocket")
    opening = "Fan_W + 2 * Fit - 2 * Rim_W"
    await call("create_sketch", plane="XY", purpose="RimOpening", offset=TOP)
    await call("add_profile", sketch="Sketch_RimOpening", kind="rectangle",
               params={"width": opening, "height": opening}, prefix="RimOpening")  # fmt: skip
    await call("pocket", sketch="Sketch_RimOpening", mode="through_all", purpose="RimOpening")
    await call("create_sketch", plane="XY", purpose="CableNotch", offset=TOP)
    await call("add_profile", sketch="Sketch_CableNotch", kind="rectangle", prefix="Notch", params={
        "width": "Notch_W", "height": "Wall + 2",
        "center": ["Notch_Offset - Fan_W / 2 - Fit", "Fan_W / 2 + Fit + Wall / 2"],
    })  # fmt: skip
    await call("pocket", sketch="Sketch_CableNotch", depth="Fan_H", purpose="CableNotch")
    # screw heads follow the layout holes, the holes come straight from the layout sketch
    await call("create_sketch", plane="XY", purpose="ScrewHeads", offset=TOP)
    await call("add_geometry", sketch="Sketch_ScrewHeads", items=[
        {"type": "external", "source": "Sketch_Layout", "element": "g1"},
        {"type": "external", "source": "Sketch_Layout", "element": "g2"},
        {"type": "circle", "center": [x - 2, y - 2], "radius": 3},
        {"type": "circle", "center": [-x + 2, -y + 2], "radius": 3},
    ])  # fmt: skip
    await call("add_constraints", sketch="Sketch_ScrewHeads", items=[
        {"type": "coincident", "a": "g0.center", "b": "x0.center"},
        {"type": "coincident", "a": "g1.center", "b": "x1.center"},
        {"type": "diameter", "a": "g0", "value": "Head_D", "name": "Head_D"},
        {"type": "equal", "a": "g0", "b": "g1"},
    ])  # fmt: skip
    await call("pocket", sketch="Sketch_ScrewHeads", depth="Fan_H + Rim_T - Lug_Floor", purpose="ScrewHeads")
    await call("hole", sketch="Sketch_Layout", diameter="Mount_Hole_D", purpose="MountScrews")
    await call("check_printability", target=BODY)
    if view:
        await call("set_view", view="iso", fit=True)


# --- check --------------------------------------------------------------------------------------------
def _check(results: list[dict[str, Any]], stage: int, name: str, ok: bool, detail: str) -> None:
    results.append({"stage": stage, "check": name, "ok": bool(ok), "detail": detail})


async def _centers(call: Call, radius: float) -> list[tuple[float, float]]:
    """Unique (x, y) centres of circular edges with this radius on the body, sorted by x."""
    try:
        found = await call("select_geometry", selector=f"edges:circular,radius={radius:g}", body=BODY,
                           document=DOCUMENT)  # fmt: skip
    except (RuntimeError, AssertionError):
        return []
    unique = {(round(m["center"][0], 4), round(m["center"][1], 4)) for m in found["matches"]}
    return sorted(unique)


async def _hole_pattern(call: Call, p: Mapping[str, float]) -> tuple[bool, str, bool, str]:
    """(holes at the expected spots, detail, head pockets coaxial, detail)."""
    holes = await _centers(call, p["Mount_Hole_D"] / 2)
    heads = await _centers(call, p["Head_D"] / 2)
    x, y = mount_point(p)
    wanted = [(-x, -y), (x, y)]
    holes_ok = len(holes) == 2 and all(
        abs(h[0] - w[0]) <= POSITION_TOLERANCE and abs(h[1] - w[1]) <= POSITION_TOLERANCE
        for h, w in zip(holes, wanted, strict=True)
    )
    distance = math.dist(*holes) if len(holes) == 2 else 0.0
    heads_ok = len(heads) == len(holes) == 2 and all(
        math.dist(a, b) <= POSITION_TOLERANCE for a, b in zip(heads, holes, strict=True)
    )
    return (
        holes_ok and abs(distance - p["Mount_Diag"]) <= POSITION_TOLERANCE,
        f"Bohrungen {holes}, Abstand {distance:.3f} (Soll ±({x:.3f}, {y:.3f}), {p['Mount_Diag']:g})",
        heads_ok,
        f"Kopftaschen {heads}",
    )


async def _body_shape(call: Call) -> dict[str, Any]:
    return (await call("get_object", ref=BODY, document=DOCUMENT)).get("shape", {})


def _size_ok(size: list[float], expected: list[float]) -> bool:
    """X spans the lug arcs: with a running GUI FreeCAD derives bounding boxes from the display
    tessellation, which cuts the arc extremes (74.73 instead of 74.80 mm). Y and Z are flat faces."""
    tolerances = (ARC_SIZE_TOLERANCE, POSITION_TOLERANCE, POSITION_TOLERANCE)
    return len(size) == 3 and all(abs(a - e) <= t for a, e, t in zip(size, expected, tolerances, strict=True))


async def check(call: Call, stage: int = LATEST_STAGE) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    p = parameters(stage)
    tree = await call("get_model_tree", document=DOCUMENT)
    bodies = [node for node in tree["objects"] if node["type"] == "PartDesign::Body"]
    _check(results, 1, f"genau ein Body „{BODY}“", [b["label"] for b in bodies] == [BODY],
           str([b["label"] for b in bodies]))  # fmt: skip
    features = [f for body in bodies for f in body["features"]]
    sketches = [f for f in features if f["type"] == "Sketcher::SketchObject"]
    _check(results, 1, "alle Features gültig", all(f["valid"] for f in features), f"{len(features)} Objekte")
    _check(results, 1, "keine Label-Probleme", not tree["label_issues"], str(tree["label_issues"]))
    _check(results, 1, "alle Skizzen DoF 0", all(s.get("dof") == 0 for s in sketches),
           str({s["label"]: s.get("dof") for s in sketches}))  # fmt: skip
    listed = {entry["name"]: entry["value"] for entry in await call("list_parameters", document=DOCUMENT)}
    for number in range(1, stage + 1):
        own = STAGE_PARAMETERS[number]
        missing = [k for k in own if k not in listed]
        wrong = [k for k in own if k in listed and abs(float(listed[k]) - own[k]) > 1e-6]
        _check(results, number, "Parameter vollständig und korrekt", not missing and not wrong,
               f"fehlend={missing} falsch={wrong}")  # fmt: skip
    types = {f["type"] for f in features}
    for number in range(1, stage + 1):
        for type_id in STAGE_FEATURES[number]:
            _check(results, number, f"Feature {type_id.split('::')[1]}", type_id in types, type_id)

    shape = await _body_shape(call)
    volume, target = shape.get("volume", 0.0), expected_volume(p, stage)
    _check(results, stage, "Volumen", abs(volume - target) <= 1.0, f"{volume:.1f} (Soll {target:.1f} ± 1)")
    size = shape.get("bound_box", {}).get("size", [])
    _check(results, stage, "Abmessungen", _size_ok(size, expected_size(p, stage)),
           f"{size} (Soll {[round(v, 3) for v in expected_size(p, stage)]}, X ± {ARC_SIZE_TOLERANCE}, "
           f"Y/Z ± {POSITION_TOLERANCE})")  # fmt: skip
    holes_ok, holes_detail, heads_ok, heads_detail = await _hole_pattern(call, p)
    _check(results, 1, "Bohrungen: Lage und Abstand Mount_Diag (gemessen)", holes_ok, holes_detail)
    _check(results, 1, "Kopftaschen koaxial zu den Bohrungen", heads_ok, heads_detail)

    # single source: exactly one sketch binds Mount_Diag, dependent sketches reference it externally
    bound, referencing = [], []
    for sketch in sketches:
        info = await call("get_object", ref=sketch["label"], document=DOCUMENT)
        if any("Mount_Diag" in str(expr) for expr in (info.get("expressions") or {}).values()):
            bound.append(sketch["label"])
    for sketch in sketches:
        report = await call("analyze_sketch", sketch=sketch["label"], document=DOCUMENT)
        if bound and any(e.get("source") == bound[0] for e in report.get("external", [])):
            referencing.append(sketch["label"])
    _check(results, 1, "Lochbild genau eine Quelle (Mount_Diag in einer Skizze)", len(bound) == 1, str(bound))
    _check(results, 1, "Laschen und Kopftaschen referenzieren das Layout extern", len(referencing) >= 2,
           str(referencing))  # fmt: skip

    # parametrics: every probe moves holes, head pockets and lugs together; undone afterwards
    for probe in PROBES:
        changed = {**p, **probe}
        name = ", ".join(f"{k} {v:g}" for k, v in probe.items())
        await call("set_parameters", parameters=dict(probe), document=DOCUMENT)
        try:
            probe_volume = (await _body_shape(call)).get("volume", 0.0)
            probe_holes, detail, probe_heads, _ = await _hole_pattern(call, changed)
        finally:
            await call("undo", steps=1, document=DOCUMENT)
        target = expected_volume(changed, stage)
        _check(results, stage, f"Parametrik ({name})", probe_holes and probe_heads
               and abs(probe_volume - target) <= 1.0,
               f"Volumen {probe_volume:.1f} (Soll {target:.1f} ± 1); {detail}")  # fmt: skip

    passed = sum(r["ok"] for r in results)
    return {"sample": "luefterrahmen", "stage": stage, "score": f"{passed}/{len(results)}", "checks": results}


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
            print(f"Lüfterrahmen Stufe {stage} gebaut ({call.calls} Tool-Aufrufe)")
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
