"""Generate the tool catalogue from the registered MCP tools, grouped by working phase.

``docs/tools.md`` is the index (groups with one-line purpose); ``docs/tools/<group>.md`` holds the
parameters and an example of every tool of that group.

uv run python tools/gen_tool_docs.py          # write the catalogue
uv run python tools/gen_tool_docs.py --check  # fail if a file is outdated
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
GROUP_DIR = REPO_ROOT / "docs" / "tools"

EXAMPLES: dict[str, dict[str, Any]] = {
    "get_status": {},
    "document": {"action": "new", "name": "Box mit Deckel"},
    "get_model_tree": {},
    "get_object": {"ref": "Sketch_Base"},
    "delete_object": {"ref": "Fillet_Top"},
    "undo": {"steps": 1},
    "storepoint": {"name": "Base body"},
    "list_storepoints": {},
    "replay": {"storepoint": "Base body", "into": "Box_Variant"},
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
    "fill_pattern": {
        "size": 5,
        "pitch": 6,
        "cell": "hex",
        "field": [100, 80],
        "margin": 3,
        "offset": "Plate_Thickness",
        "name": "Honey",
    },
    "propose_design_tool": {
        "name": "screw_boss",
        "problem": "Screw bosses with a pilot hole recur in every housing",
        "inputs": ["outer_diameter", "height", "screw_size"],
        "steps": [
            "create_sketch",
            "add_profile circle",
            "pad",
            "create_sketch",
            "add_profile circle",
            "pocket",
        ],
        "example": "screw_boss(center=[10, 10], outer_diameter=7, height=12, screw_size='M3')",
    },
    "list_design_tool_proposals": {},
    "datum_plane": {"base": "XY", "offset": "Box_Height", "purpose": "Top"},
    "shape_binder": {"sources": ["Box:Sketch_Base"], "body": "Lid", "purpose": "BoxOutline"},
    "thread": {"center": [85, 35], "diameter": "Pin_Diameter", "pitch": 1.5, "length": 15, "z_start": 5},
    "add_gear": {
        "kind": "involute",
        "teeth": "Gear_Teeth",
        "module": 1.5,
        "height": 8,
        "properties": {"backlash": 0.1},
        "purpose": "Drive",
    },
    "set_material": {"target": "Lid", "material": "ABS", "color": "red"},
    "create_assembly": {},
    "add_to_assembly": {"part": "Box"},
    "add_fastener": {"type": "ISO4032", "diameter": "M10", "positions": [[85, 35, 7]]},
    "search_parts": {"query": "raspberry pi 5", "category": "electronics"},
    "insert_part": {"part_id": "raspberry_pi_5", "position": [0, 0, 3], "purpose": "Pi"},
    "explode_assembly": {"moves": {"Lid": [0, 0, 60]}},
    "apply_configuration": {"name": "Assembled"},
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
    "install_addon": {"addon_id": "lattice2"},
    "sweep": {"profile": "Sketch_HandleSection", "path": "Sketch_HandlePath", "purpose": "Handle"},
    "loft": {"sketches": ["Sketch_FunnelBottom", "Sketch_FunnelTop"], "purpose": "Funnel"},
    "helix": {
        "sketch": "Sketch_SpringWire",
        "pitch": "Spring_Pitch",
        "height": "Spring_Height",
        "purpose": "Spring",
    },
    "primitive": {
        "kind": "sphere",
        "dims": {"diameter": "Knob_Diameter"},
        "offset": "Knob_Height",
        "purpose": "Knob",
    },
    "datum": {"kind": "line", "base": "XY", "offset": ["Hinge_X", 0, 0], "purpose": "HingeAxis"},
    "draft": {"selector": "faces:vertical", "angle": "Draft_Angle", "purpose": "Walls"},
    "boolean": {"op": "fuse", "bodies": ["Rib_Insert"], "body": "Shell_Top", "purpose": "Ribs"},
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


async def _catalog() -> tuple[list[Any], list[tuple[Any, list[str]]]]:
    """Registered MCP tools (all options on) and their groups in working-phase order."""
    sys.path[:0] = [str(REPO_ROOT / "src"), str(REPO_ROOT / "addon" / "FreeCADBuddy")]
    from buddy_server.app import build_mcp
    from buddy_server.bridge import Bridge
    from buddy_server.config import Settings
    from buddy_server.events import EventBus
    from buddy_server.tools import tool_groups

    settings = Settings(home=Path(tempfile.gettempdir()), allow_python=True, allow_addon_install=True)
    bus = EventBus()
    mcp, _ = build_mcp(settings, Bridge(settings, bus), bus)
    return await mcp.list_tools(), tool_groups()


async def _tools() -> list[Any]:
    return (await _catalog())[0]


def _summary(tool: Any) -> str:
    """First description line without the ``[Category]`` prefix."""
    line = (tool.description or "").strip().splitlines()[0]
    return line.split("] ", 1)[1] if line.startswith("[") and "] " in line else line


def _details(tool: Any) -> list[str]:
    lines = ["", f"## {tool.name}", "", (tool.description or "").strip(), ""]
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
    return [*lines, "", "Beispiel:", "", "```json", example, "```"]


def render(tools: list[Any], groups: list[tuple[Any, list[str]]]) -> dict[Path, str]:
    """``docs/tools.md`` (index) and one ``docs/tools/<group>.md`` per non-empty group."""
    by_name = {tool.name: tool for tool in tools}
    grouped = [(group, [by_name[name] for name in names]) for group, names in groups if names]
    missing = set(by_name) - {tool.name for _, members in grouped for tool in members}
    if missing:
        raise SystemExit(f"Tools ohne Gruppe: {sorted(missing)}")
    index = [
        "# Tool-Katalog — FreeCAD Buddy",
        "",
        "> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten.",
        "",
        f"{len(tools)} Tools in {len(grouped)} Gruppen nach Arbeitsphase (`execute_python` nur mit "
        "`FREECAD_BUDDY_ALLOW_PYTHON=1` bzw. `--allow-python`). Jede Tool-Beschreibung beginnt mit ihrer "
        "Kategorie, z. B. `[Sketch]`. Maße akzeptieren eine Zahl, einen Parameternamen oder einen Ausdruck "
        'über Parameter (`"Box_Width - 2*Wall"`).',
        "",
        "| Gruppe | Kategorie | Tools |",
        "|---|---|---|",
    ]
    index += [
        f"| [{group.title}](tools/{group.key}.md) | `[{group.prefix}]` | {len(members)} |"
        for group, members in grouped
    ]
    files: dict[Path, str] = {}
    for group, members in grouped:
        index += ["", f"## {group.title}", "", "| Tool | Zweck |", "|---|---|"]
        index += [f"| [`{t.name}`](tools/{group.key}.md#{t.name}) | {_summary(t)} |" for t in members]
        page = [
            f"# {group.title} — Tool-Katalog",
            "",
            "> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. "
            "Übersicht: [Tool-Katalog](../tools.md).",
            "",
            f"Kategorie-Präfix: `[{group.prefix}]` · {len(members)} Tools",
            "",
            "| Tool | Zweck |",
            "|---|---|",
        ]
        page += [f"| [`{t.name}`](#{t.name}) | {_summary(t)} |" for t in members]
        for tool in members:
            page += _details(tool)
        files[GROUP_DIR / f"{group.key}.md"] = "\n".join(page) + "\n"
    return {TARGET: "\n".join(index) + "\n", **files}


def stale_files(files: dict[Path, str]) -> list[Path]:
    """Generated group pages that no longer belong to a group."""
    return sorted(path for path in GROUP_DIR.glob("*.md") if path not in files) if GROUP_DIR.exists() else []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = render(*asyncio.run(_catalog()))
    if args.check:
        outdated = [p for p, c in files.items() if not p.exists() or p.read_text(encoding="utf-8") != c]
        outdated += stale_files(files)
        if outdated:
            names = ", ".join(str(p.relative_to(REPO_ROOT)) for p in outdated)
            print(f"Tool-Katalog veraltet ({names}) – uv run python tools/gen_tool_docs.py", file=sys.stderr)
            return 1
        return 0
    GROUP_DIR.mkdir(parents=True, exist_ok=True)
    for path in stale_files(files):
        path.unlink()
    for path, content in files.items():
        path.write_text(content, encoding="utf-8")
    tools = sum(content.count("\n## ") for path, content in files.items() if path != TARGET)
    print(f"{TARGET} + {len(files) - 1} Gruppenseiten geschrieben ({tools} Tools)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
