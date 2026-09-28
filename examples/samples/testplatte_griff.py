"""Benchmark sample "Testplatte mit Griff": reference build, deterministic check, screenshot.

Compare LLMs / thinking levels: let each model build the part from the prompt in
``testplatte-griff.md`` (fresh FreeCAD document), then run ``check``. All checks use tool
results only, so the scores are reproducible.

    uv run python examples/samples/testplatte_griff.py build       # reference build (baseline)
    uv run python examples/samples/testplatte_griff.py check       # score the open document
    uv run python examples/samples/testplatte_griff.py screenshot  # refresh testplatte-griff.png

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
SCREENSHOT = HERE / "testplatte-griff.png"
DOCUMENT = "Testplatte"

PARAMETERS: dict[str, float] = {
    "Plate_Length": 200,
    "Plate_Width": 100,
    "Plate_Thickness": 5,
    "Hole_Diameter": 8,
    "Hole_Edge_Distance": 10,
    "Handle_Diameter": 10,
    "Handle_Clearance": 30,
    "Handle_Bend_Radius": 10,
}


def expected_volume(p: Mapping[str, float]) -> float:
    """Plate - 4 holes + swept handle - the two leg pieces inside the plate (Pappus for the sweep)."""
    plate = p["Plate_Length"] * p["Plate_Width"] * p["Plate_Thickness"]
    holes = 4 * math.pi * (p["Hole_Diameter"] / 2) ** 2 * p["Plate_Thickness"]
    section = math.pi * (p["Handle_Diameter"] / 2) ** 2
    legs, radius = p["Plate_Length"] / 2, p["Handle_Bend_Radius"]
    height = p["Plate_Thickness"] + p["Handle_Clearance"] + p["Handle_Diameter"] / 2
    centre_line = 2 * height + legs - 4 * radius + math.pi * radius
    return plate - holes + section * centre_line - 2 * section * p["Plate_Thickness"]


def expected_size(p: Mapping[str, float]) -> list[float]:
    height = p["Plate_Thickness"] + p["Handle_Clearance"] + p["Handle_Diameter"]
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


async def build(call: Client) -> None:
    """Reference solution (19 tool calls) - the baseline the models are compared against."""
    await call("new_document", name=DOCUMENT)
    plate_keys = ("Plate_Length", "Plate_Width", "Plate_Thickness", "Hole_Diameter", "Hole_Edge_Distance")
    await call("set_parameters", parameters={k: PARAMETERS[k] for k in plate_keys})
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
    handle_keys = ("Handle_Diameter", "Handle_Clearance", "Handle_Bend_Radius")
    await call("set_parameters", parameters={k: PARAMETERS[k] for k in handle_keys})
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


def _check(results: list[dict[str, Any]], name: str, ok: bool, detail: str) -> None:
    results.append({"check": name, "ok": bool(ok), "detail": detail})


async def check(call: Client) -> dict[str, Any]:
    """Score the open document against the specification (read-only except one undone probe)."""
    results: list[dict[str, Any]] = []
    tree = await call("get_model_tree", document=DOCUMENT)
    bodies = [o for o in tree["objects"] if o["type"] == "PartDesign::Body"]
    _check(results, "ein Body", len(bodies) == 1, f"{len(bodies)} Bodies")
    features = bodies[0]["features"] if bodies else []
    sketches = [f for f in features if f["type"] == "Sketcher::SketchObject"]
    _check(results, "alle Skizzen DoF 0", bool(sketches) and all(s.get("dof") == 0 for s in sketches),
           ", ".join(f"{s['label']}={s.get('dof')}" for s in sketches))  # fmt: skip
    _check(results, "alle Features gültig", all(f["valid"] for f in features), f"{len(features)} Objekte")
    _check(results, "keine Label-Probleme", not tree["label_issues"], str(tree["label_issues"]))
    types = {f["type"] for f in features}
    _check(results, "Bohrungen als Hole-Feature", "PartDesign::Hole" in types, "PartDesign::Hole")
    _check(results, "Griff als Sweep", "PartDesign::AdditivePipe" in types, "PartDesign::AdditivePipe")

    listed = {p["name"]: p["value"] for p in await call("list_parameters", document=DOCUMENT)}
    missing = [k for k in PARAMETERS if k not in listed]
    wrong = [k for k in PARAMETERS if k in listed and abs(float(listed[k]) - PARAMETERS[k]) > 1e-6]
    _check(
        results,
        "Parameter vollständig und korrekt",
        not missing and not wrong,
        f"fehlend={missing} falsch={wrong}",
    )

    stats = (await call("check_printability", document=DOCUMENT))["stats"]
    volume, target = stats["volume"], expected_volume(PARAMETERS)
    _check(results, "Volumen", abs(volume - target) <= 1.0, f"{volume:.1f} (Soll {target:.1f} ± 1)")
    size, target_size = stats["size"], expected_size(PARAMETERS)
    _check(results, "Abmessungen", all(abs(a - b) <= 0.01 for a, b in zip(size, target_size, strict=True)),
           f"{size} (Soll {target_size})")  # fmt: skip

    # Parametrics: longer plate -> handle follows (expression on Plate_Length); undone afterwards.
    probe = {**PARAMETERS, "Plate_Length": 240}
    await call("set_parameters", parameters={"Plate_Length": 240}, document=DOCUMENT)
    try:
        probe_volume = (await call("check_printability", document=DOCUMENT))["stats"]["volume"]
    finally:
        await call("undo", steps=1, document=DOCUMENT)
    _check(results, "Parametrik (Plate_Length 240)", abs(probe_volume - expected_volume(probe)) <= 1.0,
           f"{probe_volume:.1f} (Soll {expected_volume(probe):.1f} ± 1)")  # fmt: skip

    passed = sum(r["ok"] for r in results)
    return {"sample": "testplatte-griff", "score": f"{passed}/{len(results)}", "checks": results}


async def screenshot(call: Client) -> Path:
    result = await call.session.call_tool("screenshot", {"view": "iso", "width": 1200, "height": 800,
                                                         "document": DOCUMENT})  # fmt: skip
    image = next(block for block in result.content if getattr(block, "type", "") == "image")
    SCREENSHOT.write_bytes(base64.b64decode(image.data))  # type: ignore[attr-defined]
    return SCREENSHOT


async def main(command: str) -> int:
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
            await build(call)
            print(f"Referenz gebaut ({call.calls} Tool-Aufrufe)")
        elif command == "check":
            report = await check(call)
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["score"].split("/")[0] == report["score"].split("/")[1] else 1
        else:
            print(f"Screenshot: {await screenshot(call)}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("command", choices=["build", "check", "screenshot"])
    sys.exit(asyncio.run(main(parser.parse_args().command)))
