"""Textual element references for sketch geometry.

``g3`` = edge of geometry 3, ``g3.start`` / ``g3.end`` / ``g3.center`` = its points,
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

_POSITIONS = {"start": START, "end": END, "center": CENTER, "mid": CENTER}
_REF = re.compile(r"^g(\d+)(?:\.(start|end|center|mid))?$")


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
            f"Ungültige Referenz '{ref}'. Erlaubt: g<N>, g<N>.start|end|center, origin, x_axis, y_axis"
        )
    geo_id = int(match.group(1))
    if geo_id >= sketch.GeometryCount:
        raise validation(f"Geometrie g{geo_id} existiert nicht (Skizze hat {sketch.GeometryCount})")
    return geo_id, _POSITIONS.get(match.group(2) or "", NONE)


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
    return f"g{geo_id}{suffix}"
