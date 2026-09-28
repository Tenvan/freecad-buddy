"""Low-level helper that adds geometry and (named, parameter-bound) constraints to a sketch."""

from __future__ import annotations

import math
from typing import Any

import FreeCAD
import Part
import Sketcher

from buddy_core.values import Value

Point = tuple[float, float]


def vec(point: Point) -> Any:
    return FreeCAD.Vector(point[0], point[1], 0)


class SketchBuilder:
    def __init__(self, sketch: Any, prefix: str) -> None:
        self.sketch = sketch
        self.prefix = prefix
        self.geometry: list[int] = []
        self.constraints: list[int] = []

    # geometry ---------------------------------------------------------------------------
    def _add(self, geometry: Any, construction: bool) -> int:
        geo_id = self.sketch.addGeometry(geometry, construction)
        self.geometry.append(geo_id)
        return geo_id

    def line(self, start: Point, end: Point, construction: bool = False) -> int:
        return self._add(Part.LineSegment(vec(start), vec(end)), construction)

    def circle(self, center: Point, radius: float, construction: bool = False) -> int:
        return self._add(Part.Circle(vec(center), FreeCAD.Vector(0, 0, 1), radius), construction)

    def arc(
        self, center: Point, radius: float, start_deg: float, end_deg: float, construction: bool = False
    ) -> int:
        circle = Part.Circle(vec(center), FreeCAD.Vector(0, 0, 1), radius)
        return self._add(
            Part.ArcOfCircle(circle, math.radians(start_deg), math.radians(end_deg)), construction
        )

    def point(self, at: Point) -> int:
        return self._add(Part.Point(vec(at)), False)

    # constraints ------------------------------------------------------------------------
    def con(self, kind: str, *args: Any) -> int:
        index = self.sketch.addConstraint(Sketcher.Constraint(kind, *args))
        self.constraints.append(index)
        return index

    def unique_name(self, what: str) -> str:
        existing = {c.Name for c in self.sketch.Constraints if c.Name}
        base = f"{self.prefix}_{what}" if self.prefix else what
        name, index = base, 2
        while name in existing:
            name, index = f"{base}_{index}", index + 1
        return name

    def dim(self, kind: str, *refs: Any, value: Value, what: str, angle: bool = False) -> int:
        """Driving dimension with a readable name, bound to its parameter expression if any."""
        number = math.radians(value.number) if angle else value.number
        index = self.con(kind, *refs, number)
        name = self.unique_name(what)
        self.sketch.renameConstraint(index, name)
        if value.expression:
            self.sketch.setExpression(f"Constraints.{name}", value.expression)
        return index

    def anchor(self, geo_id: int, pos_id: int, at: tuple[Value, Value], what: str) -> None:
        """Pin a point: coincident with the origin if at (0, 0), else X/Y distances from it."""
        x, y = at
        x_zero = x.number == 0 and not x.expression
        y_zero = y.number == 0 and not y.expression
        if x_zero and y_zero:
            self.con("Coincident", -1, 1, geo_id, pos_id)
            return
        if x_zero:
            self.con("PointOnObject", geo_id, pos_id, -2)  # on the vertical axis
        else:
            self.dim("DistanceX", -1, 1, geo_id, pos_id, value=x, what=f"{what}X")
        if y_zero:
            self.con("PointOnObject", geo_id, pos_id, -1)  # on the horizontal axis
        else:
            self.dim("DistanceY", -1, 1, geo_id, pos_id, value=y, what=f"{what}Y")
