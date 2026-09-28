"""External metric threads on vertical cylinders as a native PartDesign feature (SubtractiveHelix).

The groove profile is the ISO 60° thread form: a V from the major diameter down to the thread depth
h3 = 0.6134·P, drawn in a sketch whose plane contains the cylinder axis. A construction line in that
sketch is the helix axis. Everything is fully constrained and bound to the given values/parameters,
so a changed diameter, pitch or position rebuilds the thread.
"""

from __future__ import annotations

import math
from typing import Any

import FreeCAD

from buddy_core import display, naming, values
from buddy_core.body import origin_feature, resolve_body
from buddy_core.documents import resolve_document
from buddy_core.errors import validation
from buddy_core.result import ToolResult, describe
from buddy_core.sketch.analysis import analyze
from buddy_core.sketch.builder import SketchBuilder
from buddy_core.transaction import transaction

DEPTH_FACTOR = 0.6134  # h3 / P, ISO 68-1 external thread
CLEARANCE_FACTOR = 0.1  # profile starts this far (x P) outside the major diameter for a clean cut
TAN30 = math.tan(math.radians(30))
START, END = 1, 2


def _spec(value: values.ValueSpec) -> str:
    return f"({value})"


def _signed(sign: float, spec: values.ValueSpec) -> str:
    return _spec(spec) if sign > 0 else f"-{_spec(spec)}"


def _plane_signs(plane: Any) -> tuple[float, float, float]:
    """Signs mapping global Y (plane normal), X (sketch x) and Z (sketch y) onto the XZ origin plane."""
    rotation = plane.Placement.Rotation
    normal, local_x, local_y = (
        rotation.multVec(FreeCAD.Vector(*axis)) for axis in ((0, 0, 1), (1, 0, 0), (0, 1, 0))
    )
    if abs(abs(normal.y) - 1) > 1e-6 or abs(abs(local_x.x) - 1) > 1e-6 or abs(abs(local_y.z) - 1) > 1e-6:
        raise validation("Unexpected orientation of the XZ origin plane - cannot place the thread profile")
    return math.copysign(1, normal.y), math.copysign(1, local_x.x), math.copysign(1, local_y.z)


def thread(
    center: list[values.ValueSpec],
    diameter: values.ValueSpec,
    pitch: values.ValueSpec,
    length: values.ValueSpec,
    z_start: values.ValueSpec = 0,
    left_handed: bool = False,
    body: str | None = None,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Cut an external thread into the vertical cylinder at ``center`` [x, y] from ``z_start`` upwards."""
    if len(center) != 2:
        raise validation("center needs [x, y] of the cylinder axis")
    doc = resolve_document(document)
    target = resolve_body(doc, body)
    cx, cy = center
    d, p = values.resolve(doc, diameter, "diameter"), values.resolve(doc, pitch, "pitch")
    if d.number <= 0 or p.number <= 0 or p.number >= d.number / 2:
        raise validation("diameter and pitch must be positive and pitch smaller than the radius")
    plane = origin_feature(target, "XZ")
    s_normal, s_x, s_z = _plane_signs(plane)

    def of_pitch(factor: float) -> str:
        # a plain number keeps its unit only if it stands alone next to a length (values unit rule)
        return f"{factor * p.number:.6g}" if p.expression is None else f"{factor:.6g} * {_spec(pitch)}"

    outer = values.resolve(doc, f"{_spec(diameter)} / 2 + {of_pitch(CLEARANCE_FACTOR)}", "radius")
    inner = values.resolve(doc, f"{_spec(diameter)} / 2 - {of_pitch(DEPTH_FACTOR)}", "radius")
    half = of_pitch((DEPTH_FACTOR + CLEARANCE_FACTOR) * TAN30)
    half_width, width = values.resolve(doc, half, "width"), values.resolve(doc, f"2 * {half}", "width")
    offset = values.resolve(doc, _signed(s_normal, cy), "offset")
    axis_x = values.resolve(doc, _signed(s_x, cx), "x")
    axis_y = values.resolve(doc, _signed(s_z, z_start), "z_start")
    height = values.resolve(doc, length, "length")
    label = purpose or f"M{d.number:g}"
    result = ToolResult()
    with transaction(doc, f"Thread: {label}"):
        sketch = target.newObject("Sketcher::SketchObject", "Sketch")
        sketch.Label = naming.make_label(doc, "Sketch", f"{label}_ThreadProfile")
        sketch.AttachmentSupport = [(plane, "")]
        sketch.MapMode = "FlatFace"
        sketch.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(0, 0, offset.number), FreeCAD.Rotation())
        if offset.expression:
            sketch.setExpression(".AttachmentOffset.Base.z", offset.expression)
        b = SketchBuilder(sketch, naming.sanitize(label))
        u, v, up = axis_x.number, axis_y.number, s_z  # sketch y grows with global Z when s_z > 0
        axis = b.line((u, v), (u, v + up * height.number), construction=True)
        b.con("Vertical", axis)
        b.anchor(axis, START, (axis_x, axis_y), "Axis")
        b.dim("Distance", axis, value=height, what="Length")
        a = (u + outer.number, v - half_width.number)
        top = (u + outer.number, v + half_width.number)
        apex = (u + inner.number, v)
        flank = b.line(a, top)
        upper = b.line(top, apex)
        lower = b.line(apex, a)
        b.con("Coincident", flank, END, upper, START)
        b.con("Coincident", upper, END, lower, START)
        b.con("Coincident", lower, END, flank, START)
        b.con("Vertical", flank)
        b.con("Horizontal", axis, START, upper, END)
        b.dim("DistanceX", axis, START, flank, START, value=outer, what="Outer")
        b.dim("DistanceX", axis, START, upper, END, value=inner, what="Core")
        b.dim("DistanceY", flank, START, upper, END, value=half_width, what="HalfWidth")
        b.dim("Distance", flank, value=width, what="Width")
        sketch.Visibility = False
        helix = target.newObject("PartDesign::SubtractiveHelix", "Thread")
        helix.Label = naming.make_label(doc, "Thread", label)
        helix.Profile = sketch
        helix.ReferenceAxis = (sketch, ["Axis0"])
        helix.Mode = 0  # pitch - height - angle
        values.apply(helix, "Pitch", p)
        values.apply(helix, "Height", height)
        helix.Angle = 0
        helix.LeftHanded = left_handed
        display.apply_selection_style(helix)
        target.Tip = helix
        doc.recompute()
        report = analyze(sketch)
        if report["dof"] != 0:
            raise validation(f"Thread profile is not fully constrained (DoF {report['dof']})")
        result.add_created(sketch)
        result.add_created(helix)
    result.data["feature"] = describe(helix)
    result.data["sketch"] = describe(sketch)
    result.data["thread"] = {
        "major_diameter": d.number, "pitch": p.number, "core_diameter": round(2 * inner.number, 4),
        "length": height.number, "left_handed": left_handed,
    }  # fmt: skip
    shape = helix.Shape
    result.data["volume"] = shape.Volume if shape.Solids else 0.0
    result.hints.append("Several identical threads: pattern(features=[<thread>], kind='grid'|'linear').")
    return result
