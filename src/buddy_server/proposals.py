"""Design tool proposals (R-05): agents propose missing design tools, a developer builds them as Buddy tools.

Stored as one JSON file in the Buddy home; proposals with the same name are merged and counted.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any


def _key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")


def _merge(items: list[str], new: list[str]) -> list[str]:
    return items + [item for item in new if item and item not in items]


class ProposalStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def all(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def propose(
        self, name: str, problem: str, inputs: list[str], steps: list[str], example: str
    ) -> dict[str, Any]:
        key = _key(name)
        if not key:
            raise ValueError("name must contain letters or digits, e.g. 'screw_boss'")
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        proposals = self.all()
        entry = next((p for p in proposals if p["name"] == key), None)
        if entry is None:
            entry = {"name": key, "count": 0, "problems": [], "inputs": [], "steps": [], "examples": [],
                     "first_proposed": now}  # fmt: skip
            proposals.append(entry)
        entry["count"] += 1
        entry["problems"] = _merge(entry["problems"], [problem])
        entry["inputs"] = _merge(entry["inputs"], inputs)
        entry["steps"] = steps or entry["steps"]  # the latest breakdown wins
        entry["examples"] = _merge(entry["examples"], [example])
        entry["last_proposed"] = now
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(proposals, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
        return entry
