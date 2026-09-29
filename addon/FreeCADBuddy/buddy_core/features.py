"""PartDesign features. Every feature is one undo step, gets a readable label and accepts
parameter names for its dimensions.

Subtractive features (pocket, groove, hole) that remove no material are flipped once
automatically – the typical mistake when a sketch sits on the bottom plane of the part.
"""

from __future__ import annotations

from typing import Any

import FreeCAD

from buddy_core import display, naming, select, values, view
from buddy_core.body import body_of, origin_feature, resolve_body
from buddy_core.documents import resolve_document, resolve_object
from buddy_core.errors import RECOMPUTE_FAILED, UNSUPPORTED, CoreError, validation
from buddy_core.result import ToolResult, describe
from buddy_core.sketch.model import plane_support, resolve_sketch
from buddy_core.transaction import transaction

_VOLUME_TOL = 1e-6


def _volume(obj: Any) -> float:
    shape = getattr(obj, "Shape", None)
    return shape.Volume if shape is not None and not shape.isNull() and shape.Solids else 0.0


def _profile(doc: Any, sketch_ref: str) -> tuple[Any, Any]:
    sketch = resolve_sketch(doc, sketch_ref)
    return sketch, body_of(sketch)


def _new(body: Any, type_id: str, prefix: str, purpose: str | None, fallback: str) -> Any:
    feature = body.newObject(type_id, prefix)
    feature.Label = naming.make_label(body.Document, prefix, purpose or fallback)
    display.apply_selection_style(feature)
    return feature


def _finish(doc: Any, feature: Any, result: ToolResult) -> None:
    doc.recompute()
    if not feature.isValid():
        return  # the transaction reports the failure with hints
    shape = feature.Shape
    if len(shape.Solids) > 1:
        raise CoreError(
            RECOMPUTE_FAILED,
            f"'{feature.Label}' creates {len(shape.Solids)} separate solids",
            {"hints": ["The profile must touch or overlap the existing solid."]},
        )
    result.add_created(feature)
    result.data["feature"] = describe(feature)
    result.data["volume"] = shape.Volume if shape.Solids else 0.0


def _has_solid(body: Any) -> bool:
    tip = body.Tip
    return tip is not None and bool(getattr(tip, "Shape", None) and tip.Shape.Solids)


def _show_first_base_feature(doc: Any, feature: Any, result: ToolResult) -> None:
    """After the first solid of a body, fit an isometric view so the user can follow the build."""
    if not (FreeCAD.GuiUp and feature.isValid()):
        return
    try:
        view.set_view("iso", True, doc.Name)
    except CoreError:
        return  # no 3D view in front (e.g. spreadsheet) - modelling result is unaffected
    result.data["view"] = "iso"


def _ensure_cuts(doc: Any, feature: Any, volume_before: float, result: ToolResult) -> None:
    doc.recompute()
    if feature.isValid() and volume_before - _volume(feature) > _VOLUME_TOL:
        return
    feature.Reversed = not feature.Reversed
    doc.recompute()
    if feature.isValid() and volume_before - _volume(feature) > _VOLUME_TOL:
        result.warnings.append(
            f"Direction of '{feature.Label}' reversed automatically (it removed nothing otherwise)."
        )
        return
    raise CoreError(
        RECOMPUTE_FAILED,
        f"'{feature.Label}' removes no material in either direction",
        {"hints": ["Check sketch position and depth: the profile must cover the solid."]},
    )


def pad(
    sketch: str,
    length: values.ValueSpec = 10,
    mode: str = "length",
    length2: values.ValueSpec | None = None,
    reversed: bool = False,
    taper: values.ValueSpec = 0,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Extrude a closed profile. ``mode``: length | symmetric | two_sides | up_to_last | up_to_first.
    ``taper`` (degrees) tilts the side walls."""
    doc = resolve_document(document)
    profile, body = _profile(doc, sketch)
    result = ToolResult()
    first = not _has_solid(body)
    with transaction(doc, f"Pad: {purpose or profile.Label}"):
        feature = _new(body, "PartDesign::Pad", "Pad", purpose, profile.Label.removeprefix("Sketch_"))
        feature.Profile = profile
        feature.Reversed = reversed
        if mode in ("up_to_last", "up_to_first"):
            feature.Type = "UpToLast" if mode == "up_to_last" else "UpToFirst"
        else:
            values.apply(feature, "Length", values.resolve(doc, length, "length"))
            if mode == "symmetric":
                feature.SideType = "Symmetric"
            elif mode == "two_sides":
                feature.SideType = "Two sides"
                values.apply(
                    feature,
                    "Length2",
                    values.resolve(doc, length2 if length2 is not None else length, "length2"),
                )
            elif mode != "length":
                raise validation("mode must be length, symmetric, two_sides, up_to_last or up_to_first")
        _apply_taper(doc, feature, taper, mode == "two_sides")
        profile.Visibility = False
        _finish(doc, feature, result)
    if first:
        _show_first_base_feature(doc, feature, result)
    return result


def _apply_taper(doc: Any, feature: Any, taper: values.ValueSpec, both_sides: bool) -> None:
    value = values.resolve(doc, taper, "taper")
    if not (value.number or value.expression):
        return
    values.apply(feature, "TaperAngle", value, unit="deg")
    if both_sides:
        values.apply(feature, "TaperAngle2", value, unit="deg")


def pocket(
    sketch: str,
    depth: values.ValueSpec = 5,
    mode: str = "length",
    reversed: bool = False,
    taper: values.ValueSpec = 0,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Cut a closed profile into the body. ``mode``: length | symmetric | through_all | up_to_first.
    ``taper`` (degrees) tilts the side walls."""
    doc = resolve_document(document)
    profile, body = _profile(doc, sketch)
    result = ToolResult()
    with transaction(doc, f"Pocket: {purpose or profile.Label}"):
        before = _volume(body.Tip) if body.Tip else 0.0
        feature = _new(body, "PartDesign::Pocket", "Pocket", purpose, profile.Label.removeprefix("Sketch_"))
        feature.Profile = profile
        feature.Reversed = reversed
        if mode in ("through_all", "up_to_first"):
            feature.Type = "ThroughAll" if mode == "through_all" else "UpToFirst"
        else:
            values.apply(feature, "Length", values.resolve(doc, depth, "depth"))
            if mode == "symmetric":
                feature.SideType = "Symmetric"
            elif mode != "length":
                raise validation("mode must be length, symmetric, through_all or up_to_first")
        _apply_taper(doc, feature, taper, False)
        profile.Visibility = False
        _ensure_cuts(doc, feature, before, result)
        _finish(doc, feature, result)
    return result


def _revolve_axis(sketch: Any, body: Any, axis: str) -> tuple[Any, list[str]]:
    key = axis.upper()
    if key in ("V_AXIS", "H_AXIS"):
        return sketch, [key.replace("_AXIS", "_Axis")]
    return _axis_reference(body, axis)


def _axis_reference(body: Any, axis: str) -> tuple[Any, list[str]]:
    """Body axis X/Y/Z or a datum line of the same body (revolve, polar pattern, helix)."""
    if axis.upper() in ("X", "Y", "Z"):
        return origin_feature(body, axis.upper()), [""]
    line = resolve_object(body.Document, axis)
    if line.TypeId != "PartDesign::Line" or body_of(line) is not body:
        raise validation(
            "axis must be V_Axis, H_Axis (sketch axes), X/Y/Z (body axes) or a datum line of this body"
        )
    return line, [""]


def revolve(
    sketch: str,
    axis: str = "V_Axis",
    angle: values.ValueSpec = 360,
    subtractive: bool = False,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Revolution (additive) or Groove (subtractive) around a sketch or body axis."""
    doc = resolve_document(document)
    profile, body = _profile(doc, sketch)
    result = ToolResult()
    type_id, prefix = (
        ("PartDesign::Groove", "Groove") if subtractive else ("PartDesign::Revolution", "Revolution")
    )
    first = not subtractive and not _has_solid(body)
    with transaction(doc, f"{prefix}: {purpose or profile.Label}"):
        before = _volume(body.Tip) if body.Tip else 0.0
        feature = _new(body, type_id, prefix, purpose, profile.Label.removeprefix("Sketch_"))
        feature.Profile = profile
        feature.ReferenceAxis = _revolve_axis(profile, body, axis)
        values.apply(feature, "Angle", values.resolve(doc, angle, "angle"), unit="deg")
        profile.Visibility = False
        if subtractive:
            _ensure_cuts(doc, feature, before, result)
        _finish(doc, feature, result)
    if first:
        _show_first_base_feature(doc, feature, result)
    return result


def sweep(
    profile: str,
    path: str,
    subtractive: bool = False,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Sweep a closed profile along a path sketch (AdditivePipe, or SubtractivePipe for a cut).

    The profile should sit at the start of the path, perpendicular to it (e.g. a circle on XY
    for a path that starts vertically) - that is how a person sets up a sweep in FreeCAD.
    """
    doc = resolve_document(document)
    section, body = _profile(doc, profile)
    spine = resolve_sketch(doc, path)
    if body_of(spine) is not body:
        raise validation("Profile and path must be in the same body")
    edges = spine.Shape.Edges if not spine.Shape.isNull() else []
    if not edges:
        raise validation(f"Path '{spine.Label}' contains no edges")
    type_id, prefix = (
        ("PartDesign::SubtractivePipe", "SweepCut") if subtractive else ("PartDesign::AdditivePipe", "Sweep")
    )
    result = ToolResult()
    first = not subtractive and not _has_solid(body)
    with transaction(doc, f"{prefix}: {purpose or section.Label}"):
        before = _volume(body.Tip) if body.Tip else 0.0
        feature = _new(body, type_id, prefix, purpose, section.Label.removeprefix("Sketch_"))
        feature.Profile = section
        feature.Spine = (spine, [f"Edge{index + 1}" for index in range(len(edges))])
        section.Visibility = False
        spine.Visibility = False
        if subtractive:
            _ensure_cuts(doc, feature, before, result)
        _finish(doc, feature, result)
    if first:
        _show_first_base_feature(doc, feature, result)
    return result


def _same_plane(first: Any, second: Any) -> bool:
    a, b = first.Placement, second.Placement
    return (a.Base - b.Base).Length < 1e-6 and a.Rotation.isSame(b.Rotation, 1e-6)


def loft(
    sketches: list[str],
    subtractive: bool = False,
    ruled: bool = False,
    closed: bool = False,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Loft through two or more sketches in the given order (AdditiveLoft, or SubtractiveLoft
    for a cut): funnels, adapters, transitions between cross-sections.

    The sketches sit on origin planes or datum planes with an offset parameter; the first one is
    the profile, the others the sections - that is how a person sets up a loft in FreeCAD.
    """
    doc = resolve_document(document)
    if len(sketches) < 2:
        raise validation("A loft needs at least two sketches on different planes")
    first, body = _profile(doc, sketches[0])
    sections = [resolve_sketch(doc, ref) for ref in sketches[1:]]
    for sketch in sections:
        if body_of(sketch) is not body:
            raise validation("All loft sketches must be in the same body")
    for sketch in (first, *sections):
        if sketch.Shape.isNull() or not sketch.Shape.Wires:
            raise validation(f"Sketch '{sketch.Label}' contains no closed profile")
    for previous, sketch in zip((first, *sections), sections, strict=False):
        if _same_plane(previous, sketch):
            raise validation(
                f"Sketches '{previous.Label}' and '{sketch.Label}' lie on the same plane",
                hints=["Put each section on its own plane, e.g. a datum_plane with an offset parameter."],
            )
    type_id, prefix = (
        ("PartDesign::SubtractiveLoft", "LoftCut") if subtractive else ("PartDesign::AdditiveLoft", "Loft")
    )
    result = ToolResult()
    first_solid = not subtractive and not _has_solid(body)
    with transaction(doc, f"{prefix}: {purpose or first.Label}"):
        before = _volume(body.Tip) if body.Tip else 0.0
        feature = _new(body, type_id, prefix, purpose, first.Label.removeprefix("Sketch_"))
        feature.Profile = first
        feature.Sections = sections
        feature.Ruled = ruled
        feature.Closed = closed
        for sketch in (first, *sections):
            sketch.Visibility = False
        if subtractive:
            _ensure_cuts(doc, feature, before, result)
        _finish(doc, feature, result)
    if first_solid:
        _show_first_base_feature(doc, feature, result)
    return result


def make_helix(
    body: Any,
    profile: Any,
    reference_axis: Any,
    pitch: values.Value,
    height: values.Value | None,
    turns: values.Value | None,
    angle: values.Value,
    left_handed: bool,
    subtractive: bool,
    prefix: str,
    purpose: str | None,
    fallback: str,
) -> Any:
    """The one helix feature of the core (used by ``helix`` and ``thread``); no recompute here."""
    type_id = "PartDesign::SubtractiveHelix" if subtractive else "PartDesign::AdditiveHelix"
    feature = _new(body, type_id, prefix, purpose, fallback)
    feature.Profile = profile
    feature.ReferenceAxis = reference_axis
    feature.Mode = "pitch-height-angle" if height is not None else "pitch-turns-angle"
    values.apply(feature, "Pitch", pitch)
    if height is not None:
        values.apply(feature, "Height", height)
    if turns is not None:
        values.apply(feature, "Turns", turns, unit="")
    values.apply(feature, "Angle", angle, unit="deg")
    feature.LeftHanded = left_handed
    return feature


def helix(
    sketch: str,
    pitch: values.ValueSpec,
    height: values.ValueSpec | None = None,
    turns: values.ValueSpec | None = None,
    axis: str = "V_Axis",
    angle: values.ValueSpec = 0,
    left_handed: bool = False,
    subtractive: bool = False,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Sweep a profile along a helix (AdditiveHelix, or SubtractiveHelix for a groove): springs,
    cable guides, custom threads. ``height`` or ``turns`` sets the length, ``angle`` tapers it.

    The profile sits beside the axis in a plane that contains the axis (e.g. a circle at x = radius
    on XZ for a spring around Z) - that is how a person draws a spring section.
    """
    doc = resolve_document(document)
    profile, body = _profile(doc, sketch)
    if (height is None) == (turns is None):
        raise validation("Give either height or turns")
    pitch_value = values.resolve(doc, pitch, "pitch")
    if pitch_value.number <= 0:
        raise validation("pitch must be positive")
    height_value = values.resolve(doc, height, "height") if height is not None else None
    turns_value = values.resolve(doc, turns, "turns") if turns is not None else None
    if (height_value or turns_value or values.Value(1.0)).number <= 0:
        raise validation("height and turns must be positive")
    reference = _revolve_axis(profile, body, axis)
    prefix = "HelixCut" if subtractive else "Helix"
    result = ToolResult()
    first = not subtractive and not _has_solid(body)
    with transaction(doc, f"{prefix}: {purpose or profile.Label}"):
        before = _volume(body.Tip) if body.Tip else 0.0
        feature = make_helix(
            body, profile, reference, pitch_value, height_value, turns_value,
            values.resolve(doc, angle, "angle"), left_handed, subtractive, prefix, purpose,
            profile.Label.removeprefix("Sketch_"),
        )  # fmt: skip
        profile.Visibility = False
        if subtractive:
            _ensure_cuts(doc, feature, before, result)
        _finish(doc, feature, result)
    if first:
        _show_first_base_feature(doc, feature, result)
    return result


# kind -> (PartDesign type suffix, required dims); sizes are diameters/extents like a person thinks
_PRIMITIVES: dict[str, tuple[str, tuple[str, ...]]] = {
    "box": ("Box", ("length", "width", "height")),
    "cylinder": ("Cylinder", ("diameter", "height")),
    "sphere": ("Sphere", ("diameter",)),
    "cone": ("Cone", ("diameter", "top_diameter", "height")),
    "ellipsoid": ("Ellipsoid", ("length", "width", "height")),
    "torus": ("Torus", ("diameter", "tube_diameter")),
    "prism": ("Prism", ("sides", "diameter", "height")),
    "wedge": ("Wedge", ("length", "width", "height", "top_length", "top_width")),
}


def _primitive_props(
    doc: Any, kind: str, dims: dict[str, values.ValueSpec]
) -> list[tuple[str, values.Value, str]]:
    """(property, value, unit) per kind. Unit '' = plain number, 'int' = integer property."""

    def full(key: str) -> values.Value:
        return values.resolve(doc, dims[key], key)

    def half(key: str) -> values.Value:
        return values.resolve(doc, f"({dims[key]}) / 2", key)

    def neg_half(key: str) -> values.Value:
        return values.resolve(doc, f"-({dims[key]}) / 2", key)

    mm = "mm"
    if kind == "box":
        return [("Length", full("length"), mm), ("Width", full("width"), mm), ("Height", full("height"), mm)]
    if kind == "cylinder":
        return [("Radius", half("diameter"), mm), ("Height", full("height"), mm)]
    if kind == "sphere":
        return [("Radius", half("diameter"), mm)]
    if kind == "cone":
        return [
            ("Radius1", half("diameter"), mm),
            ("Radius2", half("top_diameter"), mm),
            ("Height", full("height"), mm),
        ]
    if kind == "ellipsoid":  # Radius1 = Z, Radius2 = X, Radius3 = Y
        return [
            ("Radius1", half("height"), mm),
            ("Radius2", half("length"), mm),
            ("Radius3", half("width"), mm),
        ]
    if kind == "torus":
        return [("Radius1", half("diameter"), mm), ("Radius2", half("tube_diameter"), mm)]
    if kind == "prism":
        return [
            ("Polygon", full("sides"), "int"),
            ("Circumradius", half("diameter"), mm),
            ("Height", full("height"), mm),
        ]
    # wedge: X = length, Z = width, Y = height; the attachment turns Y onto the plane normal
    return [
        ("Xmin", neg_half("length"), mm), ("Xmax", half("length"), mm),
        ("Zmin", neg_half("width"), mm), ("Zmax", half("width"), mm),
        ("Ymin", values.Value(0.0), mm), ("Ymax", full("height"), mm),
        ("X2min", neg_half("top_length"), mm), ("X2max", half("top_length"), mm),
        ("Z2min", neg_half("top_width"), mm), ("Z2max", half("top_width"), mm),
    ]  # fmt: skip


def _attach(
    doc: Any,
    feature: Any,
    body: Any,
    plane: str,
    x: values.ValueSpec,
    y: values.ValueSpec,
    z: values.ValueSpec,
    rotation: Any,
    map_mode: str | None = None,
) -> None:
    """Attach a feature to an origin/datum plane with a parametric offset (like datum_plane)."""
    support, _warning, default_mode = plane_support(doc, body, plane, allow_face=False)
    feature.AttachmentSupport = [support]
    feature.MapMode = map_mode or default_mode
    offsets = [
        values.resolve(doc, spec, what) for spec, what in ((x, "center x"), (y, "center y"), (z, "offset"))
    ]
    feature.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(*(v.number for v in offsets)), rotation)
    for axis_name, value in zip("xyz", offsets, strict=True):
        if value.expression:
            feature.setExpression(f".AttachmentOffset.Base.{axis_name}", value.expression)


def _ensure_primitive_cuts(doc: Any, feature: Any, volume_before: float) -> None:
    doc.recompute()
    if feature.isValid() and volume_before - _volume(feature) > _VOLUME_TOL:
        return
    raise CoreError(
        RECOMPUTE_FAILED,
        f"'{feature.Label}' removes no material",
        {"hints": ["Move the primitive into the solid: check plane, center and offset."]},
    )


def primitive(
    kind: str,
    dims: dict[str, values.ValueSpec],
    plane: str = "XY",
    center: list[values.ValueSpec] | None = None,
    offset: values.ValueSpec = 0,
    subtractive: bool = False,
    purpose: str | None = None,
    body: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Additive or subtractive primitive (box, cylinder, sphere, cone, ellipsoid, torus, prism,
    wedge) on an origin or datum plane. ``center`` [x, y] places its reference point on the plane
    (box, wedge: footprint centre; cylinder, cone, prism: base centre; sphere, ellipsoid, torus:
    centre), ``offset`` moves it along the plane normal. Sizes are diameters and extents, numbers
    or parameters, so the primitive stays editable.
    """
    key = kind.lower()
    if key not in _PRIMITIVES:
        raise validation(f"kind must be one of {', '.join(_PRIMITIVES)}")
    type_name, required = _PRIMITIVES[key]
    missing = [name for name in required if name not in dims]
    if missing:
        raise validation(f"{key} needs dims {', '.join(required)} (missing: {', '.join(missing)})")
    position = center if center is not None else [0, 0]
    if len(position) != 2:
        raise validation("center needs [x, y] on the plane")
    doc = resolve_document(document)
    target = resolve_body(doc, body)
    props = _primitive_props(doc, key, dims)
    x, y = position
    if key == "box":  # FreeCAD's box starts at its corner; place it by the footprint centre
        x, y = f"({x}) - ({dims['length']}) / 2", f"({y}) - ({dims['width']}) / 2"
    rotation = FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 90) if key == "wedge" else FreeCAD.Rotation()
    type_id = f"PartDesign::{'Subtractive' if subtractive else 'Additive'}{type_name}"
    prefix = f"{type_name}Cut" if subtractive else type_name
    first = not subtractive and not _has_solid(target)
    result = ToolResult()
    with transaction(doc, f"{prefix}: {purpose or key}"):
        before = _volume(target.Tip) if target.Tip else 0.0
        feature = _new(
            target, type_id, prefix, purpose, "Base" if first else ("Cut" if subtractive else "Add")
        )
        for prop, value, unit in props:
            if unit == "int" and not value.expression:
                feature.setExpression(prop, None)
                setattr(feature, prop, int(value.number))
            else:
                values.apply(feature, prop, value, unit="" if unit == "int" else unit)
        _attach(doc, feature, target, plane, x, y, offset, rotation)
        if subtractive:
            _ensure_primitive_cuts(doc, feature, before)
        _finish(doc, feature, result)
    if first:
        _show_first_base_feature(doc, feature, result)
    return result


def _thread_size(feature: Any, size: str) -> str:
    options = feature.getEnumerationsOfProperty("ThreadSize")
    wanted = size.strip().upper().replace(" ", "")
    for option in options:
        normalized = option.upper()
        if normalized == wanted or normalized.startswith(f"{wanted}X"):
            return option
    raise validation(f"Unknown thread size '{size}'", available=options[:40])


def hole(
    sketch: str,
    size: str = "M3",
    cut: str = "none",
    depth: values.ValueSpec | None = None,
    threaded: bool = False,
    diameter: values.ValueSpec | None = None,
    purpose: str | None = None,
    document: str | None = None,
    cut_diameter: values.ValueSpec | None = None,
    cut_depth: values.ValueSpec | None = None,
    countersink_angle: values.ValueSpec | None = None,
    model_thread: bool = False,
) -> ToolResult:
    """ISO metric hole at every circle centre of the sketch. ``model_thread`` cuts the real thread
    geometry of a threaded hole (about 1.5 s and 60-90 faces per hole - single holes only).

    ``cut``: none | countersink | counterbore. Without ``depth`` the hole goes through all.
    ``diameter`` overrides the nominal diameter (e.g. clearance holes for printing).
    ``cut_diameter``/``cut_depth`` (counterbore) and ``cut_diameter``/``countersink_angle``
    (countersink) replace the ISO default cut values; numbers, parameters or expressions.
    """
    doc = resolve_document(document)
    profile, body = _profile(doc, sketch)
    cut_types = {"none": "None", "countersink": "Countersink", "counterbore": "Counterbore"}
    if cut not in cut_types:
        raise validation("cut must be none, countersink or counterbore")
    custom = _hole_cut_values(doc, cut, cut_diameter, cut_depth, countersink_angle)
    if model_thread and not threaded:
        raise validation("model_thread needs threaded=true")
    result = ToolResult()
    with transaction(doc, f"Hole {size}: {purpose or profile.Label}"):
        before = _volume(body.Tip) if body.Tip else 0.0
        feature = _new(body, "PartDesign::Hole", "Hole", purpose or f"{size}_{cut}", profile.Label)
        feature.Profile = profile
        feature.ThreadType = "ISOMetricProfile"
        feature.ThreadSize = _thread_size(feature, size)
        feature.Threaded = threaded
        if model_thread:
            if "ModelThread" not in feature.PropertiesList:
                raise CoreError(
                    UNSUPPORTED,
                    "This FreeCAD build cannot model thread geometry (Hole has no ModelThread)",
                    {"hints": ["Use FreeCAD 1.0 or newer, or keep the cosmetic thread."]},
                )
            feature.ModelThread = True
        feature.HoleCutType = cut_types[cut]
        if depth is None:
            feature.DepthType = "ThroughAll"
        else:
            feature.DepthType = "Dimension"
            values.apply(feature, "Depth", values.resolve(doc, depth, "depth"))
        if diameter is not None:
            values.apply(feature, "Diameter", values.resolve(doc, diameter, "diameter"))
        if custom:
            _apply_hole_cut(doc, feature, custom)
        profile.Visibility = False
        _ensure_cuts(doc, feature, before, result)
        _finish(doc, feature, result)
    if not threaded and diameter is None:
        result.hints.append(
            "For printed through holes pass 'diameter' with clearance if needed (e.g. M3 → 3.4)."
        )
    return result


_HOLE_CUT_PROPERTIES = {
    "cut_diameter": ("HoleCutDiameter", "diameter", "mm"),
    "cut_depth": ("HoleCutDepth", "depth", "mm"),
    "countersink_angle": ("HoleCutCountersinkAngle", "angle", "deg"),
}


def _hole_cut_values(
    doc: Any,
    cut: str,
    cut_diameter: values.ValueSpec | None,
    cut_depth: values.ValueSpec | None,
    countersink_angle: values.ValueSpec | None,
) -> dict[str, values.Value]:
    """Validate and resolve custom cut values before anything is created."""
    given = {
        key: value
        for key, value in (
            ("cut_diameter", cut_diameter),
            ("cut_depth", cut_depth),
            ("countersink_angle", countersink_angle),
        )
        if value is not None
    }
    if not given:
        return {}
    if cut == "none":
        raise validation(f"{', '.join(given)} need cut='counterbore' or cut='countersink'")
    if cut == "counterbore" and "countersink_angle" in given:
        raise validation("countersink_angle only applies to cut='countersink'")
    if cut == "countersink" and "cut_depth" in given:
        raise validation(
            "cut_depth only applies to cut='counterbore'; a countersink uses cut_diameter and angle"
        )
    return {key: values.resolve(doc, value, _HOLE_CUT_PROPERTIES[key][1]) for key, value in given.items()}


def _apply_hole_cut(doc: Any, feature: Any, custom: dict[str, values.Value]) -> None:
    feature.HoleCutCustomValues = True
    hole_diameter = feature.Diameter.Value
    if "cut_diameter" in custom and custom["cut_diameter"].number <= hole_diameter:
        raise validation(
            f"cut_diameter {custom['cut_diameter'].number:g} mm must be larger than the hole diameter "
            f"{hole_diameter:g} mm"
        )
    for key, value in custom.items():
        prop, _, unit = _HOLE_CUT_PROPERTIES[key]
        values.apply(feature, prop, value, unit=unit)


def _dress_up(
    type_id: str,
    prefix: str,
    selector: str,
    body_ref: str | None,
    purpose: str | None,
    document: str | None,
    configure: Any,
) -> ToolResult:
    doc = resolve_document(document)
    body = resolve_body(doc, body_ref)
    base = body.Tip
    if base is None or base.Shape.isNull():
        raise validation("The body has no geometry yet")
    names = select.resolve(base.Shape, selector, single=False, doc=doc)
    result = ToolResult()
    with transaction(doc, f"{prefix}: {purpose or selector}"):
        feature = _new(body, type_id, prefix, purpose, selector.split(":", 1)[1].replace(",", " "))
        feature.Base = (base, names)
        select.remember(feature, selector)
        configure(doc, feature)
        _finish(doc, feature, result)
    result.data["selected"] = names
    return result


def fillet(
    selector: str = "edges:top",
    radius: values.ValueSpec = 1,
    body: str | None = None,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    def configure(doc: Any, feature: Any) -> None:
        values.apply(feature, "Radius", values.resolve(doc, radius, "radius"))

    return _dress_up("PartDesign::Fillet", "Fillet", selector, body, purpose, document, configure)


def chamfer(
    selector: str = "edges:bottom",
    size: values.ValueSpec = 0.5,
    body: str | None = None,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    def configure(doc: Any, feature: Any) -> None:
        values.apply(feature, "Size", values.resolve(doc, size, "size"))

    return _dress_up("PartDesign::Chamfer", "Chamfer", selector, body, purpose, document, configure)


def shell(
    selector: str = "face:top",
    thickness: values.ValueSpec = 2,
    outward: bool = False,
    body: str | None = None,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Hollow the body; the selected faces become the openings (Thickness feature)."""

    def configure(doc: Any, feature: Any) -> None:
        values.apply(feature, "Value", values.resolve(doc, thickness, "thickness"))
        feature.Reversed = outward
        feature.Join = "Intersection"

    return _dress_up("PartDesign::Thickness", "Shell", selector, body, purpose, document, configure)


def _occurrences(doc: Any, feature: Any, count: values.ValueSpec, what: str = "count") -> None:
    occurrences = values.resolve(doc, count, what)
    if occurrences.number < 2 or occurrences.number != int(occurrences.number):
        raise validation(f"{what} must be a whole number >= 2")
    if occurrences.expression:
        feature.setExpression("Occurrences", occurrences.expression)
    else:
        feature.Occurrences = int(occurrences.number)


def _linear(
    doc: Any,
    body: Any,
    feature: Any,
    direction: str,
    length: values.ValueSpec,
    count: values.ValueSpec,
    suffix: str = "",
) -> None:
    feature.Direction = (origin_feature(body, direction), [""])
    values.apply(feature, "Length", values.resolve(doc, length, f"length{suffix}"))
    _occurrences(doc, feature, count, f"count{suffix}")


def pattern(
    features: list[str],
    kind: str,
    plane: str = "YZ",
    direction: str = "X",
    axis: str = "Z",
    length: values.ValueSpec = 20,
    angle: values.ValueSpec = 360,
    count: values.ValueSpec = 2,
    direction2: str = "Y",
    length2: values.ValueSpec = 20,
    count2: values.ValueSpec = 2,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Pattern existing features.

    ``mirrored`` (``plane``), ``linear`` (``direction``, ``length`` = total extent, ``count``),
    ``polar`` (``axis``, ``angle``, ``count``) or ``grid`` – a 2D raster as one MultiTransform
    with two linear patterns (``direction``/``length``/``count`` and ``direction2``/``length2``/
    ``count2``). PartDesign cannot pattern a pattern, so rasters must use ``grid``.
    """
    doc = resolve_document(document)
    if not features:
        raise validation("features must not be empty")
    originals = [resolve_object(doc, ref) for ref in features]
    body = body_of(originals[0])
    kinds = {
        "mirrored": ("PartDesign::Mirrored", "Mirrored"),
        "linear": ("PartDesign::LinearPattern", "LinearPattern"),
        "polar": ("PartDesign::PolarPattern", "PolarPattern"),
        "grid": ("PartDesign::MultiTransform", "Grid"),
    }
    if kind not in kinds:
        raise validation("kind must be mirrored, linear, polar or grid")
    transformed = [o.Label for o in originals if o.TypeId in {t for t, _ in kinds.values()}]
    if transformed:
        raise validation(
            f"PartDesign cannot compute a pattern of a pattern ({', '.join(transformed)}) - "
            "for rasters use kind='grid' on the original feature"
        )
    type_id, prefix = kinds[kind]
    result = ToolResult()
    with transaction(doc, f"{prefix}: {', '.join(o.Label for o in originals)}"):
        feature = _new(body, type_id, prefix, purpose, "_".join(o.Label for o in originals))
        steps = []
        if kind == "grid":
            # Like FreeCAD's MultiTransform task panel: the steps stay in the body (with empty
            # Originals they are no solid features, so neither Tip nor base chain), the
            # MultiTransform claims them in the tree and only the MultiTransform is shown.
            for suffix, (axis_name, extent, number) in (
                ("X", (direction, length, count)),
                ("Y", (direction2, length2, count2)),
            ):
                step = body.newObject("PartDesign::LinearPattern", "LinearPattern")
                step.Label = naming.make_label(doc, "LinearPattern", f"{feature.Label}_{suffix}")
                _linear(doc, body, step, axis_name, extent, number, "" if suffix == "X" else "2")
                steps.append(step)
            feature.Originals = originals
            feature.Transformations = steps
        else:
            feature.Originals = originals
        # body.newObject does not make a transformed feature the tip; without this the next feature
        # would be inserted before this pattern (a second pattern then silently loses the first one).
        body.Tip = feature
        if kind == "mirrored":
            feature.MirrorPlane = (origin_feature(body, plane), [""])
        elif kind == "linear":
            _linear(doc, body, feature, direction, length, count)
        elif kind == "polar":
            feature.Axis = _axis_reference(body, axis)
            values.apply(feature, "Angle", values.resolve(doc, angle, "angle"), unit="deg")
            _occurrences(doc, feature, count)
        # every newObject in the GUI hides the rest of the body, so the visibility is set last
        display.show_only(feature, [*originals, *steps])
        _finish(doc, feature, result)
    return result


def datum_plane(
    base: str = "XY",
    offset: values.ValueSpec = 0,
    angle: values.ValueSpec = 0,
    rotation_axis: str = "X",
    body: str | None = None,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Datum plane parallel to an origin plane (``offset``), optionally tilted by ``angle``."""
    doc = resolve_document(document)
    target = resolve_body(doc, body)
    axes = {"X": FreeCAD.Vector(1, 0, 0), "Y": FreeCAD.Vector(0, 1, 0), "Z": FreeCAD.Vector(0, 0, 1)}
    if rotation_axis.upper() not in axes:
        raise validation("rotation_axis must be X, Y or Z")
    result = ToolResult()
    with transaction(doc, f"Datum plane: {purpose or base}"):
        plane = target.newObject("PartDesign::Plane", "DatumPlane")
        plane.Label = naming.make_label(doc, "DatumPlane", purpose or f"{base}_Offset")
        plane.AttachmentSupport = [(origin_feature(target, base), "")]
        plane.MapMode = "FlatFace"
        offset_value = values.resolve(doc, offset, "offset")
        angle_value = values.resolve(doc, angle, "angle")
        plane.AttachmentOffset = FreeCAD.Placement(
            FreeCAD.Vector(0, 0, offset_value.number),
            FreeCAD.Rotation(axes[rotation_axis.upper()], angle_value.number),
        )
        if offset_value.expression:
            plane.setExpression(".AttachmentOffset.Base.z", offset_value.expression)
        if angle_value.expression:
            plane.setExpression(".AttachmentOffset.Rotation.Angle", angle_value.expression)
        result.add_created(plane)
    result.data["plane"] = describe(plane)
    result.hints.append(f"create_sketch(plane='{plane.Label}') puts a sketch on this plane.")
    return result


# kind -> (type, label prefix, attachment mode on the base plane)
_DATUMS = {
    "point": ("PartDesign::Point", "DatumPoint", "ObjectOrigin"),
    "line": ("PartDesign::Line", "DatumLine", "ObjectZ"),
    "lcs": ("PartDesign::CoordinateSystem", "LCS", "ObjectXY"),
}


def datum(
    kind: str,
    base: str = "XY",
    offset: list[values.ValueSpec] | None = None,
    angle: values.ValueSpec = 0,
    rotation_axis: str = "X",
    body: str | None = None,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Datum point, datum line or local coordinate system (LCS) as a stable, parametric reference.

    ``offset`` [x, y, z] is measured in the base plane (x, y in the plane, z along its normal),
    ``angle`` tilts about ``rotation_axis``. A line runs along the normal of ``base`` (XY → Z,
    XZ → Y, YZ → X). Sketches accept an LCS as ``plane``; revolve, pattern (polar) and helix
    accept a datum line as ``axis``.
    """
    key = kind.lower()
    if key not in _DATUMS:
        raise validation("kind must be point, line or lcs")
    type_id, prefix, map_mode = _DATUMS[key]
    position = offset if offset is not None else [0, 0, 0]
    if len(position) != 3:
        raise validation("offset needs [x, y, z] relative to the base plane")
    axes = {"X": FreeCAD.Vector(1, 0, 0), "Y": FreeCAD.Vector(0, 1, 0), "Z": FreeCAD.Vector(0, 0, 1)}
    if rotation_axis.upper() not in axes:
        raise validation("rotation_axis must be X, Y or Z")
    doc = resolve_document(document)
    target = resolve_body(doc, body)
    angle_value = values.resolve(doc, angle, "angle")
    rotation = FreeCAD.Rotation(axes[rotation_axis.upper()], angle_value.number)
    result = ToolResult()
    with transaction(doc, f"{prefix}: {purpose or base}"):
        feature = target.newObject(type_id, prefix)
        feature.Label = naming.make_label(doc, prefix, purpose or f"{base}_{key}")
        x, y, z = position
        _attach(doc, feature, target, base, x, y, z, rotation, map_mode=map_mode)
        if angle_value.expression:
            feature.setExpression(".AttachmentOffset.Rotation.Angle", angle_value.expression)
        doc.recompute()
        result.add_created(feature)
    result.data["datum"] = describe(feature)
    hints = {
        "point": "Reference it as external geometry in a sketch (add_geometry type='external').",
        "line": f"revolve/helix(axis='{feature.Label}') or pattern(kind='polar', axis='{feature.Label}').",
        "lcs": f"create_sketch(plane='{feature.Label}') puts a sketch on its XY plane.",
    }
    result.hints.append(hints[key])
    return result
