# Repository Atlas: FreeCAD Buddy

## Project Responsibility

FreeCAD Buddy lets MCP clients (e.g. Claude Code) model 3D-print parts in FreeCAD via PartDesign/Sketcher. It is split into two processes: an MCP server with a German Textual TUI (`src/buddy_server`, project venv, no FreeCAD import) and a FreeCAD addon (`addon/FreeCADBuddy`) whose socket bridge (`buddy_bridge`, stdlib only) runs every call on FreeCAD's Qt main thread against the modelling layer (`buddy_core`). Every mutation is exactly one FreeCAD undo step.

## System Entry Points

- `pyproject.toml`: package `freecad-buddy`, console script `freecad-buddy = buddy_server.cli:main`, poe tasks (`check`, `test-tools`, `test-core`), ruff/pyright config.
- `src/buddy_server/cli.py`: server start (TUI or `--headless`).
- `addon/FreeCADBuddy/InitGui.py`: FreeCAD GUI start-up, registers the workbench and autostarts the bridge.
- `addon/FreeCADBuddy/buddy_bridge/headless.py` / `tools/run_headless_bridge.py`: bridge without GUI (E2E tests).

## Directory Map

| Folder | Responsibility | Map |
|---|---|---|
| `src/` | Server-side container: `buddy_server` package in the project venv. | [codemap](src/codemap.md) |
| `src/buddy_server/` | MCP server process and Textual TUI; exposes tools over authenticated HTTP and forwards every call to the FreeCAD bridge, no FreeCAD import, no modelling logic. | [codemap](src/buddy_server/codemap.md) |
| `src/buddy_server/tools/` | MCP tool layer (adapter/facade): registers the public tools per group module and forwards each to one bridge method. | [codemap](src/buddy_server/tools/codemap.md) |
| `addon/` | FreeCAD-side container: the `FreeCADBuddy` addon running inside the FreeCAD process. | [codemap](addon/codemap.md) |
| `addon/FreeCADBuddy/` | Addon root / plugin entry point: registers the workbench and starts the bridge on the Qt main thread. | [codemap](addon/FreeCADBuddy/codemap.md) |
| `addon/FreeCADBuddy/buddy_bridge/` | Transport and RPC gateway: loopback, token-authenticated JSON-RPC server that routes calls onto the Qt main thread into `buddy_core`. | [codemap](addon/FreeCADBuddy/buddy_bridge/codemap.md) |
| `addon/FreeCADBuddy/buddy_core/` | Domain/service layer: all FreeCAD modelling logic (documents, bodies, PartDesign features, parameters, assemblies, undo/history), no MCP/network, no GUI requirement. | [codemap](addon/FreeCADBuddy/buddy_core/codemap.md) |
| `addon/FreeCADBuddy/buddy_core/sketch/` | Sketcher modelling layer: builds, constrains, analyses and validates sketches incl. external geometry references. | [codemap](addon/FreeCADBuddy/buddy_core/sketch/codemap.md) |
| `addon/FreeCADBuddy/buddy_core/printing/` | Print-preparation service: printer profile persistence, read-only printability checks, verified STL/3MF/STEP export. | [codemap](addon/FreeCADBuddy/buddy_core/printing/codemap.md) |
| `addon/FreeCADBuddy/buddy_core/addons/` | Adapter around FreeCAD's Addon Manager: reports installed addons/macros and runs user-confirmed install jobs. | [codemap](addon/FreeCADBuddy/buddy_core/addons/codemap.md) |
| `tools/` | Developer tooling: runs FreeCAD's Python in a clean environment (core tests, headless bridge), generates tool docs, in-GUI acceptance checks. | [codemap](tools/codemap.md) |

Not mapped (deliberately): `tests/`, `docs/`, `examples/`, `TODOs/`, `out/`.
