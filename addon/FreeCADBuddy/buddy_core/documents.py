"""Documents and objects: resolve, create, open, save, inspect, delete, undo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import FreeCAD

from buddy_core import naming
from buddy_core.errors import AMBIGUOUS, CoreError, not_found, validation
from buddy_core.result import ToolResult, describe
from buddy_core.transaction import ensure_user_not_editing, transaction


def resolve_document(name: str | None = None) -> Any:
    """Document by name or label; without a name the active document."""
    if name is None:
        doc = FreeCAD.ActiveDocument
        if doc is None:
            raise not_found("Kein aktives Dokument. Erst new_document oder open_document aufrufen.")
        return doc
    docs = FreeCAD.listDocuments()
    if name in docs:
        return docs[name]
    by_label = [doc for doc in docs.values() if doc.Label == name]
    if len(by_label) == 1:
        return by_label[0]
    if by_label:
        raise CoreError(
            AMBIGUOUS, f"Mehrere Dokumente heißen '{name}'", {"candidates": [d.Name for d in by_label]}
        )
    raise not_found(f"Dokument '{name}' nicht gefunden", available=list(docs))


def resolve_object(doc: Any, ref: str, type_prefix: str | None = None) -> Any:
    """Object by internal name or label (optionally restricted to a type prefix)."""
    obj = doc.getObject(ref)
    candidates = [obj] if obj is not None else list(doc.getObjectsByLabel(ref))
    if type_prefix:
        candidates = [c for c in candidates if c.TypeId.startswith(type_prefix)]
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        raise CoreError(
            AMBIGUOUS, f"'{ref}' ist mehrdeutig", {"candidates": [describe(c) for c in candidates]}
        )
    raise not_found(f"Objekt '{ref}' nicht gefunden in Dokument '{doc.Label}'")


def new_document(name: str, activate: bool = True) -> ToolResult:
    safe = naming.sanitize(name) or "Model"
    doc = FreeCAD.newDocument(safe)
    doc.Label = name
    doc.UndoMode = 1
    if activate:
        FreeCAD.setActiveDocument(doc.Name)
    result = ToolResult()
    result.data["document"] = {"name": doc.Name, "label": doc.Label}
    result.hints.append("Nächster Schritt: set_parameters für zentrale Maße, dann create_body.")
    return result


def open_document(path: str) -> ToolResult:
    file = Path(path)
    if not file.is_file():
        raise not_found(f"Datei '{path}' existiert nicht")
    doc = FreeCAD.openDocument(str(file))
    doc.UndoMode = 1
    FreeCAD.setActiveDocument(doc.Name)
    result = ToolResult()
    result.data["document"] = {"name": doc.Name, "label": doc.Label, "file": doc.FileName}
    return result


def save_document(document: str | None = None, path: str | None = None) -> ToolResult:
    doc = resolve_document(document)
    ensure_user_not_editing(doc)
    if path:
        target = Path(path)
        if target.suffix.lower() != ".fcstd":
            raise validation("Dateiendung muss .FCStd sein")
        target.parent.mkdir(parents=True, exist_ok=True)
        doc.saveAs(str(target))
    elif doc.FileName:
        doc.save()
    else:
        raise validation("Dokument wurde noch nie gespeichert: 'path' angeben")
    result = ToolResult()
    result.data["document"] = {"name": doc.Name, "label": doc.Label, "file": doc.FileName}
    return result


def _node(obj: Any) -> dict[str, Any]:
    node: dict[str, Any] = {
        **describe(obj),
        "valid": obj.isValid(),
        "status": obj.getStatusString(),
        "visible": bool(getattr(obj, "Visibility", True)),
    }
    if obj.TypeId == "PartDesign::Body":
        node["tip"] = obj.Tip.Label if obj.Tip else None
        node["features"] = [_node(child) for child in obj.Group if not child.TypeId.startswith("App::Origin")]
    elif obj.TypeId == "Sketcher::SketchObject":
        obj.solve()
        node["dof"] = obj.DoF
        node["fully_constrained"] = bool(obj.FullyConstrained)
    return node


def model_tree(document: str | None = None) -> dict[str, Any]:
    doc = resolve_document(document)
    in_body = {child.Name for obj in doc.Objects if obj.TypeId == "PartDesign::Body" for child in obj.Group}
    # Filter origin elements by membership, not by type: FreeCAD 26.3 added an App::Point ("Origin001")
    # to every origin, and a type list would miss the next addition as well.
    origin_parts = {
        feature.Name
        for obj in doc.Objects
        if obj.TypeId.startswith("App::Origin")
        for feature in getattr(obj, "OriginFeatures", [])
    }
    top_level = [
        obj
        for obj in doc.Objects
        if obj.Name not in in_body
        and obj.Name not in origin_parts
        and not obj.TypeId.startswith("App::Origin")
    ]
    return {
        "document": {"name": doc.Name, "label": doc.Label, "file": doc.FileName},
        "objects": [_node(obj) for obj in top_level],
        "undo": {"count": doc.UndoCount, "names": list(doc.UndoNames)},
        "label_issues": naming.lint_labels(doc),
    }


def _shape_summary(shape: Any) -> dict[str, Any]:
    box = shape.BoundBox
    summary: dict[str, Any] = {
        "valid": shape.isValid(),
        "solids": len(shape.Solids),
        "faces": len(shape.Faces),
        "edges": len(shape.Edges),
        "bound_box": {
            "x": [box.XMin, box.XMax],
            "y": [box.YMin, box.YMax],
            "z": [box.ZMin, box.ZMax],
            "size": [box.XLength, box.YLength, box.ZLength],
        },
    }
    if shape.Solids:
        summary["volume"] = shape.Volume
    return summary


def get_object(ref: str, document: str | None = None) -> dict[str, Any]:
    doc = resolve_document(document)
    obj = resolve_object(doc, ref)
    info: dict[str, Any] = {**_node(obj), "expressions": {k: v for k, v in obj.ExpressionEngine}}
    if obj.TypeId == "Sketcher::SketchObject":
        from buddy_core.sketch import analysis

        info["sketch"] = analysis.analyze(obj)
    shape = getattr(obj, "Shape", None)
    if shape is not None and not shape.isNull():
        info["shape"] = _shape_summary(shape)
    return info


def delete_object(ref: str, document: str | None = None) -> ToolResult:
    doc = resolve_document(document)
    obj = resolve_object(doc, ref)
    result = ToolResult()
    with transaction(doc, f"Löschen: {obj.Label}"):
        label = obj.Label
        for body in (p for p in obj.InList if p.TypeId == "PartDesign::Body"):
            body.removeObject(obj)
        doc.removeObject(obj.Name)
        result.data["deleted"] = label
    return result


def undo(document: str | None = None, steps: int = 1) -> ToolResult:
    doc = resolve_document(document)
    ensure_user_not_editing(doc)
    if steps < 1:
        raise validation("steps muss >= 1 sein")
    if doc.UndoCount < steps:
        raise validation(
            f"Nur {doc.UndoCount} Rückgängig-Schritt(e) verfügbar", available=list(doc.UndoNames)
        )
    undone = list(doc.UndoNames)[:steps]
    for _ in range(steps):
        doc.undo()
    doc.recompute()
    result = ToolResult()
    result.data["undone"] = undone
    return result
