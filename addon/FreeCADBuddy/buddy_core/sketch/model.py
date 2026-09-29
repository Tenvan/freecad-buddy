"""Create sketches on stable references and run sketch edits as checked transactions."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import FreeCAD

from buddy_core import naming, values
from buddy_core.body import body_of, origin_feature, resolve_body
from buddy_core.documents import resolve_document, resolve_object
from buddy_core.errors import SKETCH_INVALID, CoreError, validation
from buddy_core.result import ToolResult, describe
from buddy_core.sketch import analysis
from buddy_core.transaction import transaction

ORIGIN_PLANES = ("XY", "XZ", "YZ")


def resolve_sketch(doc: Any, ref: str) -> Any:
    return resolve_object(doc, ref, "Sketcher::SketchObject")


def create_sketch(
    plane: str = "XY",
    purpose: str | None = None,
    offset: values.ValueSpec = 0,
    body: str | None = None,
    reversed: bool = False,
    allow_face_attachment: bool = False,
    document: str | None = None,
) -> ToolResult:
    """Sketch on an origin plane (``XY``/``XZ``/``YZ``), a datum plane (label) or a body face.

    Face attachment (``face:<selector>``) is opt-in because face references are prone to the
    topological naming problem; origin and datum planes are stable.
    """
    doc = resolve_document(document)
    target_body = resolve_body(doc, body)
    result = ToolResult()
    with transaction(doc, f"Create sketch: {purpose or plane}"):
        sketch = target_body.newObject("Sketcher::SketchObject", "Sketch")
        sketch.Label = naming.make_label(doc, "Sketch", purpose or plane)
        support, face_warning, map_mode = plane_support(doc, target_body, plane, allow_face_attachment)
        sketch.AttachmentSupport = [support]
        sketch.MapMode = map_mode
        sketch.MapReversed = reversed
        offset_value = values.resolve(doc, offset, "offset")
        sketch.AttachmentOffset = FreeCAD.Placement(
            FreeCAD.Vector(0, 0, offset_value.number), FreeCAD.Rotation()
        )
        if offset_value.expression:
            sketch.setExpression(".AttachmentOffset.Base.z", offset_value.expression)
        if face_warning:
            result.warnings.append(face_warning)
        result.add_created(sketch)
    result.data["sketch"] = describe(sketch)
    result.hints.append("Next step: add_profile (e.g. rectangle, circle, slot) into this sketch.")
    return result


def plane_support(
    doc: Any, body: Any, plane: str, allow_face: bool
) -> tuple[tuple[Any, str], str | None, str]:
    """Resolve ``plane`` to (attachment support, warning, map mode) for sketches and primitives:
    origin plane, datum plane, LCS (its XY plane) or, opt-in, a body face."""
    if plane.upper() in ORIGIN_PLANES:
        return (origin_feature(body, plane.upper()), ""), None, "FlatFace"
    if plane.lower().startswith("face:"):
        if not allow_face:
            raise validation(
                "Sketches on solid faces are prone to TNP. Use an origin plane or datum_plane "
                "or set allow_face_attachment=true."
            )
        from buddy_core import select

        tip = body.Tip
        if tip is None:
            raise validation("The body has no geometry for a face reference yet")
        faces = select.resolve(tip.Shape, plane, single=True)
        return (
            (tip, faces[0]),
            f"Sketch is attached to {tip.Label}.{faces[0]} - the reference may jump on topology changes.",
            "FlatFace",
        )
    datum = resolve_object(doc, plane)
    if datum.TypeId == "PartDesign::CoordinateSystem":
        return (datum, ""), None, "ObjectXY"
    if datum.TypeId not in ("PartDesign::Plane", "App::Plane"):
        raise validation(f"'{plane}' is not a plane (allowed: XY, XZ, YZ, datum plane, LCS, face:<selector>)")
    return (datum, ""), None, "FlatFace"


@contextmanager
def checked_edit(doc: Any, sketch: Any, label: str, result: ToolResult) -> Iterator[None]:
    """Transaction around a sketch edit that rolls back on conflicts/redundancies."""
    with transaction(doc, label):
        yield
        doc.recompute()
        report = analysis.analyze(sketch)
        blocking = analysis.problems(report)
        if blocking:
            raise CoreError(
                SKETCH_INVALID,
                f"Sketch '{sketch.Label}' invalid: {'; '.join(blocking)}",
                {"sketch": report},
            )
        result.sketch = report
        result.add_modified(sketch)
        if report["dof"] > 0:
            result.warnings.append(
                f"Sketch still has {report['dof']} degree(s) of freedom - use fully_constrain_sketch or add dimensions."
            )
        if report["open_wires"]:
            result.warnings.append(
                f"{report['open_wires']} open wire(s): right as a sweep path, "
                "unsuitable as a pad/pocket profile."
            )


def sketch_edit(
    sketch_ref: str, document: str | None, label: str, action: Callable[[Any, Any, ToolResult], None]
) -> ToolResult:
    doc = resolve_document(document)
    sketch = resolve_sketch(doc, sketch_ref)
    body_of(sketch)
    result = ToolResult()
    with checked_edit(doc, sketch, f"{label}: {sketch.Label}", result):
        action(doc, sketch, result)
    return result


def analyze_sketch(sketch: str, document: str | None = None) -> dict[str, Any]:
    doc = resolve_document(document)
    return analysis.analyze(resolve_sketch(doc, sketch))
