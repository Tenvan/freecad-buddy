# addon/FreeCADBuddy/

## Responsibility

FreeCAD addon root (installed under FreeCAD's `Mod/`): GUI bootstrap that registers the "FreeCAD Buddy" workbench and starts the bridge (Plugin Entry Point).

## Design

- `InitGui.py`: executed by FreeCAD at GUI start-up; defines `FreeCADBuddyWorkbench` (toolbar + menu from `buddy_bridge.commands.COMMANDS`) inside `_setup_freecad_buddy()` so nothing leaks into FreeCAD's global namespace.
- Imports only `FreeCADGui`, `PySide` and `buddy_bridge` (addon layer: stdlib + FreeCAD + `PySide` only).
- Sub-packages: [`buddy_bridge/`](buddy_bridge/codemap.md) (socket bridge, Qt main-thread dispatch) and [`buddy_core/`](buddy_core/codemap.md) (modelling logic).

## Flow

1. FreeCAD GUI starts → runs `InitGui.py`.
2. `commands.register()` registers the GUI commands; `FreeCADGui.addWorkbench(...)` adds the workbench.
3. `QtCore.QTimer.singleShot(0, commands.autostart)` starts the bridge once the Qt event loop runs, so the dispatcher lives on the main thread.

## Integration

- Consumed by: FreeCAD GUI addon loader.
- Depends on: `buddy_bridge.commands`; `buddy_bridge` in turn calls into `buddy_core`.
- Headless counterpart (no GUI): `buddy_bridge/headless.py`, started via `tools/run_headless_bridge.py`.
