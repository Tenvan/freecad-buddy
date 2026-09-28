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
HEADLESS_RUNNER = REPO_ROOT / "tools" / "run_headless_bridge.py"

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")
_INTERPRETER_OVERRIDES = ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV", "__PYVENV_LAUNCHER__")


class FreeCADNotFoundError(RuntimeError):
    pass


class AddonInstallError(RuntimeError):
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


def install_addon(mod_dir: Path, source: Path, force: bool = False) -> str:
    """Install FreeCADBuddy as a junction ``mod_dir / "FreeCADBuddy" -> source``."""
    link = mod_dir / "FreeCADBuddy"
    resolved_source = Path(os.path.realpath(source))

    if os.path.isjunction(link):
        current_target = Path(os.path.realpath(link))
        if current_target == resolved_source:
            return f"FreeCADBuddy ist bereits installiert: {link} -> {current_target}"
        if not force:
            raise AddonInstallError(
                f"{link} zeigt bereits auf {current_target}, nicht auf {resolved_source}. "
                "Mit --force überschreiben."
            )
        os.rmdir(link)
    elif link.exists():
        raise AddonInstallError(f"{link} existiert bereits und ist keine Junction. Manuell entfernen.")

    mod_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(source)], check=True, capture_output=True)
    return f"FreeCADBuddy installiert: {link} -> {source}"


def uninstall_addon(mod_dir: Path) -> str:
    """Remove the FreeCADBuddy junction (only the link, never its target's content)."""
    link = mod_dir / "FreeCADBuddy"
    if not link.exists() and not os.path.isjunction(link):
        return "FreeCADBuddy ist nicht installiert."
    if not os.path.isjunction(link):
        raise AddonInstallError(f"{link} ist keine Junction und wird nicht entfernt.")
    os.rmdir(link)
    return f"FreeCADBuddy deinstalliert: {link} entfernt."


def addon_status(mod_dir: Path, source: Path) -> str:
    """Report whether the FreeCADBuddy junction is installed and where it points to."""
    link = mod_dir / "FreeCADBuddy"
    resolved_source = Path(os.path.realpath(source))

    if os.path.isjunction(link):
        current_target = Path(os.path.realpath(link))
        if current_target == resolved_source:
            return f"FreeCADBuddy ist installiert: {link} -> {current_target}"
        return (
            f"FreeCADBuddy zeigt auf ein anderes Ziel: {link} -> {current_target} "
            f"(erwartet {resolved_source})"
        )
    if link.exists():
        return f"{link} existiert, ist aber keine Junction."
    return "FreeCADBuddy ist nicht installiert."


def user_mod_dir(home: Path) -> Path:
    """Ask FreeCAD's own interpreter for its user Mod directory.

    Only FreeCAD itself knows the per-version app data path (e.g. ``v26-3``), so this
    starts ``home``'s Python, imports FreeCAD and reads ``getUserAppDataDir()``.
    """
    snippet = (
        "import os, sys; "
        f"sys.path[0:0] = [r'{home / 'bin'}', r'{home / 'lib'}']; "
        f"os.add_dll_directory(r'{home / 'bin'}'); "
        "import FreeCAD; "
        "print(FreeCAD.getUserAppDataDir())"
    )
    result = subprocess.run(
        [str(home / "bin" / "python.exe"), "-c", snippet],
        check=True,
        capture_output=True,
        text=True,
        env=freecad_subprocess_env(),
    )
    return Path(result.stdout.strip()) / "Mod"


def run_core_tests(pytest_args: list[str]) -> int:
    home = find_freecad_home()
    site_packages = sysconfig.get_paths()["purelib"]
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]
    explicit_paths = any(not arg.startswith("-") and Path(arg).exists() for arg in pytest_args)
    test_dirs = [
        directory
        for directory in (REPO_ROOT / "tests" / "core", REPO_ROOT / "tests" / "bridge")
        if not explicit_paths and directory.is_dir() and any(directory.glob("test_*.py"))
    ]
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
        *(str(directory) for directory in test_dirs),
        *pytest_args,
    ]
    print(f"[freecad_env] FreeCAD: {home}", flush=True)
    env = freecad_subprocess_env()
    # Plugins registered by venv packages (entry points) may not import in FreeCAD's interpreter.
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return subprocess.call(cmd, cwd=REPO_ROOT, env=env)


def start_headless_bridge(
    port: int = 0,
    token_file: Path | None = None,
    extra_env: dict[str, str] | None = None,
    stdout: int | None = subprocess.PIPE,
) -> subprocess.Popen[str]:
    """Start the bridge in FreeCAD's Python without GUI (stdin=PIPE: closing it stops the bridge)."""
    home = find_freecad_home()
    cmd = [
        str(home / "bin" / "python.exe"),
        str(HEADLESS_RUNNER),
        "--freecad-home",
        str(home),
        "--addon-dir",
        str(ADDON_DIR),
        "--port",
        str(port),
    ]
    if token_file is not None:
        cmd += ["--token-file", str(token_file)]
    env = {**freecad_subprocess_env(), **(extra_env or {})}
    return subprocess.Popen(
        cmd, cwd=REPO_ROOT, env=env, stdin=subprocess.PIPE, stdout=stdout, stderr=subprocess.STDOUT, text=True
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("where", help="FreeCAD-Installationspfad ausgeben")
    run = sub.add_parser("run-core-tests", help="tests/core und tests/bridge in FreeCADs Python ausführen")
    run.add_argument("pytest_args", nargs=argparse.REMAINDER)
    install = sub.add_parser(
        "install-addon", help="FreeCADBuddy als Junction in FreeCADs Mod-Verzeichnis installieren"
    )
    install.add_argument("--force", action="store_true", help="abweichende Junction überschreiben")
    sub.add_parser("uninstall-addon", help="FreeCADBuddy-Junction aus FreeCADs Mod-Verzeichnis entfernen")
    sub.add_parser("addon-status", help="Installationsstatus von FreeCADBuddy anzeigen")
    headless = sub.add_parser("headless-bridge", help="Bridge ohne GUI in FreeCADs Python starten")
    headless.add_argument("--port", type=int, default=9876)
    args = parser.parse_args(argv)

    try:
        if args.command == "where":
            print(find_freecad_home())
            return 0
        if args.command == "install-addon":
            mod_dir = user_mod_dir(find_freecad_home())
            print(install_addon(mod_dir, ADDON_DIR, force=args.force))
            return 0
        if args.command == "uninstall-addon":
            mod_dir = user_mod_dir(find_freecad_home())
            print(uninstall_addon(mod_dir))
            return 0
        if args.command == "addon-status":
            mod_dir = user_mod_dir(find_freecad_home())
            print(addon_status(mod_dir, ADDON_DIR))
            return 0
        if args.command == "headless-bridge":
            process = start_headless_bridge(port=args.port, stdout=None)
            return process.wait()
        return run_core_tests(args.pytest_args)
    except (FreeCADNotFoundError, AddonInstallError) as error:
        print(f"[freecad_env] {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
