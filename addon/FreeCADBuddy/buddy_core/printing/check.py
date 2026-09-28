"""Printability checks (build volume, overhangs, thin walls, tiny features). Read-only."""

from __future__ import annotations

import math
from typing import Any

import Part

from buddy_core.body import resolve_body
from buddy_core.documents import resolve_document, resolve_object
from buddy_core.errors import validation
from buddy_core.printing.profile import PrinterProfile, get_printer_profile
from buddy_core.result import describe

_MAX_WALL_SAMPLES = 300
_RAY_OFFSET = 1e-4
_RAY_HIT_TOLERANCE = 1e-3


def resolve_target(target: str | None, document: str | None) -> tuple[Any, Any]:
    """Document + object with a non-empty ``Shape`` (default: the document's single body)."""
    doc = resolve_document(document)
    if target:
        obj = resolve_object(doc, target)
        shape = getattr(obj, "Shape", None)
        if shape is None or shape.isNull():
            raise validation(f"'{obj.Label}' hat keine Shape")
        return doc, obj
    return doc, resolve_body(doc)


def _flip(vector: Any) -> Any:
    return vector * -1


def _face_point_normal(face: Any, fu: float, fv: float) -> tuple[Any, Any]:
    """Surface point and outward normal at the fractional parameter position (fu, fv).

    ``Face.normalAt`` already returns the outward normal for solid faces in this FreeCAD/OCC
    build, for both ``Forward`` and ``Reversed`` faces alike (verified empirically against
    ``Shape.isInside``); an additional flip on ``Reversed`` -- the textbook OCC rule -- was
    tested and turns out to invert otherwise-correct normals here, so it is deliberately not
    applied.
    """
    u1, u2, v1, v2 = face.ParameterRange
    u, v = u1 + fu * (u2 - u1), v1 + fv * (v2 - v1)
    point = face.valueAt(u, v)
    normal = face.normalAt(u, v)
    return point, normal


def _check_overhang(shape: Any, profile: PrinterProfile) -> dict[str, Any] | None:
    box = shape.BoundBox
    size_metric = max(box.XLength, box.YLength, box.ZLength)
    bed_tolerance = max(size_metric * 1e-6, 1e-4)
    threshold_deg = 90.0 - profile.overhang_angle
    faces: list[str] = []
    area = 0.0
    for index, face in enumerate(shape.Faces):
        if abs(face.BoundBox.ZMin - box.ZMin) <= bed_tolerance:
            continue  # bed contact, not an overhang
        _, normal = _face_point_normal(face, 0.5, 0.5)
        if normal.z >= 0:
            continue
        angle_deg = math.degrees(math.acos(max(-1.0, min(1.0, -normal.z / normal.Length))))
        if angle_deg < threshold_deg:
            faces.append(f"Face{index + 1}")
            area += face.Area
    if not faces:
        return None
    total_area = shape.Area or 1.0
    ratio = area / total_area
    return {
        "severity": "warning",
        "code": "overhang",
        "message": (
            f"{len(faces)} Fläche(n) mit insgesamt {area:.1f} mm² ({ratio * 100:.1f} % der Oberfläche) "
            f"überschreiten den Überhangwinkel von {profile.overhang_angle:g}°."
        ),
        "faces": faces,
        "value": {"area": area, "ratio": ratio},
    }


def _sample_points(shape: Any, max_samples: int = _MAX_WALL_SAMPLES) -> list[tuple[Any, Any, str]]:
    """Face-center samples plus extra interior points on faces larger than average."""
    faces = shape.Faces
    if not faces:
        return []
    mean_area = sum(face.Area for face in faces) / len(faces)
    samples: list[tuple[Any, Any, str]] = []
    for index, face in enumerate(faces):
        name = f"Face{index + 1}"
        fractions = [(0.5, 0.5)]
        if face.Area > mean_area * 2:
            fractions += [(0.25, 0.25), (0.25, 0.75), (0.75, 0.25), (0.75, 0.75)]
        for fu, fv in fractions:
            if len(samples) >= max_samples:
                return samples
            point, normal = _face_point_normal(face, fu, fv)
            samples.append((point, normal, name))
    return samples


def _wall_thickness(solid: Any, point: Any, normal: Any, ray_length: float) -> float | None:
    inward = _flip(normal)
    start = point + inward * _RAY_OFFSET
    end = start + inward * ray_length
    if start.distanceToPoint(end) < 1e-9:
        return None
    try:
        common = solid.common(Part.LineSegment(start, end).toShape())
    except Part.OCCError:
        return None
    hits = [
        edge.Length
        for edge in common.Edges
        if any(vertex.Point.distanceToPoint(point) <= _RAY_HIT_TOLERANCE for vertex in edge.Vertexes)
    ]
    return min(hits) if hits else None


def _check_thin_walls(solid: Any, profile: PrinterProfile) -> tuple[float | None, list[str]]:
    ray_length = solid.BoundBox.DiagonalLength
    min_thickness: float | None = None
    thin_faces: list[str] = []
    for point, normal, face_name in _sample_points(solid):
        thickness = _wall_thickness(solid, point, normal, ray_length)
        if thickness is None:
            continue
        if min_thickness is None or thickness < min_thickness:
            min_thickness = thickness
        if thickness < profile.min_wall and face_name not in thin_faces:
            thin_faces.append(face_name)
    return min_thickness, thin_faces


def _check_small_features(shape: Any, profile: PrinterProfile) -> list[dict[str, Any]]:
    small_circular: list[str] = []
    small_straight: list[str] = []
    for index, edge in enumerate(shape.Edges):
        name = f"Edge{index + 1}"
        curve = edge.Curve
        if isinstance(curve, Part.Circle) and curve.Radius < profile.nozzle:
            small_circular.append(name)
        elif isinstance(curve, Part.Line) and edge.Length < profile.nozzle:
            small_straight.append(name)
    if not small_circular and not small_straight:
        return []
    parts = []
    if small_circular:
        parts.append(f"{len(small_circular)} runde Kante(n) mit Radius unter Düse ({profile.nozzle:g} mm)")
    if small_straight:
        parts.append(f"{len(small_straight)} gerade Kante(n) kürzer als die Düse ({profile.nozzle:g} mm)")
    return [
        {
            "severity": "info",
            "code": "small_feature",
            "message": "Details unterhalb der Düsengröße: " + ", ".join(parts) + ".",
            "faces": small_circular + small_straight,
        }
    ]


def check_printability(
    target: str | None = None,
    document: str | None = None,
    profile_path: str | None = None,
) -> dict[str, Any]:
    _, obj = resolve_target(target, document)
    shape = obj.Shape
    profile_dict = get_printer_profile(profile_path)
    profile = PrinterProfile(**{key: value for key, value in profile_dict.items() if key != "path"})

    issues: list[dict[str, Any]] = []

    if not shape.isValid():
        issues.append(
            {
                "severity": "error",
                "code": "invalid_shape",
                "message": "Shape ist nicht gültig (Geometrie-/Topologiefehler).",
            }
        )

    solids = shape.Solids
    if not solids:
        issues.append(
            {"severity": "error", "code": "no_solid", "message": "Shape enthält keinen Volumenkörper."}
        )
    elif len(solids) > 1:
        issues.append(
            {
                "severity": "error",
                "code": "multiple_solids",
                "message": f"Shape enthält {len(solids)} getrennte Volumenkörper statt eines einzelnen.",
                "value": len(solids),
            }
        )

    unclosed = sum(1 for shell in shape.Shells if not shell.isClosed())
    if unclosed:
        issues.append(
            {
                "severity": "error",
                "code": "not_closed",
                "message": f"{unclosed} Schale(n) sind nicht geschlossen (offene Kanten/Löcher).",
                "value": unclosed,
            }
        )

    box = shape.BoundBox
    size = [box.XLength, box.YLength, box.ZLength]
    if size[0] > profile.build_x or size[1] > profile.build_y or size[2] > profile.build_z:
        issues.append(
            {
                "severity": "error",
                "code": "build_volume",
                "message": (
                    f"Bauteil ({size[0]:.1f} x {size[1]:.1f} x {size[2]:.1f} mm) passt nicht in den Bauraum "
                    f"({profile.build_x:.1f} x {profile.build_y:.1f} x {profile.build_z:.1f} mm)."
                ),
                "value": size,
            }
        )

    overhang_issue = _check_overhang(shape, profile)
    if overhang_issue:
        issues.append(overhang_issue)

    min_wall_sampled: float | None = None
    if len(solids) == 1:
        min_wall_sampled, thin_faces = _check_thin_walls(solids[0], profile)
        if min_wall_sampled is not None and min_wall_sampled < profile.min_wall:
            issues.append(
                {
                    "severity": "warning",
                    "code": "thin_wall",
                    "message": (
                        f"Minimale gemessene Wandstärke {min_wall_sampled:.2f} mm liegt unter dem Minimum "
                        f"von {profile.min_wall:g} mm."
                    ),
                    "faces": thin_faces,
                    "value": min_wall_sampled,
                }
            )

    issues.extend(_check_small_features(shape, profile))

    stats = {
        "volume": shape.Volume if solids else 0.0,
        "size": size,
        "overhang_area": overhang_issue["value"]["area"] if overhang_issue else 0.0,
        "overhang_ratio": overhang_issue["value"]["ratio"] if overhang_issue else 0.0,
        "min_wall_sampled": min_wall_sampled,
    }

    return {
        "ok": not any(issue["severity"] == "error" for issue in issues),
        "target": describe(obj),
        "issues": issues,
        "hints": design_hints(issues, profile),
        "stats": stats,
        "profile": profile_dict,
    }


_HINTS: dict[str, str] = {
    "overhang": (
        "Überhänge: Fasen mit ≤ {overhang_angle:g}° statt waagrechter Unterseiten/Verrundungen, "
        "Bauteil drehen oder Stützstruktur einplanen."
    ),
    "thin_wall": "Wandstärke als Parameter ≥ {min_wall:g} mm (2 × Düse) setzen, z. B. Wall im VarSet.",
    "small_feature": "Details unter {nozzle:g} mm werden nicht sauber gedruckt – vergrößern oder entfernen.",
    "build_volume": "Bauteil teilen oder drehen; Bauraum {build_x:g} × {build_y:g} × {build_z:g} mm.",
    "multiple_solids": "Getrennte Körper verbinden oder als eigene Bodies modellieren.",
}
_GENERAL_HINTS = (
    "Unterkante fasen (chamfer edges:bottom, ~0.4 mm) statt verrunden – gegen Elefantenfuß.",
    "Passungen mit Spiel {clearance_fit:g} mm (Pressung {press_fit:g} mm) als Parameter modellieren; "
    "Durchgangsbohrungen ca. +0.4 mm größer (M3 → 3.4).",
)


def design_hints(issues: list[dict[str, Any]], profile: PrinterProfile) -> list[str]:
    """Actionable design advice for the agent, derived from the findings and the printer profile."""
    values = vars(profile)
    codes = {issue["code"] for issue in issues}
    hints = [template.format(**values) for code, template in _HINTS.items() if code in codes]
    hints.extend(template.format(**values) for template in _GENERAL_HINTS)
    return hints
