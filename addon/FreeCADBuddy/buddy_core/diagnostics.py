"""Catalogue of typical recompute problems with actionable hints for the agent."""

from __future__ import annotations

import re

_CATALOGUE: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"not closed|wire.*closed|open wire", re.I),
        "Profile is not closed: close the wire in the sketch (analyze_sketch shows open wires).",
    ),
    (
        re.compile(r"empty|does not intersect|no intersect|nothing to cut|resulting shape is null", re.I),
        "Feature hits no material: reverse the direction (reversed) or check depth/sketch position.",
    ),
    (
        re.compile(r"multiple solids|more than one solid|single solid", re.I),
        "Result consists of several solids: the profile must touch or overlap the existing solid.",
    ),
    (
        re.compile(r"fillet|chamfer|BRep_API|command not done", re.I),
        "Fillet/chamfer too large or edges unsuitable: reduce the radius or narrow the selector.",
    ),
    (
        re.compile(r"thickness|offset", re.I),
        "Shell (Thickness) failed: reduce the wall thickness or pick another opening face.",
    ),
    (
        re.compile(r"sketch.*(conflict|redundant|malformed)|solver", re.I),
        "Sketch cannot be solved: call analyze_sketch and remove conflicting constraints.",
    ),
    (
        re.compile(r"link.*(broken|not found|missing)|not in body|out of scope", re.I),
        "Reference is invalid: the feature points to deleted or foreign geometry.",
    ),
]


def hints(messages: list[str]) -> list[str]:
    found: list[str] = []
    for message in messages:
        for pattern, hint in _CATALOGUE:
            if pattern.search(message) and hint not in found:
                found.append(hint)
    return found
