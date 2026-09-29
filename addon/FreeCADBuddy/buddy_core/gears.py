"""Gears from the freecad.gears workbench as PartDesign features inside a body.

Built the way the workbench's own commands do it (``commands.BaseCommand.create``): a
``PartDesign::FeaturePython`` with the gear proxy, added to the body, fused with the base feature by
the proxy's ``execute``. The file then needs freecad.gears to recompute (note it in the project README).
"""

from __future__ import annotations

import importlib
import os
from collections.abc import Mapping
from typing import Any

import FreeCAD

from buddy_core import naming, values
from buddy_core.body import resolve_body
from buddy_core.documents import resolve_document
from buddy_core.errors import UNSUPPORTED, CoreError, validation
from buddy_core.features import _finish, _has_solid, _show_first_base_feature
from buddy_core.result import ToolResult
from buddy_core.transaction import transaction

# kind -> (module, class, icon); freecad.gears/freecad/gears/commands.py
KINDS = {
    "involute": ("involutegear", "InvoluteGear", "involutegear"),
    "internal": ("internalinvolutegear", "InternalInvoluteGear", "internalinvolutegear"),
    "rack": ("involutegearrack", "InvoluteGearRack", "involuterack"),
    "cycloid": ("cycloidgear", "CycloidGear", "cycloidgear"),
    "bevel": ("bevelgear", "BevelGear", "bevelgear"),
    "worm": ("wormgear", "WormGear", "wormgear"),
    "timing": ("timinggear", "TimingGear", "timinggear"),
}
COMPUTED = ("pitch_diameter", "addendum_diameter", "root_diameter")


def _gear_class(kind: str) -> tuple[Any, Any, str]:
    if kind not in KINDS:
        raise validation(f"Unknown gear kind '{kind}' (allowed: {', '.join(KINDS)})")
    module_name, class_name, icon = KINDS[kind]
    try:
        module = importlib.import_module(f"freecad.gears.{module_name}")
        base = importlib.import_module("freecad.gears.basegear")
    except ImportError:
        raise CoreError(
            UNSUPPORTED,
            "The gears workbench (freecad.gears) is not installed",
            {"hints": ["Ask the user, then install_addon('freecad.gears') and restart FreeCAD"]},
        ) from None
    icon_path = os.path.join(os.path.dirname(base.__file__ or ""), "icons", f"{icon}.svg")
    return getattr(module, class_name), base.ViewProviderGear, icon_path


def _set(doc: Any, obj: Any, prop: str, spec: Any) -> None:
    if prop not in obj.PropertiesList:
        raise validation(f"The gear has no property '{prop}'", available=sorted(obj.PropertiesList))
    kind = obj.getTypeIdOfProperty(prop)
    if isinstance(spec, bool) or kind in ("App::PropertyBool", "App::PropertyEnumeration"):
        setattr(obj, prop, spec)
        return
    value = values.resolve(doc, spec, prop)
    if "Integer" in kind:
        if value.expression:
            obj.setExpression(prop, value.expression)
        else:
            setattr(obj, prop, round(value.number))
        return
    unit = {"App::PropertyLength": "mm", "App::PropertyDistance": "mm", "App::PropertyAngle": "deg"}.get(
        kind, ""
    )
    values.apply(obj, prop, value, unit=unit)


def add_gear(
    kind: str = "involute",
    teeth: values.ValueSpec = 15,
    module: values.ValueSpec | None = None,
    height: values.ValueSpec | None = None,
    properties: Mapping[str, Any] | None = None,
    body: str | None = None,
    purpose: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Parametric gear as feature of a body; numbers, parameter names or expressions like other features."""
    gear_class, view_provider, icon = _gear_class(kind)
    doc = resolve_document(document)
    target = resolve_body(doc, body)
    first = not _has_solid(target)
    settings: dict[str, Any] = {"num_teeth": teeth, **(properties or {})}
    if module is not None:
        settings["module"] = module
    if height is not None:
        settings["height"] = height
    result = ToolResult()
    with transaction(doc, f"Gear: {purpose or kind}"):
        gear = doc.addObject("PartDesign::FeaturePython", gear_class.__name__)
        gear_class(gear)
        if FreeCAD.GuiUp and gear.ViewObject is not None:
            view_provider(gear.ViewObject, icon)
        target.addObject(gear)
        target.Tip = gear
        for prop, spec in settings.items():
            _set(doc, gear, prop, spec)
        gear.Label = naming.make_label(
            doc, "Gear", purpose or f"Z{round(values.number(doc, teeth, 'teeth'))}"
        )
        _finish(doc, gear, result)
    result.data["gear"] = {
        prop: round(getattr(gear, prop).Value, 4) for prop in COMPUTED if prop in gear.PropertiesList
    }
    result.hints.append(
        "Meshing gears need the same module and pressure angle; centre distance = (d1 + d2) / 2 of the "
        "pitch diameters. The file now needs freecad.gears: note it in the project README."
    )
    if first:
        _show_first_base_feature(doc, gear, result)
    return result
