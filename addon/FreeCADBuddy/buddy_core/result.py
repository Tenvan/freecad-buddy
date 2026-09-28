"""Uniform result object returned by every mutating core operation (``ToolResult``)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def describe(obj: Any) -> dict[str, str]:
    return {"name": obj.Name, "label": obj.Label, "type": obj.TypeId}


@dataclass
class ToolResult:
    created: list[dict[str, str]] = field(default_factory=list)
    modified: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    sketch: dict[str, Any] | None = None
    recompute: list[dict[str, Any]] = field(default_factory=list)

    def add_created(self, obj: Any) -> None:
        self.created.append(describe(obj))

    def add_modified(self, obj: Any) -> None:
        entry = describe(obj)
        if entry not in self.modified:
            self.modified.append(entry)

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "ok": True,
            "created": self.created,
            "modified": self.modified,
            "warnings": self.warnings,
            "hints": self.hints,
        }
        if self.sketch is not None:
            result["sketch"] = self.sketch
        if self.recompute:
            result["recompute"] = self.recompute
        result.update(self.data)
        return result
