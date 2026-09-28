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
    with transaction(doc, f"Skizze anlegen: {purpose or plane}"):
        sketch = target_body.newObject("Sketcher::SketchObject", "Sketch")
        sketch.Label = naming.make_label(doc, "Sketch", purpose or plane)
        support, face_warning = _support(doc, target_body, plane, allow_face_attachment)
        sketch.AttachmentSupport = [support]
        sketch.MapMode = "FlatFace"
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
    result.hints.append("Nächster Schritt: add_profile (z. B. rectangle, circle, slot) in diese Skizze.")
    return result


def _support(doc: Any, body: Any, plane: str, allow_face: bool) -> tuple[tuple[Any, str], str | None]:
    if plane.upper() in ORIGIN_PLANES:
        return (origin_feature(body, plane.upper()), ""), None
    if plane.lower().startswith("face:"):
        if not allow_face:
            raise validation(
                "Skizzen auf Körperflächen sind anfällig für TNP. Ursprungsebene oder datum_plane verwenden "
                "oder allow_face_attachment=true setzen."
            )
        from buddy_core import select

        tip = body.Tip
        if tip is None:
            raise validation("Body hat noch keine Geometrie für eine Flächenreferenz")
        faces = select.resolve(tip.Shape, plane, single=True)
        return (tip, faces[0]), (
            f"Skizze hängt an {tip.Label}.{faces[0]} – bei Topologieänderungen kann die Referenz springen."
        )
    datum = resolve_object(doc, plane)
    if datum.TypeId not in ("PartDesign::Plane", "App::Plane"):
        raise validation(f"'{plane}' ist keine Ebene (erlaubt: XY, XZ, YZ, Datum-Ebene, face:<selector>)")
    return (datum, ""), None


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
                f"Skizze '{sketch.Label}' ungültig: {'; '.join(blocking)}",
                {"sketch": report},
            )
        result.sketch = report
        result.add_modified(sketch)
        if report["dof"] > 0:
            result.warnings.append(
                f"Skizze hat noch {report['dof']} Freiheitsgrad(e) – fully_constrain_sketch oder Maße ergänzen."
            )
        if report["open_wires"]:
            result.warnings.append(
                f"{report['open_wires']} offene(r) Linienzug(e): als Pfad für sweep richtig, "
                "als Profil für Pad/Pocket ungeeignet."
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
