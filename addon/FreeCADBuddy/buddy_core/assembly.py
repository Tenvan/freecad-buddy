"""Assemblies in the Assembly4 convention, fasteners (Fasteners workbench) and exploded configurations.

Assembly4 is a data convention on plain FreeCAD objects, so this module builds it directly and needs
neither the Asm4 GUI nor its modules: an ``App::Part`` named ``Assembly`` (``Type='Assembly'``) with
``LCS_Origin``, the groups ``Constraints``/``Configurations`` and a ``Variables`` container. Parts are
``App::Link`` objects whose placement is the expression ``LCS_Origin.Placement * AttachmentOffset``
(solver ``Asm4EE``); fasteners are placed the same way. Configurations are Asm4 configuration tables
(spreadsheets), so the Assembly4 "Configurations" dialog can apply them, too.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import FreeCAD

from buddy_core import naming
from buddy_core.documents import resolve_document, resolve_object
from buddy_core.errors import UNSUPPORTED, CoreError, not_found, validation
from buddy_core.result import ToolResult, describe
from buddy_core.transaction import transaction

ASSEMBLY = "Assembly"
ORIGIN_LCS = "LCS_Origin"
PLACEMENT_EXPRESSION = f"{ORIGIN_LCS}.Placement * AttachmentOffset"
PART_TYPES = ("PartDesign::Body", "App::Part")

# Assembly4 configuration table layout (configurationEngine.py, Asm4 v0.61)
CONFIG_TYPE = "Asm4::ConfigurationTable"
HEADER_CELL, DESCRIPTION_CELL, START_ROW = "A1", "A2", 5
COLUMNS = ("A", "B", "C", "D", "E", "F", "G", "H", "I")
HEADERS = ("ObjectName", "Visible", "Assembly Type", "Pos. X", "Pos. Y", "Pos. Z", "Rot. Yaw",
           "Rot. Pitch", "Rot. Roll")  # fmt: skip
ASSEMBLED = "Assembled"


def get_assembly(doc: Any, required: bool = True) -> Any:
    assembly = doc.getObject(ASSEMBLY)
    if assembly is not None and assembly.TypeId == "App::Part" and getattr(assembly, "Type", "") == ASSEMBLY:
        return assembly
    if required:
        raise not_found("No Assembly4 assembly in the document: call create_assembly first")
    return None


def _group(parent: Any, name: str) -> Any:
    group = parent.newObject("App::DocumentObjectGroup", name)
    if group.ViewObject is not None:
        group.ViewObject.Visibility = False
    return group


def create_assembly(label: str = ASSEMBLY, document: str | None = None) -> ToolResult:
    """Assembly4 container; bodies at the document root move into a 'Parts' group."""
    doc = resolve_document(document)
    if doc.getObject(ASSEMBLY) is not None:
        raise validation("The document already has an object 'Assembly': use it with add_to_assembly")
    result = ToolResult()
    with transaction(doc, f"Assembly: {label}"):
        parts = doc.getObject("Parts") or doc.addObject("App::DocumentObjectGroup", "Parts")
        for obj in list(doc.Objects):
            if obj.TypeId in PART_TYPES and obj.getParentGeoFeatureGroup() is None and obj is not parts:
                parts.addObject(obj)
        assembly = doc.addObject("App::Part", ASSEMBLY)
        assembly.Type = ASSEMBLY
        assembly.Label = label
        assembly.addProperty("App::PropertyString", "AssemblyType", "Assembly")
        assembly.AssemblyType = "Part::Link"
        lcs = assembly.newObject("PartDesign::CoordinateSystem", ORIGIN_LCS)
        lcs.AttachmentSupport = [(assembly.Origin.OriginFeatures[0], "")]
        lcs.MapMode = "ObjectXY"
        _group(assembly, "Constraints")
        variables = doc.addObject("App::FeaturePython", "Variables")
        variables.addProperty("App::PropertyString", "Type")
        variables.Type = "App::PropertyContainer"
        assembly.addObject(variables)
        _group(assembly, "Configurations")
        doc.recompute()
        result.add_created(assembly)
    result.data["assembly"] = describe(assembly)
    result.data["parts_group"] = [o.Label for o in parts.Group]
    result.hints.append("Next: add_to_assembly for each body, then add_fastener / explode_assembly.")
    return result


def _vector(values: Sequence[float] | None) -> Any:
    if values is None:
        return FreeCAD.Vector()
    if len(values) != 3:
        raise validation("Positions and offsets need three values [x, y, z]")
    return FreeCAD.Vector(*(float(v) for v in values))


def _attach(obj: Any, offset: Any) -> None:
    """Asm4 placement: attached by its origin to the assembly's LCS_Origin, moved by AttachmentOffset."""
    for name in ("AttachedBy", "AttachedTo", "SolverId"):
        if not hasattr(obj, name):
            obj.addProperty("App::PropertyString", name, "Assembly")
    if not hasattr(obj, "AttachmentOffset"):
        obj.addProperty("App::PropertyPlacement", "AttachmentOffset", "Assembly")
    obj.AttachedBy = "Origin"
    obj.AttachedTo = f"Parent Assembly#{ORIGIN_LCS}"
    obj.AttachmentOffset = FreeCAD.Placement(offset, FreeCAD.Rotation())
    obj.setExpression("Placement", PLACEMENT_EXPRESSION)
    obj.SolverId = "Asm4EE"


def add_to_assembly(
    part: str,
    label: str | None = None,
    offset: Sequence[float] | None = None,
    document: str | None = None,
) -> ToolResult:
    """Insert a body/part as App::Link 'Link_<part>'; offset 0 = the position it was modelled in."""
    doc = resolve_document(document)
    assembly = get_assembly(doc)
    source = resolve_object(doc, part)
    if source.TypeId not in PART_TYPES:
        raise validation(f"'{source.Label}' is a {source.TypeId}; only bodies and App::Part can be linked")
    result = ToolResult()
    with transaction(doc, f"Assembly link: {source.Label}"):
        link = assembly.newObject("App::Link", "Link")
        # labels are unique per document: reusing the body label would silently become 'Box001'
        link.Label = label or naming.make_label(doc, "Link", source.Label)
        link.LinkedObject = source
        _attach(link, _vector(offset))
        if source.ViewObject is not None:
            source.ViewObject.Visibility = False  # the link shows the part; the source stays editable
        doc.recompute()
        result.add_created(link)
    result.data["link"] = describe(link)
    result.data["placement"] = [round(v, 4) for v in link.Placement.Base]
    return result


def _fasteners() -> Any:
    try:
        import FastenersCmd
    except ImportError:
        raise CoreError(
            UNSUPPORTED,
            "The Fasteners workbench is not installed",
            {"hints": ["install_addon('fasteners'), then restart FreeCAD"]},
        ) from None
    return FastenersCmd


def add_fastener(
    type: str,
    diameter: str,
    positions: Sequence[Sequence[float]],
    thread: bool = False,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Standard parts (nuts, washers, screws) from the Fasteners workbench at the given positions."""
    if not positions:
        raise validation("positions needs at least one [x, y, z]")
    fasteners = _fasteners()
    if type not in getattr(fasteners, "FSScrewCommandTable", {type: None}):
        raise validation(f"Unknown fastener type '{type}' (e.g. ISO4032 nut, ISO7089 washer, ISO4762 screw)")
    doc = resolve_document(document)
    assembly = get_assembly(doc, required=False)
    result = ToolResult()
    created = []
    with transaction(doc, f"Fastener: {type} {diameter} x{len(positions)}"):
        for index, position in enumerate(positions, 1):
            obj = doc.addObject("Part::FeaturePython", type)
            if assembly is not None:
                assembly.addObject(obj)
            fasteners.FSScrewObject(obj, type, None)
            diameters = obj.getEnumerationsOfProperty("Diameter") or []
            if diameter not in diameters:
                raise validation(f"{type} has no diameter '{diameter}'", available=diameters)
            obj.Diameter = diameter
            if hasattr(obj, "Thread"):
                obj.Thread = bool(thread)
            obj.Label = naming.make_label(doc, obj.Proxy.familyType, f"{purpose or diameter}_{index}")
            provider = getattr(fasteners, "FSViewProviderTree", None)
            if provider is not None and obj.ViewObject is not None:
                provider(obj.ViewObject)
            vector = _vector(position)
            if assembly is not None:
                _attach(obj, vector)
            else:
                obj.Placement = FreeCAD.Placement(vector, FreeCAD.Rotation())
            created.append(obj)
        doc.recompute()
        for obj in created:
            result.add_created(obj)
    result.data["fasteners"] = [describe(o) for o in created]
    if assembly is None:
        result.warnings.append("No assembly: fasteners placed absolutely at the document root")
    return result


# --- Configurations (Asm4 configuration tables) ---------------------------------------------------
def _placed_objects(assembly: Any) -> list[Any]:
    return [o for o in assembly.Group if getattr(o, "SolverId", "") == "Asm4EE"]


def _config_group(assembly: Any) -> Any:
    group = assembly.Document.getObject("Configurations")
    return group if group is not None else _group(assembly, "Configurations")


def _alias(name: str) -> str:
    return "".join(c for c in name if c not in r"`~!@#$%^&*()-+=|\;:'\".,").strip("_")


def _save_config(assembly: Any, name: str, description: str) -> Any:
    group = _config_group(assembly)
    sheet = group.getObject(name)
    if sheet is not None:
        assembly.Document.removeObject(sheet.Name)
    sheet = group.newObject("Spreadsheet::Sheet", name)
    sheet.set(HEADER_CELL, CONFIG_TYPE)
    sheet.set(DESCRIPTION_CELL, description)
    for column, header in zip(COLUMNS, HEADERS, strict=True):
        sheet.set(f"{column}{START_ROW - 1}", header)
    for row, obj in enumerate(_placed_objects(assembly), START_ROW):
        offset = obj.AttachmentOffset
        yaw, pitch, roll = offset.Rotation.toEuler()
        visible = obj.ViewObject.Visibility if obj.ViewObject is not None else obj.Visibility
        values = (f"{assembly.Name}.{obj.Name}", str(bool(visible)), "Asm4EE", *offset.Base, yaw, pitch, roll)
        for column, value in zip(COLUMNS, values, strict=True):
            sheet.set(f"{column}{row}", str(value))
        sheet.setAlias(f"A{row}", _alias(f"{assembly.Name}.{obj.Name}"))
    sheet.recompute()
    return sheet


def _offsets(sheet: Any, assembly: Any) -> dict[str, Any]:
    """Object name -> AttachmentOffset stored in a configuration table."""
    offsets = {}
    for obj in _placed_objects(assembly):
        cell = sheet.getCellFromAlias(_alias(f"{assembly.Name}.{obj.Name}"))
        if not cell:
            continue
        row = "".join(c for c in cell if c.isdigit())
        x, y, z, yaw, pitch, roll = (float(sheet.get(f"{col}{row}")) for col in COLUMNS[3:])
        offsets[obj.Name] = FreeCAD.Placement(FreeCAD.Vector(x, y, z), FreeCAD.Rotation(yaw, pitch, roll))
    return offsets


def _configuration(assembly: Any, name: str) -> Any:
    sheet = _config_group(assembly).getObject(name)
    if sheet is None or sheet.get(HEADER_CELL) != CONFIG_TYPE:
        names = [o.Name for o in _config_group(assembly).Group if o.TypeId == "Spreadsheet::Sheet"]
        raise not_found(f"No configuration '{name}'", available=names)
    return sheet


def explode_assembly(
    moves: dict[str, Sequence[float]],
    name: str = "Exploded",
    document: str | None = None,
) -> ToolResult:
    """Exploded configuration: every listed object moved from its assembled position by [dx, dy, dz].

    The assembled state is saved once as configuration 'Assembled' so repeated calls stay idempotent;
    the exploded state stays active (apply_configuration('Assembled') puts the parts back).
    """
    if not moves:
        raise validation("moves needs at least one object: {label: [dx, dy, dz]}")
    doc = resolve_document(document)
    assembly = get_assembly(doc)
    placed = {o.Name: o for o in _placed_objects(assembly)}
    targets = {}
    for ref, move in moves.items():
        obj = resolve_object(doc, ref)
        links = [o for o in placed.values() if getattr(o, "LinkedObject", None) == obj]
        if obj.Name not in placed and len(links) == 1:
            obj = links[0]  # a body stands for its single link in the assembly
        if obj.Name not in placed:
            raise validation(f"'{obj.Label}' is not placed in the assembly (add_to_assembly/add_fastener)")
        targets[obj.Name] = _vector(move)
    result = ToolResult()
    with transaction(doc, f"Exploded view: {name}"):
        group = _config_group(assembly)
        if group.getObject(ASSEMBLED) is None:
            _save_config(assembly, ASSEMBLED, "assembled state (saved by explode_assembly)")
        assembled = _offsets(_configuration(assembly, ASSEMBLED), assembly)
        for obj_name, obj in placed.items():
            base = assembled.get(obj_name, obj.AttachmentOffset)
            move = targets.get(obj_name, FreeCAD.Vector())
            obj.AttachmentOffset = FreeCAD.Placement(base.Base + move, base.Rotation)
        doc.recompute()
        sheet = _save_config(assembly, name, f"exploded view of {len(targets)} objects")
        result.add_created(sheet)
    result.data["configuration"] = name
    result.data["configurations"] = [o.Name for o in group.Group if o.TypeId == "Spreadsheet::Sheet"]
    result.data["moved"] = {placed[n].Label: [round(v, 4) for v in m] for n, m in targets.items()}
    return result


def apply_configuration(name: str, document: str | None = None) -> ToolResult:
    """Apply a saved configuration (e.g. 'Assembled' or 'Exploded') to the assembly."""
    doc = resolve_document(document)
    assembly = get_assembly(doc)
    sheet = _configuration(assembly, name)
    result = ToolResult()
    with transaction(doc, f"Configuration: {name}"):
        offsets = _offsets(sheet, assembly)
        for obj in _placed_objects(assembly):
            if obj.Name in offsets:
                obj.AttachmentOffset = offsets[obj.Name]
                result.add_modified(obj)
        doc.recompute()
    result.data["configuration"] = name
    return result
