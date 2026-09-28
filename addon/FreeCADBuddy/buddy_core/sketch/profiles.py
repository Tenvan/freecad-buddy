"""Intent-level profiles that produce fully constrained sketches the way a person draws them.

Patterns: shapes are centred on the origin via symmetry (not two position dimensions),
repeated sizes use ``Equal`` instead of duplicate dimensions, helper geometry is marked as
construction, every dimension has a name and can be bound to a parameter.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Any

from buddy_core import naming, values
from buddy_core.errors import validation
from buddy_core.result import ToolResult
from buddy_core.sketch.builder import SketchBuilder
from buddy_core.sketch.model import sketch_edit
from buddy_core.sketch.refs import CENTER, END, START
from buddy_core.values import Value

Params = dict[str, Any]


def _value(doc: Any, params: Params, key: str, positive: bool = True) -> Value:
    if key not in params:
        raise validation(f"Parameter '{key}' fehlt")
    value = values.resolve(doc, params[key], key)
    if positive and value.number <= 0:
        raise validation(f"'{key}' muss > 0 sein")
    return value


def _center(doc: Any, params: Params) -> tuple[Value, Value]:
    center = params.get("center", [0, 0])
    if not isinstance(center, list | tuple) or len(center) != 2:
        raise validation("'center' muss [x, y] sein")
    return values.resolve(doc, center[0], "center.x"), values.resolve(doc, center[1], "center.y")


def _is_origin(center: tuple[Value, Value]) -> bool:
    return all(v.number == 0 and not v.expression for v in center)


def _center_about(b: SketchBuilder, center: tuple[Value, Value]) -> tuple[int, int]:
    """Point to centre a shape on: the origin, or a construction point placed by dimensions."""
    if _is_origin(center):
        return -1, START
    point = b.point((center[0].number, center[1].number))
    b.sketch.setConstruction(point, True)
    b.anchor(point, START, center, "Center")
    return point, START


def rectangle(b: SketchBuilder, doc: Any, params: Params, construction: bool = False) -> list[int]:
    w, h = _value(doc, params, "width"), _value(doc, params, "height")
    center = _center(doc, params)
    anchor = params.get("anchor", "center")
    cx, cy = center[0].number, center[1].number
    x0, x1, y0, y1 = cx - w.number / 2, cx + w.number / 2, cy - h.number / 2, cy + h.number / 2
    if anchor == "corner":
        x0, y0, x1, y1 = cx, cy, cx + w.number, cy + h.number
    elif anchor != "center":
        raise validation("'anchor' muss 'center' oder 'corner' sein")
    bottom = b.line((x0, y0), (x1, y0), construction)
    right = b.line((x1, y0), (x1, y1), construction)
    top = b.line((x1, y1), (x0, y1), construction)
    left = b.line((x0, y1), (x0, y0), construction)
    lines = [bottom, right, top, left]
    for current, following in zip(lines, lines[1:] + lines[:1], strict=True):
        b.con("Coincident", current, END, following, START)
    b.con("Horizontal", bottom)
    b.con("Horizontal", top)
    b.con("Vertical", right)
    b.con("Vertical", left)
    b.dim("DistanceX", bottom, START, bottom, END, value=w, what="Width")
    b.dim("DistanceY", right, START, right, END, value=h, what="Height")
    if anchor == "corner":
        b.anchor(bottom, START, center, "Corner")
    else:
        about = _center_about(b, center)
        b.con("Symmetric", bottom, START, right, END, *about)
    return lines


def rounded_rectangle(b: SketchBuilder, doc: Any, params: Params) -> list[int]:
    w, h, r = _value(doc, params, "width"), _value(doc, params, "height"), _value(doc, params, "radius")
    if 2 * r.number >= min(w.number, h.number):
        raise validation("'radius' muss kleiner als die halbe Breite und Höhe sein")
    center = _center(doc, params)
    cx, cy = center[0].number, center[1].number
    hw, hh, rr = w.number / 2, h.number / 2, r.number
    x0, x1, y0, y1 = cx - hw, cx + hw, cy - hh, cy + hh
    bottom = b.line((x0 + rr, y0), (x1 - rr, y0))
    arc_br = b.arc((x1 - rr, y0 + rr), rr, -90, 0)
    right = b.line((x1, y0 + rr), (x1, y1 - rr))
    arc_tr = b.arc((x1 - rr, y1 - rr), rr, 0, 90)
    top = b.line((x1 - rr, y1), (x0 + rr, y1))
    arc_tl = b.arc((x0 + rr, y1 - rr), rr, 90, 180)
    left = b.line((x0, y1 - rr), (x0, y0 + rr))
    arc_bl = b.arc((x0 + rr, y0 + rr), rr, 180, 270)
    for line, arc_after in ((bottom, arc_br), (right, arc_tr), (top, arc_tl), (left, arc_bl)):
        b.con("Tangent", line, END, arc_after, START)
    for arc, line_after in ((arc_br, right), (arc_tr, top), (arc_tl, left), (arc_bl, bottom)):
        b.con("Tangent", arc, END, line_after, START)
    b.con("Horizontal", bottom)
    b.con("Horizontal", top)
    b.con("Vertical", right)
    b.con("Vertical", left)
    for arc in (arc_tr, arc_tl, arc_bl):
        b.con("Equal", arc_br, arc)
    b.dim("Radius", arc_br, value=r, what="Radius")
    b.dim("DistanceX", left, START, right, START, value=w, what="Width")
    b.dim("DistanceY", bottom, START, top, START, value=h, what="Height")
    b.con("Symmetric", arc_bl, CENTER, arc_tr, CENTER, *_center_about(b, center))
    return [bottom, arc_br, right, arc_tr, top, arc_tl, left, arc_bl]


def slot(b: SketchBuilder, doc: Any, params: Params) -> list[int]:
    length, width = _value(doc, params, "length"), _value(doc, params, "width")
    center = _center(doc, params)
    cx, cy = center[0].number, center[1].number
    half, r = length.number / 2, width.number / 2
    right = b.arc((cx + half, cy), r, -90, 90)
    top = b.line((cx + half, cy + r), (cx - half, cy + r))
    left = b.arc((cx - half, cy), r, 90, 270)
    bottom = b.line((cx - half, cy - r), (cx + half, cy - r))
    b.con("Tangent", right, END, top, START)
    b.con("Tangent", top, END, left, START)
    b.con("Tangent", left, END, bottom, START)
    b.con("Tangent", bottom, END, right, START)
    b.con("Horizontal", top)
    b.con("Equal", left, right)
    b.dim("Radius", right, value=width.scaled(0.5), what="Radius")
    b.dim("DistanceX", left, CENTER, right, CENTER, value=length, what="Length")
    b.con("Symmetric", left, CENTER, right, CENTER, *_center_about(b, center))
    return [right, top, left, bottom]


def circle(b: SketchBuilder, doc: Any, params: Params) -> list[int]:
    d = _value(doc, params, "diameter")
    center = _center(doc, params)
    geo = b.circle((center[0].number, center[1].number), d.number / 2)
    b.dim("Diameter", geo, value=d, what="Diameter")
    b.anchor(geo, CENTER, center, "Center")
    return [geo]


def polygon(b: SketchBuilder, doc: Any, params: Params) -> list[int]:
    sides = params.get("sides", 6)
    if not isinstance(sides, int) or sides < 3:
        raise validation("'sides' muss eine ganze Zahl >= 3 sein")
    if "across_flats" in params:
        size = _value(doc, params, "across_flats").scaled(1 / math.cos(math.pi / sides))
    else:
        size = _value(doc, params, "diameter")
    center = _center(doc, params)
    cx, cy = center[0].number, center[1].number
    radius = size.number / 2
    helper = b.circle((cx, cy), radius, construction=True)
    start = -math.pi / 2 - math.pi / sides  # first edge horizontal at the bottom
    corners = [
        (
            cx + radius * math.cos(start + k * 2 * math.pi / sides),
            cy + radius * math.sin(start + k * 2 * math.pi / sides),
        )
        for k in range(sides)
    ]
    edges = [b.line(corners[k], corners[(k + 1) % sides]) for k in range(sides)]
    for k, edge in enumerate(edges):
        b.con("Coincident", edge, END, edges[(k + 1) % sides], START)
        b.con("PointOnObject", edge, START, helper)
    for edge in edges[1:]:
        b.con("Equal", edges[0], edge)
    b.con("Horizontal", edges[0])
    b.dim("Diameter", helper, value=size, what="Diameter")
    b.anchor(helper, CENTER, center, "Center")
    return [helper, *edges]


def hole_rect(b: SketchBuilder, doc: Any, params: Params) -> list[int]:
    """Four equal circles on the corners of a construction rectangle (screw pattern)."""
    d = _value(doc, params, "diameter")
    frame = rectangle(b, doc, {**params, "anchor": "center"}, construction=True)
    circles = []
    for line in frame:
        x, y = b.sketch.Geometry[line].StartPoint.x, b.sketch.Geometry[line].StartPoint.y
        geo = b.circle((x, y), d.number / 2)
        b.con("Coincident", geo, CENTER, line, START)
        circles.append(geo)
    for geo in circles[1:]:
        b.con("Equal", circles[0], geo)
    b.dim("Diameter", circles[0], value=d, what="HoleDiameter")
    return [*frame, *circles]


def polyline(b: SketchBuilder, doc: Any, params: Params) -> list[int]:
    """Closed outline through the given points; axis-parallel segments get H/V constraints.

    Remaining freedom is reported so the agent can add dimensions or use the assistant.
    """
    points = params.get("points")
    if not isinstance(points, list) or len(points) < 3:
        raise validation("'points' muss eine Liste mit mindestens 3 Punkten [x, y] sein")
    coords = [(float(p[0]), float(p[1])) for p in points]
    edges = [b.line(coords[k], coords[(k + 1) % len(coords)]) for k in range(len(coords))]
    for k, edge in enumerate(edges):
        b.con("Coincident", edge, END, edges[(k + 1) % len(edges)], START)
        (x0, y0), (x1, y1) = coords[k], coords[(k + 1) % len(coords)]
        if abs(y1 - y0) < 1e-9:
            b.con("Horizontal", edge)
        elif abs(x1 - x0) < 1e-9:
            b.con("Vertical", edge)
        if abs(x0) < 1e-9 and abs(y0) < 1e-9:
            b.con("Coincident", -1, START, edge, START)
    return edges


PROFILES: dict[str, Callable[[SketchBuilder, Any, Params], list[int]]] = {
    "rectangle": rectangle,
    "rounded_rectangle": rounded_rectangle,
    "slot": slot,
    "circle": circle,
    "polygon": polygon,
    "hole_rect": hole_rect,
    "polyline": polyline,
}


def add_profile(
    sketch: str,
    kind: str,
    params: Params,
    prefix: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Add a profile; dimensions accept numbers or parameter names (bound via expression)."""
    if kind not in PROFILES:
        raise validation(f"Unbekanntes Profil '{kind}' (erlaubt: {', '.join(PROFILES)})")

    def action(doc: Any, sk: Any, result: ToolResult) -> None:
        builder = SketchBuilder(sk, naming.sanitize(prefix) if prefix else "")
        geometry = PROFILES[kind](builder, doc, params)
        result.data["geometry"] = geometry
        result.data["constraints"] = builder.constraints

    return sketch_edit(sketch, document, f"Profil {kind}", action)
