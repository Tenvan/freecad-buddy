"""Printer profile: build volume and print-quality defaults, persisted as TOML.

Read with ``tomllib`` (stdlib); written with a minimal serializer of our own since
``tomllib`` is read-only and a full TOML writer is not part of the standard library.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from buddy_core.errors import validation

_FILENAME = "printer-profile.toml"


@dataclass
class PrinterProfile:
    build_x: float = 256.0
    build_y: float = 256.0
    build_z: float = 256.0
    nozzle: float = 0.4
    layer_height: float = 0.2
    min_wall: float = 0.8
    overhang_angle: float = 45.0
    clearance_fit: float = 0.2
    press_fit: float = 0.05
    material: str = "PLA"
    mesh_linear_deflection: float = 0.05
    mesh_angular_deflection_deg: float = 15.0


def profile_path(environ: dict[str, str] | None = None) -> Path:
    """``FREECAD_BUDDY_HOME/printer-profile.toml``, else ``%APPDATA%\\FreeCADBuddy``."""
    env = os.environ if environ is None else environ
    home = env.get("FREECAD_BUDDY_HOME")
    base = Path(home) if home else Path(env.get("APPDATA", str(Path.home()))) / "FreeCADBuddy"
    return base / _FILENAME


def _quote(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _serialize(profile: dict[str, Any]) -> str:
    lines = [
        f"{key} = {_quote(value) if isinstance(value, str) else value}" for key, value in profile.items()
    ]
    return "\n".join(lines) + "\n"


def _load_raw(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _apply(profile: dict[str, Any], updates: dict[str, Any]) -> None:
    """Merge ``updates`` into ``profile`` in place; unknown keys or bad values are rejected."""
    for key, value in updates.items():
        if key not in profile:
            raise validation(f"Unbekannter Profil-Wert '{key}'", available=sorted(profile))
        if key == "material":
            if not isinstance(value, str) or not value.strip():
                raise validation("'material' muss ein nicht-leerer Text sein")
            if any(ord(char) < 32 or ord(char) == 127 for char in value):
                raise validation("'material' darf keine Steuerzeichen (z. B. Zeilenumbrüche) enthalten")
        else:
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise validation(f"'{key}' muss eine Zahl sein, nicht {value!r}")
            if value <= 0:
                raise validation(f"'{key}' muss positiv sein, nicht {value!r}")
        profile[key] = value


def get_printer_profile(path: str | None = None) -> dict[str, Any]:
    """Full profile (defaults merged with the saved file) plus its ``path``."""
    target = Path(path) if path else profile_path()
    profile = asdict(PrinterProfile())
    _apply(profile, _load_raw(target))
    return {**profile, "path": str(target)}


def set_printer_profile(updates: dict[str, Any], path: str | None = None) -> dict[str, Any]:
    """Merge ``updates`` into the saved profile (or the defaults) and persist it."""
    if not updates:
        raise validation("Keine Profil-Werte angegeben")
    target = Path(path) if path else profile_path()
    profile = asdict(PrinterProfile())
    _apply(profile, _load_raw(target))
    _apply(profile, updates)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_serialize(profile), encoding="utf-8")
    return {**profile, "path": str(target)}
