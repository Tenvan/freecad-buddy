"""Installed addons and macros of this FreeCAD, the way the Addon Manager sees them.

The Addon Manager treats an addon as installed when ``Mod/<id>`` exists and is not empty, and a
macro when ``<macro dir>/<file>`` (or ``Macro_<file>``) exists (spike S3, AddonCatalog.py:200-204,
addonmanager_macro.py:120-130).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import FreeCAD

from buddy_core import compat


def _mod_dir() -> Path:
    return Path(FreeCAD.getUserAppDataDir()) / "Mod"


def _macro_dir() -> Path:
    return Path(FreeCAD.getUserMacroDir(True))


def addon_status() -> dict[str, Any]:
    mod_dir, macro_dir = _mod_dir(), _macro_dir()
    addons = (
        sorted(p.name for p in mod_dir.iterdir() if p.is_dir() and any(p.iterdir()))
        if mod_dir.is_dir()
        else []
    )
    macros = sorted(p.name for p in macro_dir.iterdir() if p.is_file()) if macro_dir.is_dir() else []
    return {
        "freecad_version": list(compat.version_tuple()),
        "mod_dir": str(mod_dir),
        "macro_dir": str(macro_dir),
        "addons": addons,
        "macros": macros,
    }
