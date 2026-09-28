"""Compatibility layer: FreeCAD version info and detection of API drift in weekly builds.

Every document type the core creates must be listed in ``REQUIRED_TYPES``. A missing
type means the running FreeCAD build renamed or removed it, and tools depending on it
must fail with a clear message instead of an obscure ``addObject`` error.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

import FreeCAD

# Modules whose import registers the document types below.
_TYPE_MODULES = ("Part", "Sketcher", "PartDesign")

REQUIRED_TYPES: tuple[str, ...] = (
    "App::VarSet",
    "Sketcher::SketchObject",
    "PartDesign::Body",
    "PartDesign::Pad",
    "PartDesign::Pocket",
    "PartDesign::Revolution",
    "PartDesign::Groove",
    "PartDesign::AdditivePipe",
    "PartDesign::SubtractivePipe",
    "PartDesign::Hole",
    "PartDesign::Fillet",
    "PartDesign::Chamfer",
    "PartDesign::Thickness",
    "PartDesign::Mirrored",
    "PartDesign::LinearPattern",
    "PartDesign::PolarPattern",
    "PartDesign::MultiTransform",
    "PartDesign::Plane",
    "PartDesign::Line",
)


@dataclass(frozen=True)
class FreeCADInfo:
    version: str
    revision: str
    build_date: str
    python: str
    gui_up: bool

    def as_dict(self) -> dict[str, str | bool]:
        return {
            "version": self.version,
            "revision": self.revision,
            "build_date": self.build_date,
            "python": self.python,
            "gui_up": self.gui_up,
        }


def freecad_info() -> FreeCADInfo:
    raw = FreeCAD.Version()
    return FreeCADInfo(
        version=".".join(raw[:3]),
        revision=raw[3] if len(raw) > 3 else "",
        build_date=raw[5] if len(raw) > 5 else "",
        python=sys.version.split()[0],
        gui_up=bool(getattr(FreeCAD, "GuiUp", False)),
    )


def version_tuple() -> tuple[int, int, int]:
    major, minor, patch = (int(part) for part in FreeCAD.Version()[:3])
    return major, minor, patch


def _load_type_modules() -> None:
    for name in _TYPE_MODULES:
        __import__(name)


def missing_types(required: tuple[str, ...] = REQUIRED_TYPES) -> list[str]:
    """Return the required document types the running FreeCAD does not provide."""
    _load_type_modules()
    doc = FreeCAD.newDocument("FreeCADBuddy_TypeProbe", hidden=True, temp=True)
    try:
        supported = set(doc.supportedTypes())
    finally:
        FreeCAD.closeDocument(doc.Name)
    return [type_name for type_name in required if type_name not in supported]
