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
LATEST_STAGE = 4
BOX_STAGE = 3  # from here the document holds a second body "Box"
PIN_STAGE = 4  # pins on the supports, matching holes in the plate

STAGE_PARAMETERS: dict[int, dict[str, float]] = {
    1: {"Plate_Length": 200, "Plate_Width": 100, "Plate_Thickness": 5},
    2: {"Handle_Diameter": 10, "Handle_Clearance": 30, "Handle_Bend_Radius": 10},
    3: {"Box_Clearance": 0.2, "Box_Wall": 3, "Box_Floor": 3, "Support_Height": 20, "Support_Radius": 20},
    4: {"Pin_Diameter": 5, "Pin_Edge_Distance": 10},
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
        "Unter dem Deckel ein Kasten „Box“, in den die Platte vertieft eingelegt wird: Innenmaß gleich "
        "Plattenmaß plus 0,2 mm Spiel je Seite, Wand 3 mm, Boden 3 mm. In den vier Innenecken je eine "
        "viertelrunde Auflage mit Radius 20 mm (Mittelpunkt in der Innenecke), 20 mm hoch über dem "
        "Kastenboden. Einbaulage: Die Plattenunterseite liegt bei z = 0 auf den Auflagen, die "
        "Plattenoberseite schließt bündig mit dem Kastenrand ab. Alle Kastenmaße sind Ausdrücke der "
        "Plattenmaße.",
    ],
    4: [
        "Auf jeder der vier Auflagen ein runder Stift Ø 5 mm nach oben, Mittelpunkt 10 mm von beiden "
        "Plattenrändern, Stiftoberkante bündig mit der Plattenoberseite. Danach in der Platte die "
        "passenden Durchgangsbohrungen: Stiftdurchmesser plus Box_Clearance Spiel je Seite, als Ausdruck.",
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


def expected_box_volume(p: Mapping[str, float], stage: int = LATEST_STAGE) -> float:
    """Stage 3: outer block - cavity (support height + plate) + four quarter discs = one full disc.
    Stage 4: + four pins through the plate thickness (their top is flush with the rim)."""
    length, width, inner_area = _box_outer(p)
    height = p["Box_Floor"] + p["Support_Height"] + p["Plate_Thickness"]
    cavity = inner_area * (p["Support_Height"] + p["Plate_Thickness"])
    volume = length * width * height - cavity + math.pi * p["Support_Radius"] ** 2 * p["Support_Height"]
    if stage >= PIN_STAGE:
        volume += 4 * math.pi * (p["Pin_Diameter"] / 2) ** 2 * p["Plate_Thickness"]
    return volume


def expected_box_z(p: Mapping[str, float]) -> list[float]:
    """Assembly position: supports end at z = 0 under the plate, the rim is flush with its top."""
    return [-(p["Box_Floor"] + p["Support_Height"]), p["Plate_Thickness"]]


def expected_box_size(p: Mapping[str, float]) -> list[float]:
    length, width, _ = _box_outer(p)
    bottom, top = expected_box_z(p)
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
    if stage >= BOX_STAGE:
        await call("check_printability", target="Plate")
        await call("check_printability", target="Box")
    else:
        await call("check_printability")
    await call("set_view", view="iso")


def _quarter_disc(corner_x: float, corner_y: float, start: float) -> list[dict[str, Any]]:
    """Arc (radius 20, 90°) around an inner box corner plus its two radii, as add_geometry items."""
    ends = [(corner_x + 20 * math.cos(math.radians(a)), corner_y + 20 * math.sin(math.radians(a)))
            for a in (start, start + 90)]  # fmt: skip
    return [
        {
            "type": "arc",
            "center": [corner_x, corner_y],
            "radius": 20,
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

    The supports are drawn in one sketch: two consecutive ``mirrored`` patterns currently lose a copy
    (the body tip is not advanced), see the known limits in ``referenzmodell.md``.
    """
    await call("set_parameters", parameters=STAGE_PARAMETERS[3])
    await call("create_body", label="Box")
    await call("create_sketch", body="Box", plane="XY", offset="Plate_Thickness", purpose="BoxOuter")
    await call("add_profile", sketch="Sketch_BoxOuter", kind="rectangle", prefix="BoxOuter", params={
        "width": "Plate_Length + 2*Box_Clearance + 2*Box_Wall",
        "height": "Plate_Width + 2*Box_Clearance + 2*Box_Wall"})  # fmt: skip
    await call("pad", sketch="Sketch_BoxOuter", length="Box_Floor + Support_Height + Plate_Thickness",
               reversed=True, purpose="BoxShell")  # fmt: skip
    await call("create_sketch", body="Box", plane="XY", offset="Plate_Thickness", purpose="BoxCavity")
    await call("add_profile", sketch="Sketch_BoxCavity", kind="rectangle", prefix="BoxInner", params={
        "width": "Plate_Length + 2*Box_Clearance", "height": "Plate_Width + 2*Box_Clearance"})  # fmt: skip
    await call("pocket", sketch="Sketch_BoxCavity", depth="Support_Height + Plate_Thickness",
               purpose="BoxCavity")  # fmt: skip
    await call("create_sketch", body="Box", plane="XY", purpose="Support")
    p = parameters(3)
    x, y = p["Plate_Length"] / 2 + p["Box_Clearance"], p["Plate_Width"] / 2 + p["Box_Clearance"]
    geometry, constraints = [], []
    for index, (sx, sy, start, mirror) in enumerate(SUPPORT_CORNERS):
        geometry += _quarter_disc(sx * x, sy * y, start)
        constraints += _quarter_disc_constraints(index, start, mirror)
    await call("add_geometry", sketch="Sketch_Support", items=geometry)
    await call("add_constraints", sketch="Sketch_Support", items=constraints)
    await call("pad", sketch="Sketch_Support", length="Support_Height", reversed=True, purpose="Support")


async def _build_pins(call: Client) -> None:
    """Stage 4: four pins up from the supports (Box), then the matching holes in the plate (Plate)."""
    await call("set_parameters", parameters=STAGE_PARAMETERS[4])
    pitch = {"width": "Plate_Length - 2*Pin_Edge_Distance", "height": "Plate_Width - 2*Pin_Edge_Distance"}
    await call("create_sketch", body="Box", plane="XY", purpose="Pins")
    await call("add_profile", sketch="Sketch_Pins", kind="hole_rect", prefix="Pins",
               params={**pitch, "diameter": "Pin_Diameter"})  # fmt: skip
    await call("pad", sketch="Sketch_Pins", length="Plate_Thickness", purpose="Pins")
    await call("create_sketch", body="Plate", plane="XY", offset="Plate_Thickness", purpose="PinHoles")
    await call("add_profile", sketch="Sketch_PinHoles", kind="hole_rect", prefix="PinHoles",
               params={**pitch, "diameter": "Pin_Diameter + 2*Box_Clearance"})  # fmt: skip
    await call("hole", sketch="Sketch_PinHoles", size="M5", diameter="Pin_Diameter + 2*Box_Clearance",
               purpose="PinHoles")  # fmt: skip


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
    if stage >= BOX_STAGE:
        box = await _shape(call, "Box")
        volume, target = (box or {}).get("volume", 0.0), expected_box_volume(expected, stage)
        _check(results, stage, "Kasten Volumen", abs(volume - target) <= 1.0,
               f"{volume:.1f} (Soll {target:.1f} ± 1)")  # fmt: skip
        bound = (box or {}).get("bound_box", {"size": [0, 0, 0], "z": [0, 0]})
        _check(results, stage, "Kasten Abmessungen", _close(bound["size"], expected_box_size(expected)),
               f"{bound['size']} (Soll {expected_box_size(expected)})")  # fmt: skip
        _check(results, stage, "Kasten Einbaulage (z)", _close(bound["z"], expected_box_z(expected)),
               f"{bound['z']} (Soll {expected_box_z(expected)})")  # fmt: skip

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
        _check(results, stage, "Kasten Parametrik (Plate_Length 240)", abs(volume - target) <= 1.0,
               f"{volume:.1f} (Soll {target:.1f} ± 1)")  # fmt: skip

    passed = sum(r["ok"] for r in results)
    return {
        "sample": "referenzmodell",
        "stage": stage,
        "score": f"{passed}/{len(results)}",
        "checks": results,
    }


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
