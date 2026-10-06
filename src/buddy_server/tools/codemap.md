# src/buddy_server/tools/

## Responsibility

MCP tool layer (adapter/facade): declares the public tools the agent sees and forwards each one to a single bridge method, without FreeCAD imports or modelling logic.

## Design

- Registration pattern: every group module exposes `GROUP` (a `buddy_server.catalog.Group`) and `register(reg: Registration)`, which defines tools as decorated `async` closures (`@tool`) over `reg.ctx`. Docstrings are the agent-facing descriptions; `__init__.register_tools` prefixes them via `catalog.describe(group, doc)` (`[<Category>]`). Tool group = registering module.
- `__init__.py`: `MODULES` (working-phase order), `register_tools(mcp, ctx, allow_python, allow_addon_install)` returning tool names, and `tool_groups()` (dry run with a collecting registrar, no MCP server or bridge needed; used by docs and tests).
- `base.py`: shared `Doc`/`Num`/`Purpose` argument types, `SELECTOR_HELP`, `ToolRegistrar` protocol, `NameCollector`, frozen `Registration` dataclass, and `ToolContext`. `ToolContext.call(tool, method, timeout, **params)` drops `None` params, calls `Bridge.call`, and maps `BridgeUnavailable`/`BridgeTimeout`/`RpcError` to `ToolError` (`[bridge_unavailable]`, `[timeout]`, `[name] message` + hints). It also holds optional services (`addons`, `proposals`, `parts`, event `bus`) and helpers `installed()`, `catalog()`, `parts_catalog()`, `printer_profile()`.
- `session.py`: status, document lifecycle, undo, storepoints/replay.
- `model.py`: bodies, model tree, objects, central parameters.
- `sketch.py`: constrained sketches, profiles, low-level geometry, constraints.
- `reference.py`: datum planes, shape binders, selectors (stable references).
- `feature.py`: PartDesign features (additive, subtractive, dress-up, patterns); largest module.
- `design.py`: recurring multi-step tasks as one call, plus proposals for missing tools (`ProposalStore`, `DesignToolProposed` event).
- `assembly.py`: Assembly4-style assemblies, fasteners, STEP parts, configurations, parts catalogue lookups.
- `appearance.py`: material, colour, live view, screenshots.
- `printing.py`: printer profile, printability check, export.
- `rules.py`: design rulebook and FreeCAD addon catalogue; install tools only if `allow_addon_install`.
- `expert.py`: opt-in Python escape hatch, registered only if `allow_python`.

## Flow

1. Startup: `app.py` builds a `ToolContext` and calls `register_tools` once with `NameCollector` (to learn available tool names) and once with the MCP server.
2. For each module in `MODULES`, `register` runs; each `@tool` wrapper records the function name, prepends the group category to the docstring, and registers it with MCP.
3. A tool call arrives with typed, validated (pydantic `Annotated`/`Field`) arguments.
4. The tool body calls `ctx.call(<tool>, "<namespace.method>", **params)` (some tools aggregate several calls or use `ctx.parts`/`ctx.proposals`/`ctx.addons`).
5. `ToolContext` forwards to `Bridge.call`; the addon-side `buddy_bridge` executes it in the FreeCAD main thread.
6. The result dict is returned to the MCP client, or a bridge failure is raised as a `ToolError` with code and hints.

## Integration

- Consumed by: `buddy_server.app` (`register_tools`, `ToolContext`, `NameCollector`), `buddy_server.prompts` (`ToolContext`), `tools/gen_tool_docs.py` (`tool_groups`), tests incl. `tests/tools/test_tool_contract.py`.
- Depends on: `buddy_server.catalog` (`Group`, `describe`), `buddy_server.bridge` (`Bridge`, errors), `buddy_server.events` (`EventBus`), `buddy_server.addon_service`, `buddy_server.parts_catalog`, `buddy_server.proposals`, `buddy_bridge.protocol` (`RpcError`), `mcp`, `pydantic`.
