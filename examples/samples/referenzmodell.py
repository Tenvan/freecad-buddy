"""Benchmark sample "Referenzmodell": reference build, deterministic check, screenshot.

The model grows in stages (1 = base plate with corner holes, 2 = handle, …). Every stage adds
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
LATEST_STAGE = 2

STAGE_PARAMETERS: dict[int, dict[str, float]] = {
    1: {
        "Plate_Length": 200,
        "Plate_Width": 100,
        "Plate_Thickness": 5,
        "Hole_Diameter": 8,
        "Hole_Edge_Distance": 10,
    },
    2: {"Handle_Diameter": 10, "Handle_Clearance": 30, "Handle_Bend_Radius": 10},
}
PROMPT_HEAD = "Erstelle mit FreeCAD Buddy ein neues Dokument „Referenzmodell“ mit genau einem Body „Plate“:"
STAGE_PROMPTS: dict[int, list[str]] = {
    1: [
        "Grundplatte 200 × 100 × 5 mm, mittig zum Ursprung auf der XY-Ebene, Länge in X.",
        "In den vier Ecken je eine Durchgangsbohrung Ø 8 mm, Mittelpunkt 10 mm von beiden Rändern.",
    ],
    2: [
        "Mittig ein Haltegriff als runde Stange Ø 10 mm mit gerundeten Ecken (Biegeradius 10 mm auf der "
        "Mittellinie). Beinabstand 50 % der Plattenlänge in X-Richtung, lichte Höhe 30 mm über der "
        "Plattenoberseite. Die Beine reichen durch die ganze Platte. Der Beinabstand ist ein Ausdruck von "
        "Plate_Length.",
    ],
}
PROMPT_TAIL = "Zum Schluss Druckbarkeit prüfen und Ansicht iso. Nicht speichern, nicht exportieren."

STAGE_FEATURES: dict[int, tuple[str, ...]] = {
    1: ("PartDesign::Pad", "PartDesign::Hole"),
    2: ("PartDesign::AdditivePipe",),
}


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
    steps.append(PROMPT_TAIL)
    return "\n".join([PROMPT_HEAD, "", *(f"{index}. {step}" for index, step in enumerate(steps, 1))])


def expected_volume(p: Mapping[str, float], stage: int = LATEST_STAGE) -> float:
    """Stage 1: plate - 4 holes. Stage 2: + swept handle (Pappus) - the two leg pieces inside the plate."""
    volume = p["Plate_Length"] * p["Plate_Width"] * p["Plate_Thickness"]
    volume -= 4 * math.pi * (p["Hole_Diameter"] / 2) ** 2 * p["Plate_Thickness"]
    if stage >= 2:
        section = math.pi * (p["Handle_Diameter"] / 2) ** 2
        legs, radius = p["Plate_Length"] / 2, p["Handle_Bend_Radius"]
        height = p["Plate_Thickness"] + p["Handle_Clearance"] + p["Handle_Diameter"] / 2
        centre_line = 2 * height + legs - 4 * radius + math.pi * radius
        volume += section * centre_line - 2 * section * p["Plate_Thickness"]
    return volume


def expected_size(p: Mapping[str, float], stage: int = LATEST_STAGE) -> list[float]:
    height = p["Plate_Thickness"]
    if stage >= 2:
        height += p["Handle_Clearance"] + p["Handle_Diameter"]
    return [p["Plate_Length"], p["Plate_Width"], height]


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
    """Reference solution (stage 2: 17 tool calls) - the baseline the models are compared against."""
    await call("new_document", name=DOCUMENT)
    await call("set_parameters", parameters=STAGE_PARAMETERS[1])
    await call("create_body", label="Plate")
    await call("create_sketch", plane="XY", purpose="Plate")
    await call("add_profile", sketch="Sketch_Plate", kind="rectangle",
               params={"width": "Plate_Length", "height": "Plate_Width"}, prefix="Plate")  # fmt: skip
    await call("pad", sketch="Sketch_Plate", length="Plate_Thickness", purpose="Plate")
    await call("create_sketch", plane="XY", purpose="CornerHoles", offset="Plate_Thickness")
    await call("add_profile", sketch="Sketch_CornerHoles", kind="hole_rect", prefix="Holes", params={
        "width": "Plate_Length - 2*Hole_Edge_Distance", "height": "Plate_Width - 2*Hole_Edge_Distance",
        "diameter": "Hole_Diameter"})  # fmt: skip
    await call(
        "hole", sketch="Sketch_CornerHoles", size="M8", diameter="Hole_Diameter", purpose="CornerHoles"
    )
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
    await call("check_printability")
    await call("set_view", view="iso")


def _check(results: list[dict[str, Any]], stage: int, name: str, ok: bool, detail: str) -> None:
    results.append({"stage": stage, "check": name, "ok": bool(ok), "detail": detail})


async def check(call: Client, stage: int = LATEST_STAGE) -> dict[str, Any]:
    """Score the open document up to ``stage`` (read-only except one undone parameter probe)."""
    results: list[dict[str, Any]] = []
    expected = parameters(stage)
    tree = await call("get_model_tree", document=DOCUMENT)
    bodies = [o for o in tree["objects"] if o["type"] == "PartDesign::Body"]
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

    stats = (await call("check_printability", document=DOCUMENT))["stats"]
    volume, target = stats["volume"], expected_volume(expected, stage)
    _check(results, stage, "Volumen", abs(volume - target) <= 1.0, f"{volume:.1f} (Soll {target:.1f} ± 1)")
    size, target_size = stats["size"], expected_size(expected, stage)
    _check(results, stage, "Abmessungen", all(abs(a - b) <= 0.01 for a, b in zip(size, target_size, strict=True)),
           f"{size} (Soll {target_size})")  # fmt: skip

    # Parametrics: longer plate -> everything follows (expressions on Plate_Length); undone afterwards.
    probe = {**expected, "Plate_Length": 240}
    await call("set_parameters", parameters={"Plate_Length": 240}, document=DOCUMENT)
    try:
        probe_volume = (await call("check_printability", document=DOCUMENT))["stats"]["volume"]
    finally:
        await call("undo", steps=1, document=DOCUMENT)
    target = expected_volume(probe, stage)
    _check(results, stage, "Parametrik (Plate_Length 240)", abs(probe_volume - target) <= 1.0,
           f"{probe_volume:.1f} (Soll {target:.1f} ± 1)")  # fmt: skip

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
