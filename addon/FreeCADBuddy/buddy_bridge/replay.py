"""Replay a design stream into a new document, step by step over the same registry path that
recorded it.

The stream is document data and may come from any FCStd file, so only modelling methods are
replayed (allowlist). Scripts, addon installation, file and document lifecycle, exports and the
STEP import (a file path from the stream) are skipped and reported."""

from __future__ import annotations

import inspect
from typing import Any

import FreeCAD

from buddy_core import __version__, documents, stream
from buddy_core.errors import CoreError, not_found, validation
from buddy_core.result import ToolResult

REPLAYABLE = (
    "body.",
    "sketch.",
    "feature.",
    "design.",
    "appearance.",
    "assembly.",
    "parameters.set",
    "document.delete",
    stream.STOREPOINT_METHOD,
)
NEVER_REPLAYED = ("assembly.insert_step",)  # reads a file path taken from the stream


def replayable(method: str) -> bool:
    return method.startswith(REPLAYABLE) and method not in NEVER_REPLAYED


def replay(registry: Any, storepoint: str, into: str, document: str | None = None) -> ToolResult:
    """Build a new document ``into`` from the stream of ``document`` up to ``storepoint``."""
    source = documents.resolve_document(document)
    items = stream.reconcile(source)
    points = stream.storepoints(items)
    match = next((point for point in points if point["name"] == storepoint), None)
    if match is None:
        raise not_found(f"Unknown storepoint '{storepoint}'", available=[point["name"] for point in points])
    taken = {key for name, doc in FreeCAD.listDocuments().items() for key in (name, doc.Label)}
    if into in taken:
        raise validation(f"Document '{into}' already exists - choose a new name")
    steps = items[: match["position"] + 1]
    result = ToolResult()
    foreign_versions = sorted(
        {str(entry["version"]) for entry in steps if entry.get("version")} - {__version__}
    )
    if foreign_versions:
        result.warnings.append(
            f"Stream was recorded with FreeCAD Buddy {', '.join(foreign_versions)}; tools may have changed."
        )
    target = documents.new_document(into).data["document"]["name"]
    executed = 0
    skipped: list[dict[str, Any]] = []
    for index, entry in enumerate(steps):
        method = entry["method"]
        if method == stream.MANUAL_EDIT:
            names = ", ".join(entry.get("undo_names", []))
            result.warnings.append(
                f"Step {index}: manual edits in the original ({names}) are not in the stream."
            )
        elif not replayable(method):
            skipped.append({"step": index, "method": method})
        else:
            _run_step(registry, index, entry, target, executed)
            executed += 1
    result.data["document"] = {"name": target, "label": into}
    result.data["storepoint"] = storepoint
    result.data["steps"] = executed
    result.data["skipped"] = skipped
    if skipped:
        result.hints.append(
            "Skipped steps are not replayed for safety (scripts, addon installation, file access, STEP import) "
            "and need a manual follow-up."
        )
    result.hints.append(f"'{into}' is the active document now; the original is unchanged.")
    return result


def _run_step(registry: Any, index: int, entry: dict[str, Any], target: str, executed: int) -> None:
    """Run one stream step in ``target``; a failure stops the replay and keeps the partial document."""
    method = entry["method"]
    params = dict(entry.get("params") or {})
    if "document" in inspect.signature(registry.function(method)).parameters:
        params["document"] = target
    if method == stream.STOREPOINT_METHOD:
        params["snapshot"] = False  # the copy has no file yet
    try:
        registry.execute(method, params)
    except CoreError as error:
        raise CoreError(
            error.name,
            f"Replay stopped at step {index} ({method}): {error.message}",
            {**error.data, "step": index, "method": method, "document": target, "executed": executed},
        ) from None
    except Exception as error:  # report the step, keep the partial document
        raise CoreError(
            "recompute_failed",
            f"Replay stopped at step {index} ({method}): {type(error).__name__}: {error}",
            {"step": index, "method": method, "document": target, "executed": executed},
        ) from error
