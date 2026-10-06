# src/

## Responsibility

Container for the server-side half of the system: the `buddy_server` package (MCP server + TUI) running in the project venv.

## Design

- [`buddy_server/`](buddy_server/codemap.md): MCP server, TUI, bridge client wiring.
- [`buddy_server/tools/`](buddy_server/tools/codemap.md): public MCP tool groups.
- Hard layer rule: no FreeCAD import and no modelling logic here; modelling lives in `addon/FreeCADBuddy/buddy_core`.

## Flow

`freecad-buddy` console script (`buddy_server.cli:main`) → MCP server/TUI → tool call → bridge socket → FreeCAD process.

## Integration

- Consumed by: MCP clients (Claude Code etc.), the user via the TUI.
- Depends on: `mcp`, `textual`, `uvicorn` (`pyproject.toml`), and `buddy_bridge` client/protocol modules.
