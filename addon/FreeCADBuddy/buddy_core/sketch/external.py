"""External geometry: reference edges and points of other objects in the same body (``x<N>``).

Sources are sketches (elements ``g<N>`` like in the source sketch), datum features and shape
binders (``EdgeN``/``VertexN`` or a semantic edge selector). Solid features are TNP-prone and
need ``allow_face_reference``. Other bodies are only reachable through ``shape_binder``.
"""

from __future__ import annotations

import re
from typing import Any

from buddy_core.body import body_of
from buddy_core.documents import resolve_object
from buddy_core.errors import NOT_FOUND, UNSUPPORTED, CoreError, validation
from buddy_core.sketch import refs

SKETCH_TYPES = ("Sketcher::SketchObject",)
DATUM_TYPES = ("PartDesign::Plane", "PartDesign::Line", "PartDesign::Point")
BINDER_TYPES = ("PartDesign::SubShapeBinder", "PartDesign::ShapeBinder")
STABLE_TYPES = SKETCH_TYPES + DATUM_TYPES + BINDER_TYPES

_SKETCH_ELEMENT = re.compile(r"^g(\d+)(?:\.(start|end|center|mid))?$")
_SHAPE_ELEMENT = re.compile(r"^(Edge|Vertex|Face)(\d+)$")
_MAPPED_SKETCH = re.compile(r"^;?g(\d+)(?:v\d+)?;SKT$")


def _candidates(sketch: Any) -> list[str]:
    """Labels of objects the sketch could reference (same body, earlier in the tree)."""
    group = list(body_of(sketch).Group)
    return [obj.Label for obj in group[: group.index(sketch)] if obj.TypeId.startswith(STABLE_TYPES)]


def _source(doc: Any, sketch: Any, ref: str) -> Any:
    try:
        source = resolve_object(doc, ref)
    except CoreError as exc:
        if exc.name != NOT_FOUND:
            raise
        raise validation(f"Source '{ref}' not found", candidates=_candidates(sketch)) from exc
    if source == sketch:
        raise validation(f"Sketch '{sketch.Label}' cannot reference itself")
    target_body = body_of(sketch)
    try:
        source_body = body_of(source)
    except CoreError:
        source_body = None
    if source_body != target_body:
        raise validation(
            f"'{source.Label}' is not in body '{target_body.Label}'. Reference other bodies through "
            "shape_binder and use the binder as source",
        )
    group = list(target_body.Group)
    if group.index(source) > group.index(sketch):
        raise validation(
            f"'{source.Label}' comes after '{sketch.Label}' in the model tree; referencing it would "
            "create a dependency cycle"
        )
    return source


def sketch_element(source: Any, element: str) -> tuple[str, int]:
    """Shape element name and position for ``g<N>[.pos]`` of a source sketch."""
    match = _SKETCH_ELEMENT.match(element.strip().lower())
    if not match:
        raise validation(
            f"Invalid element '{element}' for sketch '{source.Label}' (allowed: g<N>, g<N>.start|end|center)"
        )
    geo_id = int(match.group(1))
    position = refs.position(match.group(2))
    if geo_id >= source.GeometryCount:
        raise validation(f"Geometry g{geo_id} does not exist in '{source.Label}' ({source.GeometryCount})")
    if source.getConstruction(geo_id):
        raise validation(
            f"g{geo_id} of '{source.Label}' is construction geometry, which FreeCAD does not expose for "
            "external references. Reference real geometry (e.g. the hole circle) or use a layout sketch"
        )
    is_point = type(source.Geometry[geo_id]).__name__ == "Point"
    wanted = f"g{geo_id + 1}v1;SKT" if is_point else f"g{geo_id + 1};SKT"
    for name, mapped in source.Shape.ElementReverseMap.items():
        values = mapped if isinstance(mapped, list | tuple) else [mapped]
        if any(str(value).lstrip(";") == wanted for value in values):
            return name, position
    raise validation(f"g{geo_id} of '{source.Label}' has no shape element (recompute the source sketch)")


def _shape_elements(doc: Any, source: Any, element: str) -> list[str]:
    """``EdgeN``/``VertexN`` or a semantic edge selector on a datum, binder or solid feature."""
    match = _SHAPE_ELEMENT.match(element.strip())
    if match is None:
        from buddy_core import select

        if element.strip().lower().startswith("face"):
            raise validation("Faces cannot be external geometry; reference their edges (e.g. 'edges:top')")
        return select.resolve(source.Shape, element, single=False, doc=doc)
    kind, number = match.group(1), int(match.group(2))
    if kind == "Face":
        raise validation("Faces cannot be external geometry; reference their edges (e.g. 'edges:top')")
    available = len(source.Shape.Edges if kind == "Edge" else source.Shape.Vertexes)
    if not 1 <= number <= available:
        raise validation(f"{element} does not exist on '{source.Label}' ({available} {kind.lower()}s)")
    return [element]


def _add_one(sketch: Any, source: Any, element: str, defining: bool) -> int:
    before = refs.external_count(sketch)
    try:
        if defining:
            sketch.addExternal(source.Name, element, True)
        else:
            sketch.addExternal(source.Name, element)
    except TypeError as exc:
        raise CoreError(
            UNSUPPORTED, "This FreeCAD build does not support defining external geometry"
        ) from exc
    except ValueError as exc:
        existing = _find(sketch, source, element)
        if existing is not None:
            return existing
        raise validation(f"FreeCAD refused {source.Label}.{element}: {exc}") from exc
    if refs.external_count(sketch) != before + 1:
        raise validation(f"FreeCAD did not add {source.Label}.{element} as external geometry")
    return before


def _find(sketch: Any, source: Any, element: str) -> int | None:
    for info in describe(sketch):
        if info["source_name"] == source.Name and element in (info["shape_element"], info["element"]):
            return info["index"]
    return None


def add(doc: Any, sketch: Any, item: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Add one ``{type: external, source, element, defining?, allow_face_reference?}`` item.

    Returns the new references (``x<N>`` with the position suffix of ``g<N>.pos``) and warnings.
    """
    if "source" not in item or "element" not in item:
        raise validation("External geometry needs 'source' and 'element'")
    source = _source(doc, sketch, str(item["source"]))
    element = str(item["element"])
    defining = bool(item.get("defining", False))
    warnings: list[str] = []
    if source.TypeId in SKETCH_TYPES:
        name, position = sketch_element(source, element)
        targets = [(name, position)]
    else:
        if not source.TypeId.startswith(STABLE_TYPES):
            if not item.get("allow_face_reference", False):
                raise validation(
                    f"'{source.Label}' is a solid feature; its edges are prone to the topological naming "
                    "problem. Reference a layout sketch, datum or binder, or set allow_face_reference=true"
                )
            warnings.append(
                f"External geometry follows {source.Label}.{element} - the reference can jump when the "
                "topology changes"
            )
        targets = [(name, refs.NONE) for name in _shape_elements(doc, source, element)]
    added = [
        refs.format_ref(refs.external_geo_id(_add_one(sketch, source, n, defining)), p) for n, p in targets
    ]
    return added, warnings


def _friendly(source: Any, sub: str) -> tuple[str, str]:
    """(Buddy element, shape element) for a stored external reference."""
    shape_element = sub
    if source is not None and not _SHAPE_ELEMENT.match(sub):
        mapped = sub.lstrip(";")
        for name, value in source.Shape.ElementReverseMap.items():
            values = value if isinstance(value, list | tuple) else [value]
            if any(str(v).lstrip(";") == mapped for v in values):
                shape_element = name
                break
    if source is not None and source.TypeId in SKETCH_TYPES:
        match = _MAPPED_SKETCH.match(sub)
        if match:
            return f"g{int(match.group(1)) - 1}", shape_element
    return shape_element, shape_element


def describe(sketch: Any) -> list[dict[str, Any]]:
    """External geometry of the sketch: ``[{ref, index, source, element, defining, stable}]``."""
    doc = sketch.Document
    entries: list[dict[str, Any]] = []
    for index, geometry in enumerate(list(sketch.ExternalGeo)[2:]):
        entry: dict[str, Any] = {"ref": f"x{index}", "index": index, "defining": False}
        try:
            extension = geometry.getExtensionOfType("Sketcher::ExternalGeometryExtension")
            source_name, _, sub = extension.Ref.partition(".")
            entry["defining"] = bool(extension.testFlag("Defining"))
        except Exception:  # API drift between builds: report what is known
            source_name, sub = "", ""
        source = doc.getObject(source_name) if source_name else None
        element, shape_element = _friendly(source, sub)
        entry.update(
            source=source.Label if source is not None else source_name,
            source_name=source_name,
            element=element,
            shape_element=shape_element,
            stable=source is not None and source.TypeId.startswith(STABLE_TYPES),
        )
        entries.append(entry)
    return entries


def linked_count(sketch: Any) -> int:
    """External geometries whose link still exists (``ExternalGeo`` can keep stale entries)."""
    linked = sum(len(subs) for _, subs in sketch.ExternalGeometry)
    return min(refs.external_count(sketch), linked)


def dangling(sketch: Any) -> list[dict[str, Any]]:
    """Constraints that point at external geometry which no longer exists (deleted source)."""
    count = linked_count(sketch)
    found = []
    for index, constraint in enumerate(sketch.Constraints):
        for attr in ("First", "Second", "Third"):
            geo_id = getattr(constraint, attr, -2000)
            if geo_id <= refs.FIRST_EXTERNAL and geo_id != -2000 and refs.external_index(geo_id) >= count:
                found.append({"constraint": index, "ref": refs.format_ref(geo_id)})
                break
    return found
