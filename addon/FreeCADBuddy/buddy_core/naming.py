"""Readable, stable labels (``<Type>_<Purpose>``) and a lint for FreeCAD default names."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

_DEFAULT_LABEL = re.compile(
    r"^(Body|Sketch|Pad|Pocket|Revolution|Groove|Hole|Fillet|Chamfer|Thickness|Mirrored|"
    r"LinearPattern|PolarPattern|MultiTransform|DatumPlane|Plane|DatumLine|Line|Binder)\d*$"
)
_NON_WORD = re.compile(r"[^A-Za-z0-9]+")


def sanitize(text: str) -> str:
    """ASCII PascalCase fragment; umlauts are transliterated (``Größe`` -> ``Groesse``)."""
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    text = text.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    parts = [p for p in _NON_WORD.split(ascii_text) if p]
    return "".join(p[:1].upper() + p[1:] for p in parts)


def make_label(doc: Any, prefix: str, purpose: str | None) -> str:
    base = f"{prefix}_{sanitize(purpose)}" if purpose and sanitize(purpose) else prefix
    return unique_label(doc, base)


def unique_label(doc: Any, label: str) -> str:
    existing = {obj.Label for obj in doc.Objects}
    if label not in existing:
        return label
    index = 2
    while f"{label}_{index}" in existing:
        index += 1
    return f"{label}_{index}"


def is_default_label(label: str) -> bool:
    return bool(_DEFAULT_LABEL.match(label))


def lint_labels(doc: Any) -> list[dict[str, str]]:
    """Objects inside bodies (and bodies themselves) that still carry a FreeCAD default label."""
    issues = []
    for obj in doc.Objects:
        in_body = obj.TypeId == "PartDesign::Body" or any(
            parent.TypeId == "PartDesign::Body" for parent in obj.InList
        )
        if in_body and not obj.TypeId.startswith("App::Origin") and is_default_label(obj.Label):
            issues.append(
                {"name": obj.Name, "label": obj.Label, "issue": "Standardname statt sprechendem Label"}
            )
    return issues
