"""Generate ``docs/tools.md`` (tool catalogue) from the registered MCP tools.

uv run python tools/gen_tool_docs.py          # write docs/tools.md
uv run python tools/gen_tool_docs.py --check  # fail if the file is outdated
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET = REPO_ROOT / "docs" / "tools.md"

EXAMPLES: dict[str, dict[str, Any]] = {
    "get_status": {},
    "new_document": {"name": "Box mit Deckel"},
    "open_document": {"path": "C:/Projekte/box.FCStd"},
    "save_document": {"path": "C:/Projekte/box.FCStd"},
    "get_model_tree": {},
    "get_object": {"ref": "Sketch_Base"},
    "delete_object": {"ref": "Fillet_Top"},
    "undo": {"steps": 1},
    "set_parameters": {"parameters": {"Box_Width": 60, "Grip_Count": {"value": 12, "type": "integer"}}},
    "list_parameters": {},
    "create_body": {"label": "Box"},
    "create_sketch": {"plane": "XY", "purpose": "Base", "offset": "Lid_Plate"},
    "add_profile": {
        "sketch": "Sketch_Base",
        "kind": "rounded_rectangle",
        "params": {"width": "Box_Width", "height": "Box_Depth", "radius": 5},
    },
    "add_geometry": {"sketch": "Sketch_Base", "items": [{"type": "line", "start": [0, 0], "end": [20, 0]}]},
    "add_constraints": {
        "sketch": "Sketch_Base",
        "items": [
            {"type": "coincident", "a": "g0.start", "b": "origin"},
            {"type": "distance", "a": "g0", "value": "Arm_Length", "name": "Arm_Length"},
        ],
    },
    "analyze_sketch": {"sketch": "Sketch_Base"},
    "fully_constrain_sketch": {"sketch": "Sketch_Base", "apply": False},
    "pad": {"sketch": "Sketch_Base", "length": "Box_Height", "purpose": "Base"},
    "pocket": {"sketch": "Sketch_Cutout", "mode": "through_all", "purpose": "Cutout"},
    "revolve": {"sketch": "Sketch_Profile", "axis": "V_Axis", "angle": 360},
    "hole": {"sketch": "Sketch_ScrewHoles", "size": "M4", "cut": "countersink", "diameter": 4.4},
    "fillet": {"selector": "edges:vertical", "radius": "Corner_Radius"},
    "chamfer": {"selector": "edges:bottom", "size": 0.4},
    "shell": {"selector": "face:top", "thickness": "Wall"},
    "pattern": {
        "features": ["Pocket_SieveHole"],
        "kind": "grid",
        "length": "(Sieve_Count_X - 1) * Sieve_Pitch",
        "count": "Sieve_Count_X",
        "length2": "(Sieve_Count_Y - 1) * Sieve_Pitch",
        "count2": "Sieve_Count_Y",
    },
    "datum_plane": {"base": "XY", "offset": "Box_Height", "purpose": "Top"},
    "select_geometry": {"selector": "edges:parallel=X,y=Thickness,z=Thickness"},
    "screenshot": {"view": "iso", "width": 800, "height": 600},
    "get_printer_profile": {},
    "set_printer_profile": {"updates": {"nozzle": 0.6, "min_wall": 1.2}},
    "check_printability": {"target": "Box"},
    "export_body": {"format": "3mf", "target": "Box"},
    "get_design_rules": {"topic": "printing"},
    "set_view": {"view": "iso", "fit": True},
    "search_addons": {"query": "grid", "kind": "any"},
    "get_addon": {"addon_id": "lattice2"},
    "sweep": {"profile": "Sketch_HandleSection", "path": "Sketch_HandlePath", "purpose": "Handle"},
    "execute_python": {"code": "result = len(doc.Objects)"},
}


def _type(schema: dict[str, Any]) -> str:
    if "anyOf" in schema:
        return " | ".join(_type(option) for option in schema["anyOf"])
    if "enum" in schema:
        return " | ".join(f"`{value}`" for value in schema["enum"])
    kind = schema.get("type", "any")
    if kind == "array":
        return f"array<{_type(schema.get('items', {}))}>"
    return str(kind)


async def _tools() -> list[Any]:
    sys.path[:0] = [str(REPO_ROOT / "src"), str(REPO_ROOT / "addon" / "FreeCADBuddy")]
    from buddy_server.app import build_mcp
    from buddy_server.bridge import Bridge
    from buddy_server.config import Settings
    from buddy_server.events import EventBus

    settings = Settings(home=Path(tempfile.gettempdir()), allow_python=True)
    bus = EventBus()
    mcp, _ = build_mcp(settings, Bridge(settings, bus), bus)
    return await mcp.list_tools()


def render(tools: list[Any]) -> str:
    lines = [
        "# Tool-Katalog — FreeCAD Buddy",
        "",
        "> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten.",
        "",
        f"{len(tools)} Tools (`execute_python` nur mit `FREECAD_BUDDY_ALLOW_PYTHON=1` bzw. `--allow-python`).",
        "Maße akzeptieren eine Zahl, einen Parameternamen oder einen Ausdruck über Parameter "
        '(`"Box_Width - 2*Wall"`).',
        "",
        "| Tool | Zweck |",
        "|---|---|",
    ]
    for tool in tools:
        summary = (tool.description or "").strip().splitlines()[0]
        lines.append(f"| [`{tool.name}`](#{tool.name.replace('_', '_')}) | {summary} |")
    for tool in tools:
        lines += ["", f"## {tool.name}", "", (tool.description or "").strip(), ""]
        properties = tool.input_schema.get("properties", {})
        required = set(tool.input_schema.get("required", []))
        if properties:
            lines += ["| Parameter | Typ | Pflicht | Standard | Beschreibung |", "|---|---|---|---|---|"]
            for name, schema in properties.items():
                default = json.dumps(schema["default"], ensure_ascii=False) if "default" in schema else "—"
                description = (schema.get("description") or "").replace("|", "\\|")
                lines.append(
                    f"| `{name}` | {_type(schema).replace('|', '\\|')} | {'ja' if name in required else 'nein'} "
                    f"| `{default}` | {description} |"
                )
        else:
            lines.append("Keine Parameter.")
        example = json.dumps(EXAMPLES[tool.name], ensure_ascii=False, indent=2)
        lines += ["", "Beispiel:", "", "```json", example, "```"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    content = render(asyncio.run(_tools()))
    if args.check:
        current = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if current != content:
            print(
                "docs/tools.md ist veraltet – uv run python tools/gen_tool_docs.py ausführen", file=sys.stderr
            )
            return 1
        return 0
    TARGET.write_text(content, encoding="utf-8")
    print(f"{TARGET} geschrieben ({content.count('## ')} Tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
