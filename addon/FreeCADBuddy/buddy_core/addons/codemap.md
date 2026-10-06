# addon/FreeCADBuddy/buddy_core/addons/

## Responsibility
Adapter around FreeCAD's Addon Manager: reports installed addons/macros and runs user-confirmed install jobs. The only place in `buddy_core` allowed to import Addon Manager modules.

## Design
- `install.py`: job-based installer. `Job` dataclass tracks state (`awaiting_confirmation` -> `declined` | `installing` -> `installed` | `failed`), keeps Qt objects alive, and removes a half-written `Mod/<id>` on failure.
- `install.py`: `Backend` Protocol with `AddonManagerBackend` as the real implementation (modal confirmation dialog, `AddonInstaller` in a `QThread`, `MacroInstaller`); `set_backend` swaps it for tests.
- `install.py`: module-level `_jobs` registry guarded by `_lock`; a second request for a running addon returns the existing job.
- `status.py`: read-only directory scan of `Mod/` and the macro dir, versioned via `compat.version_tuple()`.
- `__init__.py`: docstring only.

## Flow
1. `start_install` validates `kind`, asks `Backend.available()` (needs GUI), creates or reuses a `Job`, and schedules `_run` on the Qt main thread.
2. `_run` shows `Backend.confirm`; on decline the job ends `declined`.
3. On consent the state becomes `installing`; `install_macro` or `install_workbench` runs.
4. The installer's `success`/`failure` signals call `Job.finish`; failures trigger cleanup.
5. The client polls `install_status(job_id)` until `done`.
6. `status.addon_status()` returns FreeCAD version, directories, addon and macro names.

## Integration
- Consumed by: `buddy_bridge.methods` (imports `install` as `addon_install`, `status` as `addon_status`).
- Depends on: `buddy_core.errors` (`CoreError`, `UNSUPPORTED`, `not_found`, `validation`), `buddy_core.compat`, `FreeCAD`, `PySide`, Addon Manager modules (`install.py` only).
