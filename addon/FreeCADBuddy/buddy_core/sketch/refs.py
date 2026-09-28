"""Textual element references for sketch geometry.

``g3`` = edge of geometry 3, ``g3.start`` / ``g3.end`` / ``g3.center`` = its points,
``x0`` = first external geometry (FreeCAD GeoId -3), ``x0.center`` etc. = its points,
``origin`` = sketch origin, ``x_axis`` / ``y_axis`` = sketch axes.
"""

from __future__ import annotations

import re
from typing import Any

from buddy_core.errors import validation

NONE, START, END, CENTER = 0, 1, 2, 3
ROOT = (-1, START)
H_AXIS = (-1, NONE)
V_AXIS = (-2, NONE)
FIRST_EXTERNAL = -3  # FreeCAD GeoId of the first external geometry; -1/-2 are the sketch axes

_POSITIONS = {"start": START, "end": END, "center": CENTER, "mid": CENTER}
_REF = re.compile(r"^([gx])(\d+)(?:\.(start|end|center|mid))?$")


def position(name: str | None) -> int:
    """PosId for a suffix name (``start``/``end``/``center``/``mid``); ``NONE`` for the edge itself."""
    return _POSITIONS.get(name or "", NONE)


def external_geo_id(index: int) -> int:
    """GeoId of external geometry ``x<index>``."""
    return FIRST_EXTERNAL - index


def external_index(geo_id: int) -> int:
    """Index ``N`` of ``x<N>`` for an external GeoId."""
    return FIRST_EXTERNAL - geo_id


def external_count(sketch: Any) -> int:
    """Number of external geometries (``ExternalGeo`` also lists the two sketch axes first)."""
    return max(len(sketch.ExternalGeo) - 2, 0)


def parse(ref: str, sketch: Any) -> tuple[int, int]:
    """Return ``(geo_id, pos_id)`` for a textual reference."""
    key = ref.strip().lower()
    if key == "origin":
        return ROOT
    if key in ("x_axis", "h_axis"):
        return H_AXIS
    if key in ("y_axis", "v_axis"):
        return V_AXIS
    match = _REF.match(key)
    if not match:
        raise validation(
            f"Invalid reference '{ref}'. Allowed: g<N>, x<N> (external), with .start|end|center, "
            "origin, x_axis, y_axis"
        )
    kind, number = match.group(1), int(match.group(2))
    pos_id = position(match.group(3))
    if kind == "x":
        count = external_count(sketch)
        if number >= count:
            raise validation(
                f"External geometry x{number} does not exist (sketch has {count}); "
                "add it with add_geometry type 'external'"
            )
        return external_geo_id(number), pos_id
    if number >= sketch.GeometryCount:
        raise validation(f"Geometry g{number} does not exist (sketch has {sketch.GeometryCount})")
    return number, pos_id


def is_point(ref: tuple[int, int]) -> bool:
    return ref[1] != NONE


def format_ref(geo_id: int, pos_id: int = NONE) -> str:
    if (geo_id, pos_id) == ROOT:
        return "origin"
    if (geo_id, pos_id) == H_AXIS:
        return "x_axis"
    if (geo_id, pos_id) == V_AXIS:
        return "y_axis"
    suffix = {START: ".start", END: ".end", CENTER: ".center"}.get(pos_id, "")
    if geo_id <= FIRST_EXTERNAL:
        return f"x{external_index(geo_id)}{suffix}"
    return f"g{geo_id}{suffix}"
