"""Material (FreeCAD material library) and appearance (display colour) of bodies and parts."""

from __future__ import annotations

from typing import Any

import FreeCAD

from buddy_core.documents import resolve_document, resolve_object
from buddy_core.errors import not_found, validation
from buddy_core.result import ToolResult, describe
from buddy_core.transaction import transaction

COLORS: dict[str, tuple[float, float, float]] = {
    "red": (0.8, 0.1, 0.1),
    "orange": (0.95, 0.5, 0.1),
    "yellow": (0.95, 0.8, 0.1),
    "green": (0.2, 0.6, 0.2),
    "blue": (0.15, 0.35, 0.8),
    "purple": (0.5, 0.2, 0.7),
    "white": (0.95, 0.95, 0.95),
    "grey": (0.55, 0.55, 0.55),
    "gray": (0.55, 0.55, 0.55),
    "black": (0.1, 0.1, 0.1),
}


def parse_color(color: str | list[float]) -> tuple[float, float, float]:
    """Colour name, '#RRGGBB' or [r, g, b] (0-1 or 0-255)."""
    if isinstance(color, str):
        text = color.strip().lower()
        if text in COLORS:
            return COLORS[text]
        if text.startswith("#") and len(text) == 7:
            try:
                return tuple(int(text[i : i + 2], 16) / 255 for i in (1, 3, 5))  # type: ignore[return-value]
            except ValueError:
                pass
        raise validation(f"Unknown colour '{color}': use {', '.join(COLORS)}, '#RRGGBB' or [r, g, b]")
    if len(color) != 3:
        raise validation("Colour as a list needs exactly three values [r, g, b]")
    values = [float(v) for v in color]
    scale = 255.0 if max(values) > 1 else 1.0
    return tuple(min(max(v / scale, 0.0), 1.0) for v in values)  # type: ignore[return-value]


def find_material(name: str) -> Any:
    """Library material by UUID, exact name or short name ('PLA' -> 'PLA-Generic'), case-insensitive."""
    import Materials

    materials = Materials.MaterialManager().Materials
    if name in materials:
        return materials[name]
    wanted = name.strip().lower()
    by_name = {m.Name.lower(): m for m in materials.values()}
    for candidate in (wanted, f"{wanted}-generic"):
        if candidate in by_name:
            return by_name[candidate]
    close = sorted(m.Name for m in materials.values() if wanted in m.Name.lower())
    raise not_found(f"Material '{name}' not found in the material library", candidates=close[:15])


def _density(material: Any) -> float | None:
    """Density in g/cm³, if the material defines one."""
    try:
        value = material.getPhysicalValue("Density")
    except Exception:
        return None
    if value is None:
        return None
    quantity = value if hasattr(value, "getValueAs") else FreeCAD.Units.Quantity(str(value))
    return float(quantity.getValueAs("g/cm^3"))


def set_material(
    target: str,
    material: str | None = None,
    color: str | list[float] | None = None,
    document: str | None = None,
) -> ToolResult:
    """Assign a library material (physical properties, e.g. for mass) and/or a display colour."""
    if material is None and color is None:
        raise validation("Pass material and/or color")
    doc = resolve_document(document)
    obj = resolve_object(doc, target)
    result = ToolResult()
    rgb = parse_color(color) if color is not None else None
    with transaction(doc, f"Material: {obj.Label}"):
        if material is not None:
            if not hasattr(obj, "ShapeMaterial"):
                raise validation(f"'{obj.Label}' ({obj.TypeId}) cannot carry a material")
            found = find_material(material)
            obj.ShapeMaterial = found
            density = _density(found)
            info: dict[str, Any] = {"name": found.Name, "uuid": found.UUID, "density_g_cm3": density}
            shape = getattr(obj, "Shape", None)
            if density is not None and shape is not None and shape.Solids:
                info["mass_g"] = round(shape.Volume / 1000 * density, 2)
            result.data["material"] = info
        if rgb is not None:
            view = getattr(obj, "ViewObject", None)
            if view is None:
                result.warnings.append("No GUI: the colour is only visible when FreeCAD runs with its GUI")
            else:
                view.ShapeAppearance = (FreeCAD.Material(DiffuseColor=rgb),)
            result.data["color"] = [round(c, 3) for c in rgb]
        result.add_modified(obj)
    result.data["target"] = describe(obj)
    return result
