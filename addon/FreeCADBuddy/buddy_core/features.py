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
from buddy_core.errors import RECOMPUTE_FAILED, CoreError, validation
from buddy_core.result import ToolResult, describe
from buddy_core.sketch.model import resolve_sketch
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
            f"'{feature.Label}' erzeugt {len(shape.Solids)} getrennte Körper",
            {"hints": ["Profil muss den bestehenden Körper berühren oder überlappen."]},
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
            f"Richtung von '{feature.Label}' automatisch umgekehrt (entfernte sonst nichts)."
        )
        return
    raise CoreError(
        RECOMPUTE_FAILED,
        f"'{feature.Label}' entfernt in keiner Richtung Material",
        {"hints": ["Skizzenlage und Tiefe prüfen: Profil muss den Körper überdecken."]},
    )


def pad(
    sketch: str,
    length: values.ValueSpec = 10,
    mode: str = "length",
    length2: values.ValueSpec | None = None,
    reversed: bool = False,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Extrude a closed profile. ``mode``: length | symmetric | two_sides | up_to_last."""
    doc = resolve_document(document)
    profile, body = _profile(doc, sketch)
    result = ToolResult()
    first = not _has_solid(body)
    with transaction(doc, f"Pad: {purpose or profile.Label}"):
        feature = _new(body, "PartDesign::Pad", "Pad", purpose, profile.Label.removeprefix("Sketch_"))
        feature.Profile = profile
        feature.Reversed = reversed
        if mode == "up_to_last":
            feature.Type = "UpToLast"
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
                raise validation("mode muss length, symmetric, two_sides oder up_to_last sein")
        profile.Visibility = False
        _finish(doc, feature, result)
    if first:
        _show_first_base_feature(doc, feature, result)
    return result


def pocket(
    sketch: str,
    depth: values.ValueSpec = 5,
    mode: str = "length",
    reversed: bool = False,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Cut a closed profile into the body. ``mode``: length | symmetric | through_all."""
    doc = resolve_document(document)
    profile, body = _profile(doc, sketch)
    result = ToolResult()
    with transaction(doc, f"Pocket: {purpose or profile.Label}"):
        before = _volume(body.Tip) if body.Tip else 0.0
        feature = _new(body, "PartDesign::Pocket", "Pocket", purpose, profile.Label.removeprefix("Sketch_"))
        feature.Profile = profile
        feature.Reversed = reversed
        if mode == "through_all":
            feature.Type = "ThroughAll"
        else:
            values.apply(feature, "Length", values.resolve(doc, depth, "depth"))
            if mode == "symmetric":
                feature.SideType = "Symmetric"
            elif mode != "length":
                raise validation("mode muss length, symmetric oder through_all sein")
        profile.Visibility = False
        _ensure_cuts(doc, feature, before, result)
        _finish(doc, feature, result)
    return result


def _revolve_axis(sketch: Any, body: Any, axis: str) -> tuple[Any, list[str]]:
    key = axis.upper()
    if key in ("V_AXIS", "H_AXIS"):
        return sketch, [key.replace("_AXIS", "_Axis")]
    if key in ("X", "Y", "Z"):
        return origin_feature(body, key), [""]
    raise validation("axis muss V_Axis, H_Axis (Skizzenachsen) oder X/Y/Z (Body-Achsen) sein")


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
        raise validation("Profil und Pfad müssen im selben Body liegen")
    edges = spine.Shape.Edges if not spine.Shape.isNull() else []
    if not edges:
        raise validation(f"Pfad '{spine.Label}' enthält keine Kanten")
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


def _thread_size(feature: Any, size: str) -> str:
    options = feature.getEnumerationsOfProperty("ThreadSize")
    wanted = size.strip().upper().replace(" ", "")
    for option in options:
        normalized = option.upper()
        if normalized == wanted or normalized.startswith(f"{wanted}X"):
            return option
    raise validation(f"Unbekannte Gewindegröße '{size}'", available=options[:40])


def hole(
    sketch: str,
    size: str = "M3",
    cut: str = "none",
    depth: values.ValueSpec | None = None,
    threaded: bool = False,
    diameter: values.ValueSpec | None = None,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """ISO metric hole at every circle centre of the sketch.

    ``cut``: none | countersink | counterbore. Without ``depth`` the hole goes through all.
    ``diameter`` overrides the nominal diameter (e.g. clearance holes for printing).
    """
    doc = resolve_document(document)
    profile, body = _profile(doc, sketch)
    cut_types = {"none": "None", "countersink": "Countersink", "counterbore": "Counterbore"}
    if cut not in cut_types:
        raise validation("cut muss none, countersink oder counterbore sein")
    result = ToolResult()
    with transaction(doc, f"Bohrung {size}: {purpose or profile.Label}"):
        before = _volume(body.Tip) if body.Tip else 0.0
        feature = _new(body, "PartDesign::Hole", "Hole", purpose or f"{size}_{cut}", profile.Label)
        feature.Profile = profile
        feature.ThreadType = "ISOMetricProfile"
        feature.ThreadSize = _thread_size(feature, size)
        feature.Threaded = threaded
        feature.HoleCutType = cut_types[cut]
        if depth is None:
            feature.DepthType = "ThroughAll"
        else:
            feature.DepthType = "Dimension"
            values.apply(feature, "Depth", values.resolve(doc, depth, "depth"))
        if diameter is not None:
            values.apply(feature, "Diameter", values.resolve(doc, diameter, "diameter"))
        profile.Visibility = False
        _ensure_cuts(doc, feature, before, result)
        _finish(doc, feature, result)
    if not threaded and diameter is None:
        result.hints.append(
            "Für gedruckte Durchgangsbohrungen ggf. 'diameter' mit Spiel angeben (z. B. M3 → 3.4)."
        )
    return result


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
        raise validation("Body hat noch keine Geometrie")
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
        raise validation(f"{what} muss eine ganze Zahl >= 2 sein")
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
        raise validation("features darf nicht leer sein")
    originals = [resolve_object(doc, ref) for ref in features]
    body = body_of(originals[0])
    kinds = {
        "mirrored": ("PartDesign::Mirrored", "Mirrored"),
        "linear": ("PartDesign::LinearPattern", "LinearPattern"),
        "polar": ("PartDesign::PolarPattern", "PolarPattern"),
        "grid": ("PartDesign::MultiTransform", "Grid"),
    }
    if kind not in kinds:
        raise validation("kind muss mirrored, linear, polar oder grid sein")
    transformed = [o.Label for o in originals if o.TypeId in {t for t, _ in kinds.values()}]
    if transformed:
        raise validation(
            f"Muster auf Muster ({', '.join(transformed)}) kann PartDesign nicht berechnen – "
            "für Raster kind='grid' auf das Ausgangsfeature verwenden"
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
            feature.Axis = (origin_feature(body, axis), [""])
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
        raise validation("rotation_axis muss X, Y oder Z sein")
    result = ToolResult()
    with transaction(doc, f"Bezugsebene: {purpose or base}"):
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
    result.hints.append(f"create_sketch(plane='{plane.Label}') legt eine Skizze auf diese Ebene.")
    return result
