# addon/

## Responsibility

Container for the FreeCAD-side half of the system: the `FreeCADBuddy` addon that runs inside the FreeCAD process.

## Design

- [`FreeCADBuddy/`](FreeCADBuddy/codemap.md): addon root, linked or copied into FreeCAD's `Mod/` folder.
- Hard layer rule: code here uses only the stdlib, FreeCAD modules and `PySide` (enforced by `tests/tools/test_addon_imports.py`).

## Flow

FreeCAD loads `FreeCADBuddy/InitGui.py` (GUI) or the headless bridge is started from `tools/run_headless_bridge.py`; both expose `buddy_core` via `buddy_bridge` to the MCP server in `src/buddy_server`.

## Integration

- Consumed by: FreeCAD (GUI/headless), `src/buddy_server` over the bridge socket.
- `buddy_bridge` is also shipped in the server wheel (`pyproject.toml`, `[tool.hatch.build.targets.wheel]`) for its stdlib-only client/protocol modules.
