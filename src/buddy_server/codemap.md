# src/buddy_server/

## Responsibility
MCP server process and terminal front end of FreeCAD Buddy: exposes the tool surface to MCP clients over authenticated HTTP and forwards every call to the FreeCAD-side bridge. Runs in the project venv, never imports FreeCAD and holds no modelling logic.

## Design
- Event-bus decoupling: `events.py` (`EventBus` plus typed events such as `ToolStarted`, `ToolFinished`, `BridgeState`, `SessionsChanged`, `Console`); the core only publishes, front ends (`tui.py`, headless `cli.py`) subscribe. `logs.py` routes Python logging into the bus.
- Composition root: `app.py` builds `ToolContext` (bridge, bus, addon catalog, proposals, parts catalog), registers tools and prompts, and wraps the ASGI app in `BearerAuth` and `SessionTracker`.
- Bridge adapter: `bridge.py` (`Bridge`) wraps `buddy_bridge.client.BridgeClient` with lazy connect, reconnect, async `call` and a status watchdog; raises `BridgeUnavailable`/`BridgeTimeout`.
- Middleware: `calllog.py` (`ToolCallLog`, `JsonlLog`) publishes each request/response pair; `payloads.py` (`Masker`, compaction, previews) is the single place that masks secrets and shortens payloads for display.
- Single-source rulebook: `design_rules.py` (`Topic`/`Rule`, filtered by registered tools, character budget) feeds instructions, resources and prompts; `prompts.py` only registers them.
- Tool grouping: `catalog.py` defines `Group` and the `[Category]` description prefix used by modules in `tools/`.
- Server-side services (outside FreeCAD, async, cached under the Buddy home): `addon_catalog.py` (parse/search official addon catalog), `addon_service.py` (`AddonCatalogService`, fetch/verify/cache), `parts_catalog.py` (`PartsCatalog`, step.parts STEP models), `proposals.py` (`ProposalStore`, JSON of proposed design tools), `slicer.py` (OrcaSlicer CLI, print time and filament).
- Lifecycle: `runner.py` (`ServerRunner`, uvicorn plus watchdog in one asyncio loop, `PortInUse`); `config.py` (`Settings`, env flags, default ports 8765 MCP / 9876 bridge).
- TUI (German): `tui.py` (`BuddyApp`, Textual), `chat.py` (`ToolChat`, `CallItem`, `DetailScreen`, batched rendering, capped history), `splitter.py` (`Splitter` widget).
- Subpackage `tools/`: the MCP tool modules (mapped separately).

## Flow
1. `freecad-buddy` starts `cli.main`: `parse_args` -> `settings_from` -> `Settings`; `--print-claude-command` prints the client setup and exits.
2. `--headless`: `run_headless` runs `ServerRunner` directly and prints bus events via `format_event`. Otherwise `route_logging_to_bus`, then `BuddyApp(settings, ServerRunner(...)).run()`.
3. `ServerRunner` checks the port (`ensure_port_free`), calls `app.build_app` and serves it with uvicorn; the `Bridge.watchdog` task runs in the same loop and publishes `BridgeState`.
4. `build_mcp` collects tool names, builds instructions via `design_rules.build_instructions`, creates the MCP server with the `ToolCallLog` middleware, then registers tools and prompts.
5. A client request passes `BearerAuth` (token check) and `SessionTracker` into the MCP streamable HTTP app; the tool handler in `tools/` calls `Bridge.call`, which lazily connects and sends the RPC over the socket to `buddy_bridge`.
6. The result returns through the tool handler to the client; `ToolCallLog` emits `ToolStarted`/`ToolFinished` with masked, compacted payloads.
7. TUI: `BuddyApp` receives bus events as `BusEvent` messages, updates bridge status, sessions and console log, and `ToolChat` renders one request/response entry per call; `DetailScreen` shows the full payload.

## Integration
- Entry point: `freecad-buddy = "buddy_server.cli:main"` (`[project.scripts]` in `pyproject.toml`).
- Depends on: `buddy_bridge.client`, `buddy_bridge.protocol`, `buddy_bridge.tokens` (socket protocol, token file); third-party `mcp`, `uvicorn`, `httpx2`, Textual.
- Consumed by: `tools/` (imports `ToolContext`-related services, `catalog`, `payloads`, `slicer`, catalogs, `design_rules`); tests in `tests/server`, `tests/tools`.
- Talks to the FreeCAD process only via `Bridge`; the FreeCAD addon (`addon/FreeCADBuddy/buddy_bridge`, `buddy_core`) executes the actual modelling.
