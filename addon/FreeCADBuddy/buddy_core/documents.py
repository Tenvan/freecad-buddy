"""Documents and objects: resolve, create, open, save, close, revert, inspect, delete, undo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import FreeCAD

from buddy_core import naming, stream
from buddy_core.errors import AMBIGUOUS, CoreError, not_found, validation
from buddy_core.result import ToolResult, describe
from buddy_core.transaction import ensure_user_not_editing, transaction


def resolve_document(name: str | None = None) -> Any:
    """Document by name or label; without a name the active document."""
    if name is None:
        doc = FreeCAD.ActiveDocument
        if doc is None:
            raise not_found(
                "No active document. Call document(action='new') or document(action='open') first."
            )
        return doc
    docs = FreeCAD.listDocuments()
    if name in docs:
        return docs[name]
    by_label = [doc for doc in docs.values() if doc.Label == name]
    if len(by_label) == 1:
        return by_label[0]
    if by_label:
        raise CoreError(
            AMBIGUOUS, f"Several documents are called '{name}'", {"candidates": [d.Name for d in by_label]}
        )
    raise not_found(f"Document '{name}' not found", available=list(docs))


def resolve_object(doc: Any, ref: str, type_prefix: str | None = None) -> Any:
    """Object by internal name or label (optionally restricted to a type prefix)."""
    obj = doc.getObject(ref)
    candidates = [obj] if obj is not None else list(doc.getObjectsByLabel(ref))
    if type_prefix:
        candidates = [c for c in candidates if c.TypeId.startswith(type_prefix)]
    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        raise CoreError(AMBIGUOUS, f"'{ref}' is ambiguous", {"candidates": [describe(c) for c in candidates]})
    raise not_found(f"Object '{ref}' not found in document '{doc.Label}'")


def new_document(name: str, activate: bool = True) -> ToolResult:
    safe = naming.sanitize(name) or "Model"
    doc = FreeCAD.newDocument(safe)
    doc.Label = name
    doc.UndoMode = 1
    if activate:
        FreeCAD.setActiveDocument(doc.Name)
    _mark_saved(doc)
    result = ToolResult()
    result.data["document"] = {"name": doc.Name, "label": doc.Label}
    result.hints.append("Next step: set_parameters for the central dimensions, then create_body.")
    return result


def open_document(path: str) -> ToolResult:
    file = Path(path)
    if not file.is_file():
        raise not_found(f"File '{path}' does not exist")
    doc = FreeCAD.openDocument(str(file))
    doc.UndoMode = 1
    FreeCAD.setActiveDocument(doc.Name)
    _mark_saved(doc)
    result = ToolResult()
    result.data["document"] = {"name": doc.Name, "label": doc.Label, "file": doc.FileName}
    return result


def save_document(document: str | None = None, path: str | None = None) -> ToolResult:
    doc = resolve_document(document)
    ensure_user_not_editing(doc)
    if path:
        target = Path(path)
        if target.suffix.lower() != ".fcstd":
            raise validation("File extension must be .FCStd")
        target.parent.mkdir(parents=True, exist_ok=True)
        doc.saveAs(str(target))
    elif doc.FileName:
        doc.save()
    else:
        raise validation("The document was never saved: pass 'path'")
    _mark_saved(doc)
    result = ToolResult()
    result.data["document"] = {"name": doc.Name, "label": doc.Label, "file": doc.FileName}
    return result


# Undo count per document at the last save/open. App documents have no "modified" flag without the GUI,
# so headless the undo count since then stands in for it (conservative: an undo also counts as a change).
_saved_marks: dict[str, int] = {}


def _mark_saved(doc: Any) -> None:
    _saved_marks[doc.Name] = doc.UndoCount


def has_unsaved_changes(doc: Any) -> bool:
    """GUI: the document's Modified flag; headless: undo steps since the last save/open (or creation)."""
    if FreeCAD.GuiUp:
        import FreeCADGui

        gui_doc = FreeCADGui.getDocument(doc.Name)
        if gui_doc is not None:
            return bool(gui_doc.Modified)
    return doc.UndoCount != _saved_marks.get(doc.Name, 0)


UNSAVED_MODES = ("refuse", "save", "discard")


def _open_documents() -> list[dict[str, Any]]:
    return [{"name": d.Name, "label": d.Label, "file": d.FileName} for d in FreeCAD.listDocuments().values()]


def close_document(
    document: str | None = None, unsaved: str = "refuse", path: str | None = None
) -> ToolResult:
    """Close a document. Unsaved changes are refused unless ``unsaved`` is 'save' or 'discard'."""
    if unsaved not in UNSAVED_MODES:
        raise validation(f"unsaved must be one of {', '.join(UNSAVED_MODES)}")
    doc = resolve_document(document)
    ensure_user_not_editing(doc)
    modified = has_unsaved_changes(doc)
    if modified and unsaved == "refuse":
        raise validation(
            f"Document '{doc.Label}' has unsaved changes: pass unsaved='save' (with path for a new "
            "document) or unsaved='discard'"
        )
    if modified and unsaved == "save":
        save_document(doc.Name, path)
    closed = {"name": doc.Name, "label": doc.Label, "file": doc.FileName}
    FreeCAD.closeDocument(doc.Name)
    _saved_marks.pop(closed["name"], None)
    result = ToolResult()
    result.data["closed"] = closed
    result.data["discarded_changes"] = modified and unsaved == "discard"
    result.data["open_documents"] = _open_documents()
    active = FreeCAD.ActiveDocument
    result.data["active_document"] = active.Name if active else None
    return result


def revert_document(document: str | None = None) -> ToolResult:
    """Discard all changes since the last save: close without saving and reopen the saved file."""
    doc = resolve_document(document)
    ensure_user_not_editing(doc)
    if not doc.FileName:
        raise validation(
            f"Document '{doc.Label}' was never saved, there is nothing to revert to: "
            "use document(action='close', unsaved='discard')"
        )
    name, file, discarded = doc.Name, doc.FileName, has_unsaved_changes(doc)
    FreeCAD.closeDocument(name)
    _saved_marks.pop(name, None)
    result = open_document(file)
    result.data["discarded_changes"] = discarded
    return result


def _transformation_steps(objects: Any) -> set[str]:
    """Names of the sub-transformations claimed by MultiTransforms among ``objects``."""
    return {
        step.Name
        for obj in objects
        if obj.TypeId == "PartDesign::MultiTransform"
        for step in obj.Transformations
    }


def _node(obj: Any) -> dict[str, Any]:
    node: dict[str, Any] = {
        **describe(obj),
        "valid": obj.isValid(),
        "status": obj.getStatusString(),
        "visible": bool(getattr(obj, "Visibility", True)),
    }
    if obj.TypeId == "PartDesign::Body":
        node["tip"] = obj.Tip.Label if obj.Tip else None
        steps = _transformation_steps(obj.Group)
        node["features"] = [
            _node(child)
            for child in obj.Group
            if not child.TypeId.startswith("App::Origin") and child.Name not in steps
        ]
    elif obj.TypeId == "PartDesign::MultiTransform":
        node["transformations"] = [_node(step) for step in obj.Transformations]
    elif obj.TypeId == "Sketcher::SketchObject":
        obj.solve()
        node["dof"] = obj.DoF
        node["fully_constrained"] = bool(obj.FullyConstrained)
    elif obj.Name == stream.GROUP_NAME:
        node["steps"] = len(stream.entries(obj.Document))
        node["storepoints"] = [
            {
                **describe(marker),
                "position": marker.Position,
                "feature": marker.Feature.Label if marker.Feature is not None else None,
            }
            for marker in stream.markers(obj.Document)
        ]
    return node


def model_tree(document: str | None = None) -> dict[str, Any]:
    doc = resolve_document(document)
    in_body = {child.Name for obj in doc.Objects if obj.TypeId == "PartDesign::Body" for child in obj.Group}
    # older files keep the grid steps in the document root – they still belong under their MultiTransform
    in_body |= _transformation_steps(doc.Objects)
    # Filter origin elements by membership, not by type: FreeCAD 26.3 added an App::Point ("Origin001")
    # to every origin, and a type list would miss the next addition as well.
    origin_parts = {
        feature.Name
        for obj in doc.Objects
        if obj.TypeId.startswith("App::Origin")
        for feature in getattr(obj, "OriginFeatures", [])
    }
    markers = {marker.Name for marker in stream.markers(doc)}  # listed under their group
    top_level = [
        obj
        for obj in doc.Objects
        if obj.Name not in in_body
        and obj.Name not in origin_parts
        and obj.Name not in markers
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
    info.update(_assembly_details(obj))
    return info


def _assembly_details(obj: Any) -> dict[str, Any]:
    """Material, colour, link target, group members, Asm4 attachment and fastener data, when present."""
    details: dict[str, Any] = {}
    material = getattr(obj, "ShapeMaterial", None)
    if material is not None and material.Name not in ("", "Default"):
        details["material"] = material.Name
    view = getattr(obj, "ViewObject", None)
    appearance = getattr(view, "ShapeAppearance", None) if view is not None else None
    if appearance:
        details["color"] = [round(c, 3) for c in appearance[0].DiffuseColor[:3]]
    linked = getattr(obj, "LinkedObject", None)
    if obj.TypeId == "App::Link" and linked is not None:
        details["linked_object"] = describe(linked)
    if obj.TypeId in ("App::Part", "App::DocumentObjectGroup"):
        details["group"] = [describe(child) for child in obj.Group]
    if getattr(obj, "SolverId", ""):
        details["attachment"] = {
            "attached_to": getattr(obj, "AttachedTo", ""),
            "offset": [round(v, 4) for v in obj.AttachmentOffset.Base],
            "solver": obj.SolverId,
        }
        details["placement"] = [round(v, 4) for v in obj.Placement.Base]
    if obj.TypeId == "Part::FeaturePython" and hasattr(obj, "Diameter") and hasattr(obj, "Type"):
        details["fastener"] = {
            "type": obj.Type,
            "diameter": obj.Diameter,
            "thread": getattr(obj, "Thread", False),
        }
    return details


def delete_object(ref: str, document: str | None = None) -> ToolResult:
    doc = resolve_document(document)
    obj = resolve_object(doc, ref)
    result = ToolResult()
    with transaction(doc, f"Delete: {obj.Label}"):
        label = obj.Label
        # a MultiTransform owns its steps (FreeCAD's GUI deletes them together as well)
        steps = list(obj.Transformations) if obj.TypeId == "PartDesign::MultiTransform" else []
        for target in (obj, *steps):
            for body in (p for p in target.InList if p.TypeId == "PartDesign::Body"):
                body.removeObject(target)
            doc.removeObject(target.Name)
        result.data["deleted"] = label
    return result


def undo(document: str | None = None, steps: int = 1) -> ToolResult:
    doc = resolve_document(document)
    ensure_user_not_editing(doc)
    if steps < 1:
        raise validation("steps must be >= 1")
    if doc.UndoCount < steps:
        raise validation(f"Only {doc.UndoCount} undo step(s) available", available=list(doc.UndoNames))
    undone = list(doc.UndoNames)[:steps]
    for _ in range(steps):
        doc.undo()
    doc.recompute()
    result = ToolResult()
    result.data["undone"] = undone
    return result
