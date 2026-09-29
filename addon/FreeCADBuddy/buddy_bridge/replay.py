"""Replay a design stream into a new document, step by step over the same registry path that
recorded it. Python execution and addon installation are never replayed."""

from __future__ import annotations

import inspect
from typing import Any

import FreeCAD

from buddy_core import __version__, documents, stream
from buddy_core.errors import CoreError, not_found, validation
from buddy_core.result import ToolResult

NEVER_REPLAYED = ("python.", "addons.install")


def replay(registry: Any, storepoint: str, into: str, document: str | None = None) -> ToolResult:
    """Build a new document ``into`` from the stream of ``document`` up to ``storepoint``."""
    source = documents.resolve_document(document)
    items = stream.reconcile(source)
    points = stream.storepoints(items)
    match = next((point for point in points if point["name"] == storepoint), None)
    if match is None:
        raise not_found(f"Unknown storepoint '{storepoint}'", available=[point["name"] for point in points])
    taken = {name for name in FreeCAD.listDocuments()} | {
        doc.Label for doc in FreeCAD.listDocuments().values()
    }
    if into in taken:
        raise validation(f"Document '{into}' already exists - choose a new name")
    result = ToolResult()
    target = documents.new_document(into).data["document"]["name"]
    executed = 0
    skipped: list[dict[str, Any]] = []
    versions = sorted(
        str(entry.get("version")) for entry in items[: match["position"] + 1] if entry.get("version")
    )
    foreign_versions = sorted(set(versions) - {__version__})
    if foreign_versions:
        result.warnings.append(
            f"Stream was recorded with FreeCAD Buddy {', '.join(foreign_versions)}; tools may have changed."
        )
    for index, entry in enumerate(items[: match["position"] + 1]):
        method = entry["method"]
        if method == stream.MANUAL_EDIT:
            names = ", ".join(entry.get("undo_names", []))
            result.warnings.append(
                f"Step {index}: manual edits in the original ({names}) are not in the stream."
            )
            continue
        if method.startswith(NEVER_REPLAYED):
            skipped.append({"step": index, "method": method})
            continue
        params = dict(entry["params"])
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
        executed += 1
    result.data["document"] = {"name": target, "label": into}
    result.data["storepoint"] = storepoint
    result.data["steps"] = executed
    result.data["skipped"] = skipped
    if skipped:
        result.hints.append("Skipped steps need a manual follow-up (Python execution, addon installation).")
    result.hints.append(f"'{into}' is the active document now; the original is unchanged.")
    return result
