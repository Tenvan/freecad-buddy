"""Sketch analysis: degrees of freedom, solver problems, closed profiles and style lint."""

from __future__ import annotations

from typing import Any

DIMENSIONAL = {"Distance", "DistanceX", "DistanceY", "Radius", "Diameter", "Angle"}
_ORIGIN_TYPES = ("App::Origin", "App::Line", "App::Plane", "PartDesign::Plane", "PartDesign::Line")


def _wires(sketch: Any) -> tuple[int, int]:
    shape = sketch.Shape
    if shape.isNull():
        return 0, 0
    closed = sum(1 for wire in shape.Wires if wire.isClosed())
    return closed, len(shape.Wires) - closed


def lint(sketch: Any) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    expressions = {path.lstrip(".") for path, _ in sketch.ExpressionEngine}
    for index, constraint in enumerate(sketch.Constraints):
        if constraint.Type == "Block":
            issues.append(
                {"severity": "error", "constraint": index, "issue": "Block-Constraint statt echter Maße"}
            )
        if constraint.Type in DIMENSIONAL and constraint.Driving:
            if not constraint.Name:
                issues.append({"severity": "warning", "constraint": index, "issue": "Maß ohne Namen"})
            elif f"Constraints.{constraint.Name}" not in expressions:
                issues.append(
                    {
                        "severity": "info",
                        "constraint": index,
                        "name": constraint.Name,
                        "issue": "Maß nicht an einen Parameter gebunden",
                    }
                )
    for obj, subs in sketch.ExternalGeometry:
        if not obj.TypeId.startswith(_ORIGIN_TYPES):
            issues.append(
                {
                    "severity": "warning",
                    "issue": f"Externe Geometrie aus '{obj.Label}' ({', '.join(subs)}) – anfällig für TNP",
                }
            )
    return issues


def analyze(sketch: Any) -> dict[str, Any]:
    solver_status = sketch.solve()
    closed, open_ = _wires(sketch)
    return {
        "sketch": sketch.Label,
        "dof": sketch.DoF,
        "fully_constrained": bool(sketch.FullyConstrained),
        "solver_ok": solver_status == 0,
        "conflicting": list(sketch.ConflictingConstraints),
        "redundant": list(sketch.RedundantConstraints),
        "partially_redundant": list(sketch.PartiallyRedundantConstraints),
        "malformed": list(sketch.MalformedConstraints),
        "geometry_count": sketch.GeometryCount,
        "constraint_count": sketch.ConstraintCount,
        "closed_wires": closed,
        "open_wires": open_,
        "lint": lint(sketch),
    }


def problems(report: dict[str, Any]) -> list[str]:
    """Blocking solver problems (conflicts, redundancies, malformed) as readable text."""
    found = []
    for key, text in (
        ("conflicting", "widersprüchliche"),
        ("redundant", "redundante"),
        ("malformed", "fehlerhafte"),
    ):
        if report[key]:
            found.append(f"{text} Constraints {report[key]}")
    if not report["solver_ok"] and not found:
        found.append("Solver konnte die Skizze nicht lösen")
    return found
