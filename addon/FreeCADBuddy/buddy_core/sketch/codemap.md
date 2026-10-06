# addon/FreeCADBuddy/buddy_core/sketch/

## Responsibility
Sketcher modelling layer: builds, constrains, analyses and validates sketches, including external geometry references.

## Design
- `model.py`: sketch creation (`create_sketch`, `plane_support`), `resolve_sketch`, and `checked_edit`/`sketch_edit`, a transaction that recomputes, analyses and rolls back on conflicts or redundancies.
- `builder.py`: `SketchBuilder` wraps geometry (`line`, `circle`, `arc`, `point`), constraints (`con`, `dim`, `anchor`) and unique constraint names.
- `profiles.py`: parametric profile functions (`rectangle`, `rounded_rectangle`, `slot`, `circle`, `polygon`, `hole_rect`, `polyline`, `u_path`) dispatched by `add_profile`.
- `lowlevel.py`: `add_geometry` and `add_constraints` for raw item lists.
- `assist.py`: `fully_constrain_sketch` adds obvious relations and dimensions for free points.
- `analysis.py`: `analyze` (DOF, solver problems, wires), `lint`, `problems`.
- `external.py`: external geometry add/describe/dangling-check for sketches, datums and shape binders.
- `refs.py`: parse and format geometry refs (`g<N>`, `x<N>`, start/end/center positions).

## Flow
1. A public function (`add_profile`, `add_geometry`, `add_constraints`, `fully_constrain_sketch`) calls `sketch_edit` with an action callback.
2. `sketch_edit` resolves document and sketch, opens `checked_edit` (`transaction`), and runs the action with a `SketchBuilder`.
3. The action resolves values and refs (`values`, `refs`, `external`) and adds geometry and constraints.
4. `checked_edit` recomputes and runs `analysis.analyze`; blocking problems raise `SKETCH_INVALID` and roll back, otherwise the report and warnings go into the `ToolResult`.

## Integration
- Consumed by: `buddy_bridge.methods` (`assist`, `lowlevel`, `model`, `profiles`), `buddy_core.design_tools`, `buddy_core.features`, `buddy_core.thread`, `buddy_core.binder`, `buddy_core.documents`.
- Depends on: `buddy_core.transaction`, `buddy_core.body`, `buddy_core.documents`, `buddy_core.errors`, `buddy_core.result`, `buddy_core.values`, `buddy_core.naming`, `FreeCAD`, `Part`, `Sketcher`.
