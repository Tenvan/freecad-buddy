"""Semantic selectors for faces and edges instead of fragile names like ``Edge12``.

Grammar: ``<kind>:<filter>[,<filter>...]`` with kind ``face``/``faces``/``edge``/``edges``
(singular = exactly one match). Filters are AND-combined:

- ``top`` ``bottom`` ``front`` ``back`` ``left`` ``right`` – outermost planar faces in that
  direction (for edges: the edges of those faces)
- ``normal=+Z`` (any axis ±X/±Y/±Z), ``planar``, ``cylindrical``
- ``vertical`` (parallel to Z), ``horizontal`` (perpendicular to Z), ``parallel=X|Y|Z``,
  ``line``, ``circular``, ``radius=<mm>``
- ``at_max_z`` ``at_min_z`` – elements lying completely at the top/bottom height
- ``x=<v>`` ``y=<v>`` ``z=<v>`` – elements lying completely at that coordinate; ``v`` may be a
  number, a parameter name or an expression over parameters (``z=Thickness``)
- ``of_feature=<label>`` – elements created by that feature (not present before it)
- ``all``

Dress-up features remember their selector (property ``BuddySelector``) and are re-resolved
after parameter changes, so the intent survives topology changes.
"""

from __future__ import annotations

import math
from typing import Any

import FreeCAD

from buddy_core.errors import AMBIGUOUS, CoreError, not_found, validation

SELECTOR_PROPERTY = "BuddySelector"
TOL = 1e-6
_DIRECTIONS = {
    "top": FreeCAD.Vector(0, 0, 1),
    "bottom": FreeCAD.Vector(0, 0, -1),
    "right": FreeCAD.Vector(1, 0, 0),
    "left": FreeCAD.Vector(-1, 0, 0),
    "back": FreeCAD.Vector(0, 1, 0),
    "front": FreeCAD.Vector(0, -1, 0),
}
_AXES = {"X": FreeCAD.Vector(1, 0, 0), "Y": FreeCAD.Vector(0, 1, 0), "Z": FreeCAD.Vector(0, 0, 1)}


def _axis(text: str) -> FreeCAD.Vector:
    sign = -1 if text.startswith("-") else 1
    key = text.lstrip("+-").upper()
    if key not in _AXES:
        raise validation(f"Unknown axis '{text}' (allowed: ±X, ±Y, ±Z)")
    return _AXES[key] * sign


def face_normal(face: Any) -> FreeCAD.Vector:
    u0, u1, v0, v1 = face.ParameterRange
    normal = face.normalAt((u0 + u1) / 2, (v0 + v1) / 2)
    return normal


def _is_planar(face: Any) -> bool:
    return face.Surface.__class__.__name__ == "Plane"


def _parallel(a: FreeCAD.Vector, b: FreeCAD.Vector) -> bool:
    return abs(abs(a.normalize().dot(b.normalize())) - 1) < 1e-6


def _same_direction(a: FreeCAD.Vector, b: FreeCAD.Vector) -> bool:
    return a.normalize().dot(b.normalize()) > 1 - 1e-6


def _extreme_faces(shape: Any, direction: FreeCAD.Vector) -> list[int]:
    candidates = [
        (i, face)
        for i, face in enumerate(shape.Faces)
        if _is_planar(face) and _same_direction(face_normal(face), direction)
    ]
    if not candidates:
        return []
    heights = {i: face.CenterOfMass.dot(direction) for i, face in candidates}
    best = max(heights.values())
    return [i for i, h in heights.items() if abs(h - best) < 1e-6 * max(1.0, abs(best))]


def _edge_is_line(edge: Any) -> bool:
    return edge.Curve.__class__.__name__ in ("Line", "LineSegment")


def _edge_is_circle(edge: Any) -> bool:
    return edge.Curve.__class__.__name__ == "Circle"


def _edge_direction(edge: Any) -> FreeCAD.Vector:
    return edge.Vertexes[-1].Point - edge.Vertexes[0].Point


def _signature(element: Any) -> tuple[Any, ...]:
    center = element.CenterOfMass
    size = element.Area if hasattr(element, "Area") and element.ShapeType == "Face" else element.Length
    return (element.ShapeType, round(size, 4), round(center.x, 4), round(center.y, 4), round(center.z, 4))


def _new_elements(doc: Any, feature_ref: str, kind: str) -> set[tuple[Any, ...]]:
    from buddy_core.documents import resolve_object

    feature = resolve_object(doc, feature_ref)
    base = getattr(feature, "BaseFeature", None)
    elements = feature.Shape.Faces if kind == "face" else feature.Shape.Edges
    before = set()
    if base is not None and not base.Shape.isNull():
        before = {_signature(e) for e in (base.Shape.Faces if kind == "face" else base.Shape.Edges)}
    return {_signature(e) for e in elements} - before


_COORDINATE = ("x=", "y=", "z=")


def _coordinate(token: str, doc: Any | None) -> tuple[str, float]:
    axis, _, raw = token.partition("=")
    try:
        return axis, float(raw)
    except ValueError:
        if doc is None:
            raise validation(f"Parameter '{raw}' in the selector needs a document") from None
        from buddy_core import values

        return axis, values.number(doc, raw, token)


def _at_coordinate(elements: list[Any], token: str, doc: Any | None) -> set[int]:
    """Elements lying completely at ``x|y|z = value`` (number or parameter/expression)."""
    axis, value = _coordinate(token, doc)
    low, high = {"x": ("XMin", "XMax"), "y": ("YMin", "YMax"), "z": ("ZMin", "ZMax")}[axis]
    return {
        i
        for i, e in enumerate(elements)
        if abs(getattr(e.BoundBox, low) - value) < 1e-6 and abs(getattr(e.BoundBox, high) - value) < 1e-6
    }


def _face_filter(shape: Any, token: str, doc: Any | None) -> set[int]:
    faces = shape.Faces
    everything = set(range(len(faces)))
    if token == "all":
        return everything
    if token == "vertical":  # side walls: planar faces with a horizontal normal
        return {i for i, f in enumerate(faces) if _is_planar(f) and abs(face_normal(f).z) < 1e-6}
    if token in _DIRECTIONS:
        return set(_extreme_faces(shape, _DIRECTIONS[token]))
    if token.startswith("normal="):
        direction = _axis(token.split("=", 1)[1])
        return {
            i for i, f in enumerate(faces) if _is_planar(f) and _same_direction(face_normal(f), direction)
        }
    if token == "planar":
        return {i for i, f in enumerate(faces) if _is_planar(f)}
    if token == "cylindrical":
        return {i for i, f in enumerate(faces) if f.Surface.__class__.__name__ == "Cylinder"}
    if token.startswith("radius="):
        radius = float(token.split("=", 1)[1])
        return {
            i
            for i, f in enumerate(faces)
            if f.Surface.__class__.__name__ == "Cylinder" and abs(f.Surface.Radius - radius) < 1e-3
        }
    if token in ("at_max_z", "at_min_z"):
        z = shape.BoundBox.ZMax if token == "at_max_z" else shape.BoundBox.ZMin
        return {
            i
            for i, f in enumerate(faces)
            if abs(f.BoundBox.ZMax - z) < TOL and abs(f.BoundBox.ZMin - z) < TOL
        }
    if token.startswith("of_feature="):
        if doc is None:
            raise validation("of_feature needs a document")
        created = _new_elements(doc, token.split("=", 1)[1], "face")
        return {i for i, f in enumerate(faces) if _signature(f) in created}
    if token.startswith(_COORDINATE):
        return _at_coordinate(list(faces), token, doc)
    raise validation(f"Unknown face filter '{token}'")


def _edge_filter(shape: Any, token: str, doc: Any | None) -> set[int]:
    edges = shape.Edges
    everything = set(range(len(edges)))
    if token == "all":
        return everything
    if token in _DIRECTIONS:
        face_ids = _extreme_faces(shape, _DIRECTIONS[token])
        members = {_signature(e) for i in face_ids for e in shape.Faces[i].Edges}
        return {i for i, e in enumerate(edges) if _signature(e) in members}
    if token == "vertical":
        return {
            i for i, e in enumerate(edges) if _edge_is_line(e) and _parallel(_edge_direction(e), _AXES["Z"])
        }
    if token == "horizontal":
        return {
            i
            for i, e in enumerate(edges)
            if _edge_is_line(e) and abs(_edge_direction(e).normalize().dot(_AXES["Z"])) < 1e-6
        }
    if token.startswith("parallel="):
        axis = _axis(token.split("=", 1)[1])
        return {i for i, e in enumerate(edges) if _edge_is_line(e) and _parallel(_edge_direction(e), axis)}
    if token == "line":
        return {i for i, e in enumerate(edges) if _edge_is_line(e)}
    if token == "circular":
        return {i for i, e in enumerate(edges) if _edge_is_circle(e)}
    if token.startswith("radius="):
        radius = float(token.split("=", 1)[1])
        return {i for i, e in enumerate(edges) if _edge_is_circle(e) and abs(e.Curve.Radius - radius) < 1e-3}
    if token in ("at_max_z", "at_min_z"):
        z = shape.BoundBox.ZMax if token == "at_max_z" else shape.BoundBox.ZMin
        return {
            i
            for i, e in enumerate(edges)
            if abs(e.BoundBox.ZMax - z) < TOL and abs(e.BoundBox.ZMin - z) < TOL
        }
    if token.startswith("of_feature="):
        if doc is None:
            raise validation("of_feature needs a document")
        created = _new_elements(doc, token.split("=", 1)[1], "edge")
        return {i for i, e in enumerate(edges) if _signature(e) in created}
    if token.startswith(_COORDINATE):
        return _at_coordinate(list(edges), token, doc)
    raise validation(f"Unknown edge filter '{token}'")


def parse(selector: str) -> tuple[str, bool, list[str]]:
    if ":" not in selector:
        raise validation(f"Selector '{selector}' does not have the form <kind>:<filter>, e.g. 'edges:top'")
    kind, _, rest = selector.partition(":")
    kind = kind.strip().lower()
    if kind not in ("face", "faces", "edge", "edges"):
        raise validation(f"Unknown selector kind '{kind}' (allowed: face, faces, edge, edges)")
    tokens = [t.strip() for t in rest.split(",") if t.strip()]
    if not tokens:
        raise validation("Selektor ohne Filter")
    return kind.rstrip("s"), not kind.endswith("s"), tokens


def resolve(shape: Any, selector: str, single: bool | None = None, doc: Any | None = None) -> list[str]:
    """Return sub-element names (``Face3``, ``Edge7``) matching the selector on ``shape``."""
    kind, singular, tokens = parse(selector)
    single = singular if single is None else single
    matcher = _face_filter if kind == "face" else _edge_filter
    elements = shape.Faces if kind == "face" else shape.Edges
    matches = set(range(len(elements)))
    for token in tokens:
        matches &= matcher(shape, token, doc)
    names = [f"{'Face' if kind == 'face' else 'Edge'}{i + 1}" for i in sorted(matches)]
    if not names:
        raise not_found(f"Selektor '{selector}' trifft nichts", selector=selector)
    if single and len(names) > 1:
        raise CoreError(
            AMBIGUOUS, f"Selektor '{selector}' trifft {len(names)} Elemente", {"candidates": names}
        )
    return names


def describe_matches(shape: Any, names: list[str]) -> list[dict[str, Any]]:
    described = []
    for name in names:
        element = shape.getElement(name)
        entry: dict[str, Any] = {"name": name, "center": list(element.CenterOfMass)}
        if element.ShapeType == "Face":
            entry["area"] = element.Area
            normal = face_normal(element)
            entry["normal"] = [round(c, 6) for c in normal]
        else:
            entry["length"] = element.Length
            if _edge_is_circle(element):
                entry["radius"] = element.Curve.Radius
        described.append(entry)
    return described


def select_geometry(
    selector: str, target: str | None = None, body: str | None = None, document: str | None = None
) -> dict[str, Any]:
    """Preview what a selector matches (on a feature, or on the body's tip)."""
    from buddy_core.body import resolve_body
    from buddy_core.documents import resolve_document, resolve_object

    doc = resolve_document(document)
    obj = resolve_object(doc, target) if target else resolve_body(doc, body).Tip
    if obj is None or obj.Shape.isNull():
        raise not_found("No geometry to select from")
    names = resolve(obj.Shape, selector, single=False, doc=doc)
    return {"target": obj.Label, "selector": selector, "matches": describe_matches(obj.Shape, names)}


def remember(feature: Any, selector: str) -> None:
    if SELECTOR_PROPERTY not in feature.PropertiesList:
        feature.addProperty("App::PropertyString", SELECTOR_PROPERTY, "FreeCADBuddy", "Semantischer Selektor")
    setattr(feature, SELECTOR_PROPERTY, selector)


def refresh_references(doc: Any) -> list[Any]:
    """Re-resolve remembered selectors after model changes; returns features that changed."""
    changed = []
    for feature in doc.Objects:
        if SELECTOR_PROPERTY not in feature.PropertiesList or not getattr(feature, SELECTOR_PROPERTY):
            continue
        base_ref = feature.Base
        base = base_ref[0] if base_ref else feature.BaseFeature
        if base is None or base.Shape.isNull():
            continue
        try:
            names = resolve(base.Shape, getattr(feature, SELECTOR_PROPERTY), single=False, doc=doc)
        except CoreError:
            continue
        current = list(base_ref[1]) if base_ref else []
        if sorted(current) != sorted(names):
            feature.Base = (base, names)
            feature.recompute()
            changed.append(feature)
    return changed


def angle_between_deg(a: FreeCAD.Vector, b: FreeCAD.Vector) -> float:
    return math.degrees(a.getAngle(b))
