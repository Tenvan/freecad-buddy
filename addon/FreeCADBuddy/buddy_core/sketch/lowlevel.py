"""Low-level sketch editing (fallback when no profile fits): geometry and constraints."""

from __future__ import annotations

from typing import Any

from buddy_core import naming, values
from buddy_core.errors import validation
from buddy_core.result import ToolResult
from buddy_core.sketch import refs
from buddy_core.sketch.builder import SketchBuilder
from buddy_core.sketch.model import sketch_edit


def _point(item: dict[str, Any], key: str) -> tuple[float, float]:
    value = item.get(key)
    if not isinstance(value, list | tuple) or len(value) != 2:
        raise validation(f"'{key}' muss [x, y] sein")
    return float(value[0]), float(value[1])


def _add_geometry_item(b: SketchBuilder, item: dict[str, Any]) -> int:
    kind = item.get("type")
    construction = bool(item.get("construction", False))
    if kind == "line":
        return b.line(_point(item, "start"), _point(item, "end"), construction)
    if kind == "circle":
        return b.circle(_point(item, "center"), float(item["radius"]), construction)
    if kind == "arc":
        return b.arc(
            _point(item, "center"),
            float(item["radius"]),
            float(item["start_angle"]),
            float(item["end_angle"]),
            construction,
        )
    if kind == "point":
        return b.point(_point(item, "at"))
    raise validation(f"Unbekannter Geometrietyp '{kind}' (erlaubt: line, circle, arc, point)")


def add_geometry(sketch: str, items: list[dict[str, Any]], document: str | None = None) -> ToolResult:
    """Add lines/circles/arcs/points (angles in degrees, counter-clockwise)."""
    if not items:
        raise validation("Keine Geometrie angegeben")

    def action(doc: Any, sk: Any, result: ToolResult) -> None:
        builder = SketchBuilder(sk, "")
        ids = [_add_geometry_item(builder, item) for item in items]
        result.data["geometry"] = [refs.format_ref(i) for i in ids]

    return sketch_edit(sketch, document, "Geometrie", action)


_TWO_EDGES = {"parallel": "Parallel", "perpendicular": "Perpendicular", "equal": "Equal"}
_DIMENSIONS = {
    "distance": "Distance",
    "distance_x": "DistanceX",
    "distance_y": "DistanceY",
    "radius": "Radius",
    "diameter": "Diameter",
    "angle": "Angle",
}


def _refs(sk: Any, item: dict[str, Any], *keys: str) -> list[tuple[int, int]]:
    parsed = []
    for key in keys:
        if key not in item:
            raise validation(f"'{key}' fehlt für Constraint '{item.get('type')}'")
        parsed.append(refs.parse(str(item[key]), sk))
    return parsed


def _flat(parsed: list[tuple[int, int]], edge_only: tuple[bool, ...]) -> list[int]:
    args: list[int] = []
    for (geo, pos), edge in zip(parsed, edge_only, strict=True):
        args.extend([geo] if edge else [geo, pos])
    return args


def _add_constraint_item(b: SketchBuilder, doc: Any, item: dict[str, Any]) -> int:
    sk = b.sketch
    kind = item.get("type")
    if kind == "coincident":
        a, c = _refs(sk, item, "a", "b")
        return b.con("Coincident", *a, *c)
    if kind in ("horizontal", "vertical"):
        name = kind.capitalize()
        if "b" in item:
            a, c = _refs(sk, item, "a", "b")
            return b.con(name, *a, *c)
        (a,) = _refs(sk, item, "a")
        return b.con(name, a[0])
    if kind in _TWO_EDGES:
        a, c = _refs(sk, item, "a", "b")
        return b.con(_TWO_EDGES[kind], a[0], c[0])
    if kind == "tangent":
        a, c = _refs(sk, item, "a", "b")
        if refs.is_point(a) and refs.is_point(c):
            return b.con("Tangent", *a, *c)
        return b.con("Tangent", a[0], c[0])
    if kind == "point_on_object":
        a, c = _refs(sk, item, "a", "b")
        return b.con("PointOnObject", *a, c[0])
    if kind == "symmetric":
        a, c, about = _refs(sk, item, "a", "b", "about")
        return b.con("Symmetric", *a, *c, *(about if refs.is_point(about) else [about[0]]))
    if kind in _DIMENSIONS:
        if "value" not in item:
            raise validation(f"'value' fehlt für Maß '{kind}'")
        value = values.resolve(doc, item["value"], kind)
        what = naming.sanitize(str(item.get("name") or kind.replace("_", " ")))
        keys = ("a", "b") if "b" in item else ("a",)
        parsed = _refs(sk, item, *keys)
        if kind in ("radius", "diameter"):
            args = [parsed[0][0]]
        elif kind == "angle":
            args = [p[0] for p in parsed]  # line to x-axis, or between two lines
        elif len(parsed) == 1:
            args = _flat(parsed, (not refs.is_point(parsed[0]),))
        else:
            args = _flat(parsed, (False, not refs.is_point(parsed[1])))
        return b.dim(_DIMENSIONS[kind], *args, value=value, what=what, angle=kind == "angle")
    raise validation(
        f"Unbekannter Constraint '{kind}' (erlaubt: coincident, horizontal, vertical, parallel, perpendicular, "
        f"equal, tangent, point_on_object, symmetric, {', '.join(_DIMENSIONS)})"
    )


def add_constraints(sketch: str, items: list[dict[str, Any]], document: str | None = None) -> ToolResult:
    """Add constraints; dimension ``value`` may be a number or a parameter name."""
    if not items:
        raise validation("Keine Constraints angegeben")

    def action(doc: Any, sk: Any, result: ToolResult) -> None:
        builder = SketchBuilder(sk, "")
        result.data["constraints"] = [_add_constraint_item(builder, doc, item) for item in items]

    return sketch_edit(sketch, document, "Constraints", action)
