"""Fully-constrain assistant: add obvious relations first, dimension only what remains.

Never uses Block/Lock; remaining freedom is removed with named X/Y dimensions from the
origin, which the lint reports as "not bound to a parameter" so they stay visible.
"""

from __future__ import annotations

from typing import Any

import FreeCAD

from buddy_core.documents import resolve_document
from buddy_core.result import ToolResult
from buddy_core.sketch import analysis
from buddy_core.sketch.builder import SketchBuilder
from buddy_core.sketch.model import resolve_sketch, sketch_edit
from buddy_core.sketch.refs import CENTER, END, START, format_ref
from buddy_core.values import Value

PRECISION = 1e-6


def _points(geometry: Any) -> list[tuple[int, Any]]:
    kind = type(geometry).__name__
    if kind == "LineSegment":
        return [(START, geometry.StartPoint), (END, geometry.EndPoint)]
    if kind == "ArcOfCircle":
        return [(CENTER, geometry.Center), (START, geometry.StartPoint), (END, geometry.EndPoint)]
    if kind == "Circle":
        return [(CENTER, geometry.Center)]
    if kind == "Point":
        return [(START, FreeCAD.Vector(geometry.X, geometry.Y, geometry.Z))]
    return []


def _free_points(sk: Any) -> list[tuple[int, int, Any]]:
    """Points of non-construction and construction geometry that the solver still moves."""
    sk.solve()
    dependent = {(geo, pos) for geo, pos in sk.getGeometryWithDependentParameters()}
    return [
        (geo_id, pos, point)
        for geo_id, geometry in enumerate(sk.Geometry)
        for pos, point in _points(geometry)
        if (geo_id, pos) not in dependent
    ]


def _try_dimension(builder: SketchBuilder, kind: str, geo_id: int, pos: int, coordinate: float) -> bool:
    """Keep a coordinate dimension only if it removes freedom without redundancy."""
    sk = builder.sketch
    dof_before = sk.DoF
    index = builder.dim(
        kind, -1, START, geo_id, pos, value=Value(coordinate), what=f"G{geo_id}P{pos}{kind[-1]}"
    )
    sk.solve()
    if sk.DoF < dof_before and not sk.RedundantConstraints and not sk.ConflictingConstraints:
        return True
    sk.delConstraint(index)
    builder.constraints.remove(index)
    sk.solve()
    return False


def _obvious_relations(sk: Any) -> int:
    added = 0
    if sk.detectMissingPointOnPointConstraints(PRECISION) > 0:
        before = sk.ConstraintCount
        sk.makeMissingPointOnPointCoincident()
        added += sk.ConstraintCount - before
    if sk.detectMissingVerticalHorizontalConstraints() > 0:
        before = sk.ConstraintCount
        sk.makeMissingVerticalHorizontal()
        added += sk.ConstraintCount - before
    return added


def fully_constrain_sketch(sketch: str, apply: bool = False, document: str | None = None) -> ToolResult:
    """``apply=False`` only reports suggestions; ``apply=True`` adds them as one undo step."""
    doc = resolve_document(document)
    sk = resolve_sketch(doc, sketch)
    report = analysis.analyze(sk)
    if not apply:
        result = ToolResult(sketch=report)
        result.data["free_points"] = [
            {"ref": format_ref(g, p), "at": [v.x, v.y]} for g, p, v in _free_points(sk)
        ]
        if report["dof"] == 0:
            result.hints.append("Skizze ist bereits vollständig bestimmt.")
        else:
            result.hints.append(
                "Mit apply=true werden fehlende Koinzidenzen/H/V ergänzt und Restfreiheit über "
                "benannte X/Y-Maße vom Ursprung gebunden. Besser: gezielte Maße mit add_constraints."
            )
        return result

    def action(doc_: Any, sk_: Any, result: ToolResult) -> None:
        builder = SketchBuilder(sk_, "Auto")
        relations = _obvious_relations(sk_)
        sk_.solve()
        dimensions = 0
        for geo_id, geometry in enumerate(sk_.Geometry):
            for pos, point in _points(geometry):
                for kind, coordinate in (("DistanceX", point.x), ("DistanceY", point.y)):
                    if sk_.DoF == 0:
                        break
                    if _try_dimension(builder, kind, geo_id, pos, coordinate):
                        dimensions += 1
        result.data["added_relations"] = relations
        result.data["added_dimensions"] = dimensions
        if dimensions:
            result.hints.append("Automatisch gesetzte Maße (Auto_*) prüfen und ggf. an Parameter binden.")

    return sketch_edit(sketch, document, "Skizze vollständig bestimmen", action)
