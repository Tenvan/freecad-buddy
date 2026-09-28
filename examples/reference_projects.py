"""Reference projects built purely through FreeCAD Buddy's MCP tools.

Each project takes ``call(tool, **arguments)`` (an MCP tool caller) and returns a summary.
They double as E2E tests (headless) and as a demo against the live GUI:

    uv run python examples/reference_projects.py box --out ./out
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

Call = Callable[..., Awaitable[Any]]


async def box_with_lid(call: Call, out: Path) -> dict[str, Any]:
    """Storage box with a push-fit lid; the lid lip uses the printer's fit clearance."""
    profile = await call("get_printer_profile")
    await call("document", action="new", name="Box mit Deckel")
    await call(
        "set_parameters",
        parameters={
            "Box_Length": 80,
            "Box_Width": 50,
            "Box_Height": 30,
            "Wall": 2,
            "Corner_Radius": 5,
            "Lid_Plate": 2,
            "Lip_Height": 5,
            "Lip_Wall": 1.6,
            "Fit_Clearance": profile["clearance_fit"],
        },
    )

    await call("create_body", label="Box")
    await call("create_sketch", plane="XY", purpose="BoxOutline", body="Box")
    await call(
        "add_profile",
        sketch="Sketch_BoxOutline",
        kind="rounded_rectangle",
        params={"width": "Box_Length", "height": "Box_Width", "radius": "Corner_Radius"},
        prefix="Box",
    )
    await call("pad", sketch="Sketch_BoxOutline", length="Box_Height", purpose="Box")
    await call("shell", selector="face:top", thickness="Wall", body="Box", purpose="Box")
    await call("chamfer", selector="edges:bottom", size=0.4, body="Box", purpose="ElephantFoot")

    await call("create_body", label="Lid")
    await call("create_sketch", plane="XY", purpose="LidPlate", body="Lid")
    await call(
        "add_profile",
        sketch="Sketch_LidPlate",
        kind="rounded_rectangle",
        params={"width": "Box_Length", "height": "Box_Width", "radius": "Corner_Radius"},
        prefix="Lid",
    )
    await call("pad", sketch="Sketch_LidPlate", length="Lid_Plate", purpose="LidPlate")
    await call("create_sketch", plane="XY", purpose="Lip", offset="Lid_Plate", body="Lid")
    await call(
        "add_profile",
        sketch="Sketch_Lip",
        kind="rounded_rectangle",
        params={
            "width": "Box_Length - 2*Wall - 2*Fit_Clearance",
            "height": "Box_Width - 2*Wall - 2*Fit_Clearance",
            "radius": "Corner_Radius - Wall",
        },
        prefix="Lip",
    )
    await call("pad", sketch="Sketch_Lip", length="Lip_Height", purpose="Lip")
    await call("create_sketch", plane="XY", purpose="LipInner", offset="Lid_Plate + Lip_Height", body="Lid")
    await call(
        "add_profile",
        sketch="Sketch_LipInner",
        kind="rounded_rectangle",
        params={
            "width": "Box_Length - 2*Wall - 2*Fit_Clearance - 2*Lip_Wall",
            "height": "Box_Width - 2*Wall - 2*Fit_Clearance - 2*Lip_Wall",
            "radius": "Corner_Radius - Wall - Lip_Wall",
        },
        prefix="LipInner",
    )
    await call("pocket", sketch="Sketch_LipInner", depth="Lip_Height", purpose="LipInner")

    checks = {body: await call("check_printability", target=body) for body in ("Box", "Lid")}
    exports = {
        body: await call(
            "export_body",
            format="3mf",
            overwrite=True,
            target=body,
            path=str(out / f"BoxMitDeckel_{body}.3mf"),
        )
        for body in ("Box", "Lid")
    }
    return {"checks": checks, "exports": exports, "tree": await call("get_model_tree")}


async def wall_bracket(call: Call, out: Path) -> dict[str, Any]:
    """L-shaped wall bracket with countersunk screw holes and a filleted inner corner."""
    await call("document", action="new", name="Wandhalter")
    await call(
        "set_parameters",
        parameters={
            "Arm_Length": 40,
            "Plate_Height": 50,
            "Thickness": 5,
            "Bracket_Width": 30,
            "Hole_Spacing": 16,
            "Hole_Height": 35,
            "Inner_Radius": 3,
        },
    )
    await call("create_body", label="Bracket")
    await call("create_sketch", plane="YZ", purpose="Profile")
    await call(
        "add_profile",
        sketch="Sketch_Profile",
        kind="polyline",
        params={"points": [[0, 0], [40, 0], [40, 5], [5, 5], [5, 50], [0, 50]]},
    )
    analysis = await call(
        "add_constraints",
        sketch="Sketch_Profile",
        items=[
            {"type": "distance", "a": "g0", "value": "Arm_Length", "name": "Arm_Length"},
            {"type": "distance", "a": "g1", "value": "Thickness", "name": "Arm_Thickness"},
            {"type": "distance", "a": "g4", "value": "Thickness", "name": "Plate_Thickness"},
            {"type": "distance", "a": "g5", "value": "Plate_Height", "name": "Plate_Height"},
        ],
    )
    assert analysis["sketch"]["dof"] == 0, analysis["sketch"]
    await call("pad", sketch="Sketch_Profile", length="Bracket_Width", mode="symmetric", purpose="Bracket")
    await call(
        "fillet",
        selector="edges:parallel=X,y=Thickness,z=Thickness",
        radius="Inner_Radius",
        purpose="InnerCorner",
    )
    await call("create_sketch", plane="XZ", purpose="ScrewHoles")
    for side, x in (("Left", "-Hole_Spacing / 2"), ("Right", "Hole_Spacing / 2")):
        await call(
            "add_profile",
            sketch="Sketch_ScrewHoles",
            kind="circle",
            params={"diameter": 4, "center": [x, "Hole_Height"]},
            prefix=side,
        )
    await call(
        "hole", sketch="Sketch_ScrewHoles", size="M4", cut="countersink", diameter=4.4, purpose="Screws"
    )
    await call("chamfer", selector="edges:bottom", size=0.4, purpose="ElephantFoot")
    check = await call("check_printability")
    exported = await call("export_body", format="3mf", overwrite=True, path=str(out / "Wandhalter.3mf"))
    return {"check": check, "export": exported, "tree": await call("get_model_tree")}


async def knob(call: Call, out: Path) -> dict[str, Any]:
    """Turning knob: revolved body, filleted top, polar grip notches, shaft bore."""
    await call("document", action="new", name="Drehknopf")
    await call(
        "set_parameters",
        parameters={
            "Knob_Radius": 15,
            "Knob_Height": 18,
            "Top_Fillet": 2,
            "Grip_Diameter": 4,
            "Grip_Count": {"value": 12, "type": "integer"},
            "Shaft_Diameter": 6.2,
            "Shaft_Depth": 12,
        },
    )
    await call("create_body", label="Knob")
    await call("create_sketch", plane="XZ", purpose="Profile")
    await call(
        "add_profile",
        sketch="Sketch_Profile",
        kind="rectangle",
        params={"width": "Knob_Radius", "height": "Knob_Height", "anchor": "corner"},
    )
    await call("revolve", sketch="Sketch_Profile", axis="V_Axis", purpose="Body")
    await call("fillet", selector="edges:top", radius="Top_Fillet", purpose="Top")
    await call("create_sketch", plane="XY", purpose="Grip")
    await call(
        "add_profile",
        sketch="Sketch_Grip",
        kind="circle",
        params={"diameter": "Grip_Diameter", "center": ["Knob_Radius", 0]},
    )
    await call("pocket", sketch="Sketch_Grip", mode="through_all", purpose="Grip")
    await call(
        "pattern", features=["Pocket_Grip"], kind="polar", axis="Z", count="Grip_Count", purpose="Grip"
    )
    await call("create_sketch", plane="XY", purpose="Shaft")
    await call("add_profile", sketch="Sketch_Shaft", kind="circle", params={"diameter": "Shaft_Diameter"})
    await call("pocket", sketch="Sketch_Shaft", depth="Shaft_Depth", purpose="Shaft")
    check = await call("check_printability")
    exported = await call("export_body", format="3mf", overwrite=True, path=str(out / "Drehknopf.3mf"))
    return {"check": check, "export": exported, "tree": await call("get_model_tree")}


PROJECTS: dict[str, Callable[[Call, Path], Awaitable[dict[str, Any]]]] = {
    "box": box_with_lid,
    "bracket": wall_bracket,
    "knob": knob,
}


async def _run_against_server(names: list[str], url: str, token: str, out: Path) -> None:
    import httpx2
    from mcp import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with (
        httpx2.AsyncClient(
            headers={"Authorization": f"Bearer {token}"}, timeout=httpx2.Timeout(30, read=300)
        ) as http,
        streamable_http_client(url, http_client=http) as streams,
        ClientSession(streams[0], streams[1]) as session,
    ):
        await session.initialize()

        async def call(tool: str, /, **arguments: Any) -> Any:
            result = await session.call_tool(tool, arguments)
            text = "\n".join(getattr(block, "text", "") for block in result.content)
            if result.is_error:
                raise RuntimeError(f"{tool}: {text}")
            content = result.structured_content
            if content is not None:
                return content.get("result", content) if set(content) == {"result"} else content
            return json.loads(text) if text else None

        for name in names:
            summary = await PROJECTS[name](call, out)
            checks: dict[str, Any] = summary.get("checks") or {name: summary["check"]}
            verdicts = ", ".join(
                f"{body}: {'ok' if check['ok'] else 'Befunde'}" for body, check in checks.items()
            )
            print(f"{name}: fertig – Druckprüfung {verdicts}")


def main() -> None:
    from buddy_server.config import Settings

    parser = argparse.ArgumentParser(
        description="Referenzprojekte gegen einen laufenden freecad-buddy ausführen"
    )
    parser.add_argument("projects", nargs="*", help=f"Auswahl aus {', '.join(PROJECTS)} (Standard: alle)")
    parser.add_argument("--out", type=Path, default=Path("out"))
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    unknown = [name for name in args.projects if name not in PROJECTS]
    if unknown:
        parser.error(f"unbekannte Projekte: {', '.join(unknown)}")
    settings = Settings(port=args.port)
    args.out.mkdir(parents=True, exist_ok=True)
    asyncio.run(
        _run_against_server(args.projects or list(PROJECTS), settings.url, settings.mcp_token(), args.out)
    )


if __name__ == "__main__":
    main()
