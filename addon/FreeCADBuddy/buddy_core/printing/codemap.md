# addon/FreeCADBuddy/buddy_core/printing/

## Responsibility
Print-preparation service layer: printer profile persistence, read-only printability analysis, and verified STL/3MF/STEP export of the print target.

## Design
- `profile.py`: `PrinterProfile` dataclass of defaults (build volume, nozzle, layer height, tolerances, mesh deflection); TOML read with `tomllib`, written by a minimal own serializer; `_apply` validates keys and values.
- `check.py`: `check_printability` combines build-volume, overhang, thin-wall (ray sampling) and small-feature checks into issues plus `design_hints`; `resolve_target` picks the object (default: the single body). No document mutation.
- `export.py`: `export_body` works on a copy of the shape, optionally places it on the bed, writes via `MeshPart`/`exportStep`, then reimports the file and warns on volume deviation above 1 %.
- `__init__.py`: re-exports the four public functions.

## Flow
1. `get_printer_profile` merges defaults with `printer-profile.toml` (`FREECAD_BUDDY_HOME` or `%APPDATA%/FreeCADBuddy`); `set_printer_profile` merges updates and rewrites the file.
2. `check_printability` loads the profile, resolves the target via `resolve_target`, runs the checks and returns an issue report.
3. `export_body` validates the format, resolves target and output path, refuses to overwrite without `overwrite`, writes the file.
4. It reimports the file, computes the volume deviation and returns the result with warnings.

## Integration
- Consumed by: `buddy_bridge.methods` (`check`, `export`, `profile`).
- Depends on: `buddy_core.body`, `buddy_core.documents`, `buddy_core.errors`, `buddy_core.result`, `buddy_core.naming`, `Part`, `Mesh`, `MeshPart`, `FreeCAD`.
