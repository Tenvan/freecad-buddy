"""Export the print target to STL, 3MF, or STEP; verifies the file by reimporting it."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import FreeCAD
import Mesh
import MeshPart
import Part

from buddy_core import naming
from buddy_core.errors import UNSUPPORTED, CoreError, validation
from buddy_core.printing.check import resolve_target
from buddy_core.printing.profile import PrinterProfile, get_printer_profile

_EXTENSIONS = {"stl": "stl", "3mf": "3mf", "step": "step"}


def _export_filename(doc: Any, obj: Any, extension: str) -> str:
    return f"{naming.sanitize(doc.Label)}_{naming.sanitize(obj.Label)}.{extension}"


def _resolve_path(path: str | None, doc: Any, obj: Any, extension: str) -> Path:
    if path is None:
        if not doc.FileName:
            raise validation("Document was never saved: pass 'path' or call document(action='save') first.")
        return Path(doc.FileName).parent / "export" / _export_filename(doc, obj, extension)
    candidate = Path(path)
    is_directory = candidate.is_dir() or path.endswith(("/", "\\")) or candidate.suffix == ""
    if is_directory:
        return candidate / _export_filename(doc, obj, extension)
    allowed = (".stp", ".step") if extension == "step" else (f".{extension}",)
    if candidate.suffix.lower() not in allowed:
        raise validation(
            f"File extension '{candidate.suffix}' does not match the format '{extension}' (expected: {', '.join(allowed)})"
        )
    return candidate


def _place_on_bed(shape: Any) -> None:
    box = shape.BoundBox
    center_x, center_y = (box.XMin + box.XMax) / 2, (box.YMin + box.YMax) / 2
    shape.translate(FreeCAD.Vector(-center_x, -center_y, -box.ZMin))


def _write_mesh(shape: Any, target: Path, format_name: str, profile: PrinterProfile) -> None:
    mesh = MeshPart.meshFromShape(
        Shape=shape,
        LinearDeflection=profile.mesh_linear_deflection,
        AngularDeflection=math.radians(profile.mesh_angular_deflection_deg),
    )
    try:
        mesh.write(str(target))
    except Exception as error:
        raise CoreError(
            UNSUPPORTED,
            f"Export as '{format_name}' is not supported by this FreeCAD version: {error}",
        ) from error


def export_body(
    format: str,
    target: str | None = None,
    path: str | None = None,
    place_on_bed: bool = True,
    document: str | None = None,
    profile_path: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    format_name = format.lower()
    extension = _EXTENSIONS.get(format_name)
    if extension is None:
        raise validation(f"Unknown format '{format}' (allowed: {', '.join(_EXTENSIONS)})")

    doc, obj = resolve_target(target, document)
    shape = obj.Shape.copy()  # never touch the model itself
    volume_model = shape.Volume if shape.Solids else 0.0

    if place_on_bed:
        _place_on_bed(shape)

    profile_dict = get_printer_profile(profile_path)
    profile = PrinterProfile(**{key: value for key, value in profile_dict.items() if key != "path"})

    target_path = _resolve_path(path, doc, obj, extension)
    if target_path.exists() and not overwrite:
        raise validation(f"File '{target_path}' already exists - set overwrite=true to replace it")
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if extension == "step":
        shape.exportStep(str(target_path))
        volume_file = Part.read(str(target_path)).Volume
    else:
        _write_mesh(shape, target_path, format_name, profile)
        volume_file = Mesh.Mesh(str(target_path)).Volume

    deviation_percent = abs(volume_file - volume_model) / volume_model * 100 if volume_model else 0.0
    warnings: list[str] = []
    if deviation_percent > 1.0:
        warnings.append(
            f"Volume deviation after re-import: {deviation_percent:.2f} % "
            f"(model {volume_model:.2f} mm³, file {volume_file:.2f} mm³)."
        )

    return {
        "ok": True,
        "path": str(target_path),
        "format": format_name,
        "volume_model": volume_model,
        "volume_file": volume_file,
        "deviation_percent": deviation_percent,
        "placed_on_bed": place_on_bed,
        "warnings": warnings,
    }
