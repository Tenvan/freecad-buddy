"""Shape binders: bring geometry of another body into a body (``PartDesign::SubShapeBinder``).

The binder follows its source (``BindMode`` Synchronized) and is a stable source for external
geometry, sketches and datums of the target body - the PartDesign way to reference across bodies.
"""

from __future__ import annotations

from typing import Any

from buddy_core import display, naming
from buddy_core.body import body_of, resolve_body
from buddy_core.documents import resolve_document, resolve_object
from buddy_core.errors import RECOMPUTE_FAILED, CoreError, validation
from buddy_core.result import ToolResult, describe
from buddy_core.sketch.external import SKETCH_TYPES, sketch_element
from buddy_core.transaction import transaction


def _parse(doc: Any, spec: str) -> tuple[Any, str | None]:
    """``Object``, ``Object:Element``, ``Body:Object`` or ``Body:Object:Element`` → (object, element)."""
    parts = [p.strip() for p in spec.split(":") if p.strip()]
    if not 1 <= len(parts) <= 3:
        raise validation(f"Invalid source '{spec}' (use Object, Object:Element or Body:Object[:Element])")
    first = resolve_object(doc, parts[0])
    if first.TypeId == "PartDesign::Body" and len(parts) > 1:
        obj = resolve_object(doc, parts[1])
        if obj not in first.Group:
            raise validation(f"'{obj.Label}' is not in body '{first.Label}'")
        element = parts[2] if len(parts) == 3 else None
    else:
        if len(parts) == 3:
            raise validation(f"'{parts[0]}' is not a body (use Body:Object:Element)")
        obj, element = first, (parts[1] if len(parts) == 2 else None)
    if element and obj.TypeId in SKETCH_TYPES and element.lower().startswith("g"):
        element = sketch_element(obj, element)[0]
    return obj, element


def _owner(obj: Any) -> Any:
    return obj if obj.TypeId == "PartDesign::Body" else body_of(obj)


def shape_binder(
    sources: list[str],
    body: str | None = None,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Bind objects or elements of other bodies into ``body`` as one synchronized SubShapeBinder."""
    doc = resolve_document(document)
    target = resolve_body(doc, body)
    if not sources:
        raise validation("sources must not be empty")
    support: dict[str, tuple[Any, list[str]]] = {}
    for spec in sources:
        obj, element = _parse(doc, spec)
        if _owner(obj) == target:
            raise validation(
                f"'{obj.Label}' is already in body '{target.Label}'; reference it directly with "
                "add_geometry type 'external' instead of a binder"
            )
        entry = support.setdefault(obj.Name, (obj, []))
        if element:
            entry[1].append(element)
    result = ToolResult()
    first = next(iter(support.values()))[0]
    with transaction(doc, f"Shape binder: {purpose or first.Label}"):
        binder = target.newObject("PartDesign::SubShapeBinder", "Binder")
        binder.Label = naming.make_label(doc, "Binder", purpose or first.Label)
        binder.Support = [(obj, tuple(elements) if elements else ("",)) for obj, elements in support.values()]
        display.apply_selection_style(binder)
        doc.recompute()
        if not binder.isValid() or binder.Shape.isNull():
            raise CoreError(
                RECOMPUTE_FAILED,
                f"Shape binder '{binder.Label}' has no geometry",
                {"hints": ["Check the source elements (EdgeN, FaceN, VertexN or g<N> of a sketch)."]},
            )
        result.add_created(binder)
    shape = binder.Shape
    result.data["binder"] = describe(binder)
    result.data["elements"] = {
        "faces": len(shape.Faces),
        "edges": len(shape.Edges),
        "vertexes": len(shape.Vertexes),
    }
    result.hints.append(
        f"Use '{binder.Label}' as source of add_geometry type 'external' (element EdgeN/VertexN or an edge "
        "selector); it follows changes of its source."
    )
    return result
