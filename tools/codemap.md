# tools/

## Responsibility

Developer tooling: build/test scripts that launch FreeCAD's bundled Python in a clean environment, generate the tool documentation, and provide in-GUI acceptance checks.

## Design

- `freecad_env.py`: CLI dispatcher (`where`, `run-core-tests`, `install-addon`, `uninstall-addon`, `addon-status`, `headless-bridge`). Locates the FreeCAD installation (`find_freecad_home`), builds a sanitized subprocess environment (`freecad_subprocess_env` drops `PYTHONHOME`, `PYTHONPATH`, `VIRTUAL_ENV`, `__PYVENV_LAUNCHER__` so FreeCAD does not load the uv Python stdlib), and manages the addon junction in FreeCAD's user Mod directory (`install_addon`, `uninstall_addon`, `addon_status`).
- `run_core_tests.py`: entry point executed by FreeCAD's `python.exe`. Sets `sys.path` (FreeCAD, addon, then project-venv site-packages for pytest), imports FreeCAD, drops stale `buddy_core`/`buddy_bridge` modules, runs pytest.
- `run_headless_bridge.py`: entry point executed by FreeCAD's `python.exe`. Same path setup, then starts `buddy_bridge.headless.main` without GUI.
- `gen_tool_docs.py`: builds the MCP app (`buddy_server.app.build_mcp`) and renders `docs/tools.md` plus `docs/tools/<group>.md` from registered tools and the `EXAMPLES` table; `--check` fails on outdated files.
- `gui_checks.py`: acceptance checks (G13 `task_panels`, G14 `storepoint_tree`) from `docs/acceptance.md`, run inside the FreeCAD GUI via `execute_python`; drives FreeCADGui/Qt in-process.

## Flow

1. `poe test-core` → `freecad_env.py run-core-tests` → `find_freecad_home` + `freecad_subprocess_env` → FreeCAD `python.exe` → `run_core_tests.py` → pytest (core and bridge tests).
2. `poe headless-bridge` → `freecad_env.py headless-bridge` → FreeCAD `python.exe` → `run_headless_bridge.py` → `buddy_bridge.headless.main` (also used for E2E tests against the headless bridge).
3. `poe install-addon` / `uninstall-addon` / `addon-status` → `freecad_env.py` manages the `addon/FreeCADBuddy` junction in FreeCAD's Mod directory.
4. `uv run python tools/gen_tool_docs.py` → imports `buddy_server` tool groups → writes `docs/tools.md` and `docs/tools/`.
5. `gui_checks.py` is loaded by `exec` inside the FreeCAD GUI and returns a result dict.

## Integration

- Consumed by: poe tasks in `pyproject.toml` (`test-core`, `install-addon`, `uninstall-addon`, `addon-status`, `headless-bridge`; `test` and `check` via `test-core`); `tests/tools/test_freecad_env.py`, `tests/tools/test_install_addon.py` and `tests/tools/test_tool_docs.py`; the GUI acceptance process in `docs/acceptance.md`.
- Depends on: a FreeCAD installation, `addon/FreeCADBuddy` (`buddy_bridge.headless`), `src/buddy_server` (`app`, `bridge`, `config`, `events`, `tools`), pytest from the project venv, FreeCADGui/PySide in `gui_checks.py`.
