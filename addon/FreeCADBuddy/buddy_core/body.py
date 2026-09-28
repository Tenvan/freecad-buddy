"""PartDesign bodies and their origin features."""

from __future__ import annotations

from typing import Any

import FreeCAD

from buddy_core import naming
from buddy_core.documents import resolve_document, resolve_object
from buddy_core.errors import AMBIGUOUS, CoreError, not_found, validation
from buddy_core.result import ToolResult, describe
from buddy_core.transaction import transaction

ORIGIN_ROLES = {
    "XY": "XY_Plane",
    "XZ": "XZ_Plane",
    "YZ": "YZ_Plane",
    "X": "X_Axis",
    "Y": "Y_Axis",
    "Z": "Z_Axis",
}


def resolve_body(doc: Any, ref: str | None = None) -> Any:
    if ref:
        return resolve_object(doc, ref, "PartDesign::Body")
    bodies = [obj for obj in doc.Objects if obj.TypeId == "PartDesign::Body"]
    if len(bodies) == 1:
        return bodies[0]
    if not bodies:
        raise not_found("Kein Body im Dokument. Erst create_body aufrufen.")
    raise CoreError(
        AMBIGUOUS, "Mehrere Bodies: 'body' angeben", {"candidates": [describe(b) for b in bodies]}
    )


def body_of(obj: Any) -> Any:
    for parent in obj.InList:
        if parent.TypeId == "PartDesign::Body":
            return parent
    raise validation(f"'{obj.Label}' liegt in keinem Body")


def origin_feature(body: Any, role: str) -> Any:
    key = ORIGIN_ROLES.get(role.upper(), role)
    for feature in body.Origin.OriginFeatures:
        if feature.Role == key:
            return feature
    raise validation(f"Unbekannte Ursprungsreferenz '{role}' (erlaubt: {', '.join(ORIGIN_ROLES)})")


def create_body(label: str, document: str | None = None) -> ToolResult:
    doc = resolve_document(document)
    result = ToolResult()
    with transaction(doc, f"Body anlegen: {label}"):
        body = doc.addObject("PartDesign::Body", "Body")
        body.Label = naming.unique_label(doc, naming.sanitize(label) or "Part")
        result.add_created(body)
    if FreeCAD.GuiUp:
        import FreeCADGui

        gui_doc = FreeCADGui.getDocument(doc.Name)
        view = gui_doc.ActiveView if gui_doc is not None else None
        try:
            if view is not None:
                view.setActiveObject("pdbody", body)
        except Exception:  # the body exists already; activating it is only a convenience
            result.warnings.append("Body angelegt, konnte aber in der GUI nicht aktiviert werden.")
    result.data["body"] = describe(body)
    result.hints.append("Nächster Schritt: create_sketch auf XY/XZ/YZ und add_profile.")
    return result
