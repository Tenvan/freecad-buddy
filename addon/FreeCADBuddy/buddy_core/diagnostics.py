"""Catalogue of typical recompute problems with actionable hints for the agent."""

from __future__ import annotations

import re

_CATALOGUE: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"not closed|wire.*closed|open wire", re.I),
        "Profil ist nicht geschlossen: Linienzug in der Skizze schließen (analyze_sketch zeigt offene Wires).",
    ),
    (
        re.compile(r"empty|does not intersect|no intersect|nothing to cut|resulting shape is null", re.I),
        "Feature trifft kein Material: Richtung umkehren (reversed) oder Tiefe/Skizzenlage prüfen.",
    ),
    (
        re.compile(r"multiple solids|more than one solid|single solid", re.I),
        "Ergebnis besteht aus mehreren Körpern: Profil muss den bestehenden Körper berühren oder überlappen.",
    ),
    (
        re.compile(r"fillet|chamfer|BRep_API|command not done", re.I),
        "Verrundung/Fase zu groß oder Kanten ungeeignet: Radius verkleinern oder Selektor einschränken.",
    ),
    (
        re.compile(r"thickness|offset", re.I),
        "Schale (Thickness) fehlgeschlagen: Wandstärke verringern oder andere Öffnungsfläche wählen.",
    ),
    (
        re.compile(r"sketch.*(conflict|redundant|malformed)|solver", re.I),
        "Skizze ist nicht lösbar: analyze_sketch aufrufen und widersprüchliche Constraints entfernen.",
    ),
    (
        re.compile(r"link.*(broken|not found|missing)|not in body|out of scope", re.I),
        "Referenz ist ungültig: Feature verweist auf gelöschte oder fremde Geometrie.",
    ),
]


def hints(messages: list[str]) -> list[str]:
    found: list[str] = []
    for message in messages:
        for pattern, hint in _CATALOGUE:
            if pattern.search(message) and hint not in found:
                found.append(hint)
    return found
