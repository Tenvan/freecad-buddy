"""Central model parameters in an ``App::VarSet`` labelled ``Parameters``.

Dimensions reference them via expressions (``<<Parameters>>.Box_Width``), so a change in
the GUI propagates through the whole model.
"""

from __future__ import annotations

import re
from typing import Any

from buddy_core.errors import not_found, validation
from buddy_core.result import ToolResult
from buddy_core.transaction import transaction

VARSET_LABEL = "Parameters"
GROUP = "Parameters"
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

TYPES: dict[str, str] = {
    "length": "App::PropertyLength",
    "distance": "App::PropertyDistance",
    "angle": "App::PropertyAngle",
    "integer": "App::PropertyInteger",
    "float": "App::PropertyFloat",
    "bool": "App::PropertyBool",
}
_TYPE_BY_ID = {type_id: name for name, type_id in TYPES.items()}


_UNITS = {"length": "mm", "distance": "mm", "angle": "deg"}


def unit_of(doc: Any, name: str) -> str | None:
    """Unit used in expressions for a parameter (``mm``/``deg``) or ``None`` for plain numbers."""
    kind = _existing_type(doc, name)
    return _UNITS.get(kind) if kind else None


def _clashes_with_unit(name: str) -> bool:
    """Names FreeCAD's expression parser reads as unit or constant (N, mm, pi, e, h, ...)."""
    import FreeCAD

    try:
        FreeCAD.Units.parseQuantity(name)
    except Exception:
        return False
    return True


def expression(name: str) -> str:
    return f"<<{VARSET_LABEL}>>.{name}"


def find_varset(doc: Any) -> Any | None:
    matches = doc.getObjectsByLabel(VARSET_LABEL)
    return next((obj for obj in matches if obj.TypeId == "App::VarSet"), None)


def _ensure_varset(doc: Any, result: ToolResult) -> Any:
    varset = find_varset(doc)
    if varset is None:
        varset = doc.addObject("App::VarSet", "Parameters")
        varset.Label = VARSET_LABEL
        result.add_created(varset)
    return varset


def _raw(value: Any) -> Any:
    return value.Value if hasattr(value, "Value") and hasattr(value, "Unit") else value


def _entry(varset: Any, name: str) -> dict[str, Any]:
    type_id = varset.getTypeIdOfProperty(name)
    return {
        "name": name,
        "type": _TYPE_BY_ID.get(type_id, type_id),
        "value": _raw(getattr(varset, name)),
        "description": varset.getDocumentationOfProperty(name),
        "expression": expression(name),
    }


def list_parameters(doc: Any) -> list[dict[str, Any]]:
    varset = find_varset(doc)
    if varset is None:
        return []
    return [
        _entry(varset, name) for name in varset.PropertiesList if varset.getGroupOfProperty(name) == GROUP
    ]


def numeric_value(doc: Any, name: str) -> float:
    varset = find_varset(doc)
    if varset is None or name not in varset.PropertiesList:
        raise not_found(
            f"Parameter '{name}' existiert nicht. Erst mit set_parameters anlegen.",
            available=[p["name"] for p in list_parameters(doc)],
        )
    value = _raw(getattr(varset, name))
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise validation(f"Parameter '{name}' ist nicht numerisch")
    return float(value)


def _existing_type(doc: Any, name: str) -> str | None:
    varset = find_varset(doc)
    if varset is None or name not in varset.PropertiesList:
        return None
    return _TYPE_BY_ID.get(varset.getTypeIdOfProperty(name))


def _infer_type(value: Any) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int | float):
        return "length"
    raise validation(f"Wert {value!r} ist weder Zahl noch Bool")


def set_parameters(doc: Any, parameters: dict[str, Any]) -> ToolResult:
    """Create or update parameters.

    ``parameters`` maps names to a value or to ``{"value", "type", "description"}``; numbers
    default to type ``length`` (mm).
    """
    if not parameters:
        raise validation("Keine Parameter angegeben")
    specs: dict[str, dict[str, Any]] = {}
    for name, spec in parameters.items():
        if not _NAME.match(name):
            raise validation(f"Ungültiger Parametername '{name}' (Buchstabe, dann Buchstaben/Ziffern/_)")
        if _clashes_with_unit(name):
            raise validation(
                f"Parametername '{name}' ist in FreeCAD eine Einheit oder Konstante und würde Ausdrücke brechen – "
                "sprechenden Namen wählen (z. B. Box_Height statt h)"
            )
        spec = spec if isinstance(spec, dict) else {"value": spec}
        if "value" not in spec:
            raise validation(f"Parameter '{name}': 'value' fehlt")
        existing = _existing_type(doc, name)
        kind = spec.get("type") or existing or _infer_type(spec["value"])
        if kind not in TYPES:
            raise validation(f"Parameter '{name}': unbekannter Typ '{kind}' (erlaubt: {', '.join(TYPES)})")
        specs[name] = {**spec, "type": kind}

    result = ToolResult()
    with transaction(doc, f"Parameter setzen: {', '.join(specs)}"):
        varset = _ensure_varset(doc, result)
        for name, spec in specs.items():
            type_id = TYPES[spec["type"]]
            if name in varset.PropertiesList:
                if varset.getTypeIdOfProperty(name) != type_id:
                    raise validation(
                        f"Parameter '{name}' hat bereits Typ '{_TYPE_BY_ID.get(varset.getTypeIdOfProperty(name))}'"
                    )
            else:
                varset.addProperty(type_id, name, GROUP, spec.get("description", ""))
            setattr(varset, name, spec["value"])
        result.add_modified(varset)
        doc.recompute()
        _refresh_semantic_references(doc, result)
    result.data["parameters"] = list_parameters(doc)
    return result


def _refresh_semantic_references(doc: Any, result: ToolResult) -> None:
    # Parameter changes can move topology; dress-up features re-resolve their selectors.
    from buddy_core import select

    for obj in select.refresh_references(doc):
        result.add_modified(obj)
