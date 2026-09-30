"""Design stream: every mutating Buddy call of a document, stored in the document, with storepoints.

The bridge registry records a call after it succeeded (method, parameters, created objects, undo
name); this module owns the storage (group ``Storepoints``), the bookkeeping for undo and foreign
transactions, storepoints (a marker object plus a description on the feature) and their listing.
Replay lives in the bridge, which knows methods by name.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import FreeCAD

from buddy_core import __version__, naming
from buddy_core.errors import validation
from buddy_core.result import ToolResult, describe
from buddy_core.transaction import commits, transaction

GROUP_NAME = "BuddyStorepoints"
GROUP_LABEL = "Storepoints"
STREAM_PROPERTY = "Stream"
MANUAL_EDIT = "manual_edit"
STOREPOINT_METHOD = "stream.storepoint"
MARKER_PREFIX = "Storepoint"

# 16x16 diamond, the tree icon of a storepoint marker (GUI only)
_ICON = """/* XPM */
static char * storepoint_xpm[] = {
"16 16 2 1",
" \tc None",
".\tc #1F77B4",
"       ..       ",
"      ....      ",
"     ......     ",
"    ........    ",
"   ..........   ",
"  ............  ",
" .............. ",
"................",
"................",
" .............. ",
"  ............  ",
"   ..........   ",
"    ........    ",
"     ......     ",
"      ....      ",
"       ..       "};
"""


# --- storage ---------------------------------------------------------------------------------------
def group(doc: Any, create: bool = False) -> Any:
    """The group ``Storepoints`` that holds the stream property and the marker objects."""
    obj = doc.getObject(GROUP_NAME)
    if obj is None and create:
        obj = doc.addObject("App::DocumentObjectGroup", GROUP_NAME)
        obj.Label = GROUP_LABEL
        obj.addProperty(
            "App::PropertyStringList",
            STREAM_PROPERTY,
            "FreeCADBuddy",
            "Design stream, one JSON entry per line",
        )
        obj.addProperty("App::PropertyString", "StreamVersion", "FreeCADBuddy", "Stream format version")
        obj.StreamVersion = "1"
    return obj


def entries(doc: Any) -> list[dict[str, Any]]:
    """Stream entries of the document; damaged lines (foreign or edited files) are dropped."""
    obj = group(doc)
    if obj is None:
        return []
    items: list[dict[str, Any]] = []
    for line in obj.Stream:
        try:
            entry = json.loads(line)
        except ValueError:
            continue  # ponytail: a damaged line is dropped, not repaired
        if isinstance(entry, dict) and isinstance(entry.get("method"), str):
            items.append(entry)
    return items


def _write(doc: Any, items: list[dict[str, Any]]) -> None:
    group(doc, create=True).Stream = [
        json.dumps(item, ensure_ascii=False, separators=(",", ":")) for item in items
    ]


def append(doc: Any, entry: dict[str, Any]) -> None:
    _write(doc, [*entries(doc), entry])


def markers(doc: Any) -> list[Any]:
    """Storepoint markers in the group; foreign objects the user dropped there are not markers."""
    obj = group(doc)
    return [child for child in obj.Group if hasattr(child, "Position")] if obj is not None else []


# --- recording (called by the bridge registry) ----------------------------------------------------
_seen: dict[str, list[str]] = {}
"""Undo history per document at the last reconcile; forgotten when a document is closed, created or
reloaded in place (``restore``), since its undo history starts empty again."""


class _ForgetHistory:
    def slotCreatedDocument(self, doc: Any) -> None:
        _seen.pop(doc.Name, None)

    def slotDeletedDocument(self, doc: Any) -> None:  # also fired by doc.restore()
        _seen.pop(doc.Name, None)


FreeCAD.addDocumentObserver(_ForgetHistory())


def snapshot() -> dict[str, int]:
    """Committed Buddy transactions of all open documents before a call."""
    return {name: commits.get(name, 0) for name in FreeCAD.listDocuments()}


def record(
    method: str, params: dict[str, Any], payload: Any, before: dict[str, int], store: bool = True
) -> None:
    """Append the call to the stream of every document it committed a transaction in (``store``);
    otherwise just align the streams with the undo history."""
    created = [item["label"] for item in payload.get("created", [])] if isinstance(payload, dict) else []
    for name, doc in FreeCAD.listDocuments().items():
        if name not in before:
            continue  # a document created by this call starts with an empty stream
        if not store or commits.get(name, 0) <= before[name]:
            _align(doc)
        else:
            _align(doc, keep=1)
            append(
                doc,
                {
                    "method": method,
                    "params": params,
                    "created": created,
                    "undo_name": next(iter(doc.UndoNames), ""),
                    "time": _now(),
                    "version": __version__,
                },
            )


def reconcile(doc: Any, keep: int = 0) -> list[dict[str, Any]]:
    """Align the stream with the undo history (see ``_align``) and return its entries."""
    _align(doc, keep)
    return entries(doc)


def _align(doc: Any, keep: int = 0) -> None:
    """Drop entries the user undid and note foreign transactions (manual GUI edits) as
    ``manual_edit``. ``keep`` skips the newest undo names (the transaction of the call being
    recorded). The stream is only parsed when the undo history changed.

    The difference to the history of the last reconcile tells how many steps were undone and how
    many foreign ones were added since. # ponytail: undo-then-redo of a reconciled entry comes back
    as a manual edit; a history of identical names only stays ambiguous.
    """
    history = list(doc.UndoNames)
    previous = _seen.get(doc.Name, [])
    _seen[doc.Name] = history
    undone, added = _difference(previous, history, _undo_limit(), keep)
    if not added and doc.RedoCount < undone:
        undone = 0  # the history was cleared (undo switched off), nothing was undone
    added = max(added - keep, 0)
    items = entries(doc) if undone or added else []
    if not items:
        return
    result = _drop(items, undone)
    if added:
        names = history[keep : keep + added]
        if result and result[-1]["method"] == MANUAL_EDIT:  # further GUI transactions: the same edit
            result[-1] = {**result[-1], "undo_names": names + result[-1].get("undo_names", [])}
        else:
            result.append({"method": MANUAL_EDIT, "undo_names": names, "time": _now()})
    _write(doc, result)


def _undo_limit() -> int:
    """Undo steps FreeCAD keeps at least (GUI preference, headless fixed 20). Too low is harmless,
    too high would read a full stack as undone steps - so never above 20."""
    return min(FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Document").GetInt("MaxUndoSize", 20), 20)


def _difference(previous: list[str], current: list[str], limit: int, least_added: int = 0) -> tuple[int, int]:
    """(undone, added): the shortest explanation - fewest steps, then fewest undone - that turns the
    previous undo history into the current one (newest first), with at least ``least_added`` new
    steps (the call being recorded). Only a full stack (``limit``) drops its oldest steps."""
    for total in range(len(previous) + len(current) + 1):
        for undone in range(min(total, len(previous)) + 1):
            added, rest = total - undone, previous[undone:]
            expected = len(rest) + added
            fits = expected == len(current) or (expected > len(current) >= limit)
            if (
                least_added <= added <= len(current)
                and fits
                and current[added:] == rest[: len(current) - added]
            ):
                return undone, added
    return 0, 0  # unreachable: undoing everything and adding the whole history always fits


def _drop(items: list[dict[str, Any]], undone: int) -> list[dict[str, Any]]:
    """``items`` without their newest ``undone`` transactions (a manual edit may be cut)."""
    result = list(items)
    while undone > 0 and result:
        entry = result.pop()
        names = entry.get("undo_names", []) if entry["method"] == MANUAL_EDIT else [entry.get("undo_name")]
        if len(names) > undone:
            result.append({**entry, "undo_names": names[undone:]})
        undone -= len(names)
    return result


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


# --- storepoints ---------------------------------------------------------------------------------
def storepoints(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Storepoints of a stream with position, timestamp and steps since the previous one."""
    found: list[dict[str, Any]] = []
    previous = -1
    for index, entry in enumerate(items):
        name = (entry.get("params") or {}).get("name") if entry["method"] == STOREPOINT_METHOD else None
        if isinstance(name, str):
            found.append(
                {
                    "name": name,
                    "position": index,
                    "created": entry.get("time"),
                    "steps": index - previous - 1,
                    "marker": entry["created"][0] if entry.get("created") else None,
                }
            )
            previous = index
    return found


def _last_created(doc: Any, items: list[dict[str, Any]]) -> Any:
    for entry in reversed(items):
        for label in reversed(entry.get("created", [])):
            found = doc.getObjectsByLabel(label)
            if found and found[0].TypeId != "App::FeaturePython":
                return found[0]
    return None


def _snapshot_path(doc: Any, name: str) -> Path:
    source = Path(doc.FileName)
    return source.with_name(f"{source.stem}-{naming.sanitize(name)}.FCStd")


def storepoint(name: str, snapshot: bool = False, document: str | None = None) -> ToolResult:
    """Mark the current position of the design stream: a marker object in the group ``Storepoints``
    (linked to the feature that was current) and the description "◆ Storepoint n: name" on that
    feature. ``snapshot`` also saves a copy of the document next to its file (fallback for manual
    edits that are not in the stream).
    """
    from buddy_core.documents import resolve_document

    doc = resolve_document(document)
    clean = name.strip()
    if not clean:
        raise validation("name must not be empty")
    items = reconcile(doc)
    points = storepoints(items)
    existing = [point["name"] for point in points]
    if clean in existing:
        raise validation(f"Storepoint '{clean}' already exists", available=existing)
    if snapshot and not doc.FileName:
        raise validation("snapshot needs a saved document (document(action='save') first)")
    feature = _last_created(doc, items)
    number = len(existing) + 1
    result = ToolResult()
    with transaction(doc, f"Storepoint: {clean}"):
        container = group(doc, create=True)
        marker = doc.addObject("App::FeaturePython", MARKER_PREFIX)
        marker.Label = naming.make_label(doc, MARKER_PREFIX, clean)
        marker.addProperty("App::PropertyLink", "Feature", "Storepoint", "Feature that was current here")
        marker.addProperty("App::PropertyInteger", "Position", "Storepoint", "Index in the design stream")
        marker.addProperty("App::PropertyString", "Created", "Storepoint", "Timestamp")
        marker.addProperty(
            "App::PropertyInteger", "Steps", "Storepoint", "Recorded steps since the previous storepoint"
        )
        marker.Feature = feature
        marker.Position = len(items)
        marker.Created = _now()
        marker.Steps = len(items) - (points[-1]["position"] + 1 if points else 0)
        container.addObject(marker)
        if feature is not None:
            feature.Label2 = f"◆ Storepoint {number}: {clean}"
        if FreeCAD.GuiUp and getattr(marker, "ViewObject", None) is not None:
            marker.ViewObject.Proxy = StorepointViewProvider()
        doc.recompute()
        result.add_created(marker)
    result.data["storepoint"] = {
        "name": clean,
        "number": number,
        "position": len(items),
        "feature": feature.Label if feature is not None else None,
        "marker": describe(marker),
    }
    if snapshot:
        path = _snapshot_path(doc, clean)
        doc.saveCopy(str(path))
        result.data["snapshot"] = str(path)
    result.hints.append(
        f"replay(storepoint='{clean}', into='<new document>') rebuilds the design up to here."
    )
    return result


def list_storepoints(document: str | None = None) -> ToolResult:
    """Storepoints of the document with position, timestamp and steps since the previous one."""
    from buddy_core.documents import resolve_document

    doc = resolve_document(document)
    items = reconcile(doc)
    result = ToolResult()
    points = storepoints(items)
    for point in points:
        markers = doc.getObjectsByLabel(point["marker"]) if point["marker"] else []
        feature = markers[0].Feature if markers else None
        point["feature"] = feature.Label if feature is not None else None
    result.data["storepoints"] = points
    result.data["steps"] = len(items)
    result.data["manual_edits"] = sum(1 for entry in items if entry["method"] == MANUAL_EDIT)
    if not items:
        result.hints.append("No design stream yet - recording starts with the next modelling call.")
    return result


class StorepointViewProvider:
    """Tree icon and double-click for marker objects (GUI only; the addon must be installed)."""

    def attach(self, vobj: Any) -> None:
        self.Object = vobj.Object

    def getIcon(self) -> str:
        return _ICON

    def claimChildren(self) -> list[Any]:
        return []

    def doubleClicked(self, vobj: Any) -> bool:
        import FreeCADGui  # ui

        feature = vobj.Object.Feature
        if feature is not None:
            FreeCADGui.Selection.clearSelection()
            FreeCADGui.Selection.addSelection(feature)
        return True

    def dumps(self) -> None:
        return None

    def loads(self, state: Any) -> None:
        return None
