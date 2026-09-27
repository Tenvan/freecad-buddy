"""Locate the FreeCAD installation and run the core test suite inside FreeCAD's Python.

The core package imports FreeCAD modules, so its tests must run in the interpreter
that ships with FreeCAD. Nothing is installed into FreeCAD's environment: pure-Python
test dependencies (pytest & co.) are borrowed from the project venv via ``sys.path``.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import sysconfig
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ADDON_DIR = REPO_ROOT / "addon" / "FreeCADBuddy"
CORE_RUNNER = REPO_ROOT / "tools" / "run_core_tests.py"

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")
_INTERPRETER_OVERRIDES = ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "__PYVENV_LAUNCHER__")


class FreeCADNotFoundError(RuntimeError):
    pass


def _version_key(path: Path) -> tuple[int, ...]:
    match = _VERSION_RE.search(path.name)
    return tuple(int(part) for part in match.group(1).split(".")) if match else ()


def is_freecad_home(path: Path) -> bool:
    return (path / "bin" / "python.exe").is_file() and (path / "bin" / "FreeCAD.pyd").is_file()


def candidate_roots(environ: os._Environ[str] | dict[str, str]) -> list[Path]:
    roots = []
    for var, sub in (("LOCALAPPDATA", "Programs"), ("ProgramFiles", ""), ("ProgramW6432", "")):
        base = environ.get(var)
        if base:
            roots.append(Path(base) / sub if sub else Path(base))
    return roots


def find_freecad_home(environ: os._Environ[str] | dict[str, str] | None = None) -> Path:
    """Return the FreeCAD installation directory.

    ``FREECAD_HOME`` wins; otherwise the highest version below the usual install roots.
    """
    env = os.environ if environ is None else environ
    explicit = env.get("FREECAD_HOME")
    if explicit:
        home = Path(explicit)
        if not is_freecad_home(home):
            raise FreeCADNotFoundError(
                f"FREECAD_HOME={home} ist keine FreeCAD-Installation (bin/python.exe fehlt)"
            )
        return home

    found = [
        path
        for root in candidate_roots(env)
        if root.is_dir()
        for path in root.glob("FreeCAD*")
        if is_freecad_home(path)
    ]
    if not found:
        raise FreeCADNotFoundError("Keine FreeCAD-Installation gefunden. FREECAD_HOME setzen.")
    return max(found, key=_version_key)


def freecad_subprocess_env(environ: os._Environ[str] | dict[str, str] | None = None) -> dict[str, str]:
    """Environment for FreeCAD's interpreter without the venv's interpreter overrides.

    Inside ``uv run`` the venv launcher exports ``PYTHONHOME``; inherited by FreeCAD's
    ``python.exe`` it would load a foreign stdlib (conda-forge vs. python.org build).
    """
    env = dict(os.environ if environ is None else environ)
    for key in _INTERPRETER_OVERRIDES:
        env.pop(key, None)
    return env


def run_core_tests(pytest_args: list[str]) -> int:
    home = find_freecad_home()
    site_packages = sysconfig.get_paths()["purelib"]
    cmd = [
        str(home / "bin" / "python.exe"),
        str(CORE_RUNNER),
        "--freecad-home",
        str(home),
        "--site-packages",
        site_packages,
        "--addon-dir",
        str(ADDON_DIR),
        "--",
        str(REPO_ROOT / "tests" / "core"),
        *pytest_args,
    ]
    print(f"[freecad_env] FreeCAD: {home}", flush=True)
    return subprocess.call(cmd, cwd=REPO_ROOT, env=freecad_subprocess_env())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("where", help="FreeCAD-Installationspfad ausgeben")
    run = sub.add_parser("run-core-tests", help="tests/core in FreeCADs Python ausführen")
    run.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)

    try:
        if args.command == "where":
            print(find_freecad_home())
            return 0
        return run_core_tests(args.pytest_args)
    except FreeCADNotFoundError as error:
        print(f"[freecad_env] {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
