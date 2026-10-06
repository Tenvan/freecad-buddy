# addon/FreeCADBuddy/buddy_core/

## Responsibility

Domain/Service Layer: all FreeCAD modelling logic (documents, bodies, PartDesign features, parameters, assemblies, undo/history), running in FreeCAD's Python with no MCP/network dependency and no GUI requirement.

## Design

- Plain functions per domain returning `result.ToolResult` (created/modified/warnings/hints/data); `errors.CoreError` (named, mapped to JSON-RPC codes by the bridge, FreeCAD-free) for failures.
- `transaction.py`: `transaction(doc, label)` context manager = one undo step; refuses while the user edits (`busy_user_transaction`), recomputes, rolls back on error or newly invalid objects (`recompute_failed` with `diagnostics.hints`); nested calls join the outer one; counts commits in `commits`.
- `compat.py`: `REQUIRED_TYPES` and `missing_types()` detect FreeCAD API drift; missing features surface as `errors.UNSUPPORTED`.
- `documents.py`: resolve document/object refs, new/open/save/close/revert, `model_tree`, `get_object`, `delete_object`, `undo`.
- `body.py`, `binder.py`: PartDesign bodies/origin features and shape binders across bodies.
- `features.py`: PartDesign features (pad, pocket, revolve, sweep, loft, helix, primitive, hole, fillet/chamfer/shell/draft, pattern, datum, boolean); flips subtractive features that remove no material.
- `values.py`: dimension values as number, parameter name or expression, bound as FreeCAD expressions; `parameters.py`: central `Parameters` VarSet.
- `select.py`: semantic face/edge selectors (`face:...`, `edge:...`) instead of fragile names; `naming.py`: `<Type>_<Purpose>` labels and lint.
- `design_tools.py`: multi-step tasks composed from existing features in one transaction; `thread.py`, `gears.py`, `assembly.py` (Assembly4 convention, fasteners, STEP parts, exploded views): domain features built on the same primitives.
- `stream.py`: design stream and storepoints stored in the document, reconciled with undo/redo; `appearance.py`, `display.py`, `view.py`: material/colour, edge/vertex display style, view and screenshots (GUI only).
- Subpackages (mapped separately): `addons/` (workbench add-on status/install), `printing/` (3D-print checks and export), `sketch/` (Sketcher model and geometry).

## Flow

1. The bridge dispatches a JSON-RPC method (`buddy_bridge/methods.py`) on the Qt main thread to a `buddy_core` function, e.g. `features.pad`.
2. The function resolves inputs: `documents.resolve_document`, `body.resolve_body`, `documents.resolve_object` / `sketch.model.resolve_sketch`, dimensions via `values`, faces/edges via `select`.
3. Mutation runs inside `with transaction(doc, "Pad: <purpose>")`; `naming` gives the label, `display` styles the new object.
4. On exit the transaction recomputes; new invalid objects trigger rollback and `CoreError(recompute_failed)`, otherwise the undo step is committed.
5. The function fills a `ToolResult` (`add_created`/`add_modified`) and returns it; the bridge serialises `to_dict()` and records the call in the design stream (`stream.record`).

## Integration

- Consumed by: `buddy_bridge` (`methods.py`, `registry.py`, `replay.py`, `headless.py`), which uses `errors` without FreeCAD; indirectly `src/buddy_server` tools via the bridge; tests in `tests/`.
- Depends on: FreeCAD (`FreeCAD`, `FreeCADGui` only when `GuiUp`, Part/PartDesign/Sketcher) and the Python stdlib; optional workbenches (Fasteners, freecad.gears) only in `assembly.py` / `gears.py`; no MCP SDK or network.
