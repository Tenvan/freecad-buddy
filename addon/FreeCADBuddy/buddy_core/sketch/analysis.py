"""Sketch analysis: degrees of freedom, solver problems, closed profiles and style lint."""

from __future__ import annotations

from typing import Any

from buddy_core.sketch import external

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
                {
                    "severity": "error",
                    "constraint": index,
                    "issue": "Block constraint instead of real dimensions",
                }
            )
        if constraint.Type in DIMENSIONAL and constraint.Driving:
            if not constraint.Name:
                issues.append(
                    {"severity": "warning", "constraint": index, "issue": "Dimension without a name"}
                )
            elif f"Constraints.{constraint.Name}" not in expressions:
                issues.append(
                    {
                        "severity": "info",
                        "constraint": index,
                        "name": constraint.Name,
                        "issue": "Dimension not bound to a parameter",
                    }
                )
    for entry in external.describe(sketch):
        stable = entry["stable"] or entry["source_name"] in {o.Name for o in _origin_objects(sketch)}
        where = f"{entry['ref']} from '{entry['source']}' ({entry['element']})"
        issues.append(
            {"severity": "info", "ref": entry["ref"], "issue": f"External geometry {where}"}
            if stable
            else {
                "severity": "warning",
                "ref": entry["ref"],
                "issue": f"External geometry {where} is prone to the topological naming problem",
            }
        )
    for broken in external.dangling(sketch):
        issues.append(
            {
                "severity": "error",
                "constraint": broken["constraint"],
                "ref": broken["ref"],
                "issue": f"Constraint references missing external geometry {broken['ref']} (source deleted?)",
            }
        )
    return issues


def _origin_objects(sketch: Any) -> list[Any]:
    return [obj for obj, _ in sketch.ExternalGeometry if obj.TypeId.startswith(_ORIGIN_TYPES)]


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
        "external": [
            {key: entry[key] for key in ("ref", "source", "element", "defining")}
            for entry in external.describe(sketch)
        ],
        "constraint_count": sketch.ConstraintCount,
        "closed_wires": closed,
        "open_wires": open_,
        "lint": lint(sketch),
    }


def problems(report: dict[str, Any]) -> list[str]:
    """Blocking solver problems (conflicts, redundancies, malformed) as readable text."""
    found = []
    for key, text in (
        ("conflicting", "conflicting"),
        ("redundant", "redundant"),
        ("malformed", "malformed"),
    ):
        if report[key]:
            found.append(f"{text} Constraints {report[key]}")
    if not report["solver_ok"] and not found:
        found.append("The solver could not solve the sketch")
    return found
