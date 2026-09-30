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
from buddy_core.transaction import transaction

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


def claimed(doc: Any) -> set[str]:
    """Names of the marker objects (listed under the group in the model tree, not at the root)."""
    obj = group(doc)
    return {child.Name for child in obj.Group} if obj is not None else set()


# --- recording (called by the bridge registry) ----------------------------------------------------
def snapshot() -> dict[str, int]:
    """Undo counts of all open documents before a call."""
    return {name: doc.UndoCount for name, doc in FreeCAD.listDocuments().items()}


def record(
    method: str, params: dict[str, Any], payload: Any, before: dict[str, int], store: bool = True
) -> None:
    """Append the call to the stream of every document whose undo count grew (``store``);
    otherwise just align the streams with the undo history."""
    created = [item["label"] for item in payload.get("created", [])] if isinstance(payload, dict) else []
    for name, doc in FreeCAD.listDocuments().items():
        if name not in before:
            continue  # a document created by this call starts with an empty stream
        if not store or doc.UndoCount <= before[name]:
            reconcile(doc)
        else:
            reconcile(doc, keep=1)
            append(
                doc,
                {
                    "method": method,
                    "params": params,
                    "created": created,
                    "undo_name": next(iter(doc.UndoNames), ""),
                    "time": datetime.now().isoformat(timespec="seconds"),
                    "version": __version__,
                },
            )


def reconcile(doc: Any, keep: int = 0) -> list[dict[str, Any]]:
    """Align the stream with the undo history: drop entries the user undid, note foreign
    transactions (manual GUI edits) as ``manual_edit``. ``keep`` skips the newest undo names
    (the transaction of the call being recorded).

    Only the undo history FreeCAD still holds is inspected (default 20 steps); older entries count
    as applied. # ponytail: undo-then-redo of an already reconciled entry loses it from the stream.
    """
    items = entries(doc)
    if not items:
        return items
    history = list(doc.UndoNames)[keep:]  # newest first
    result: list[dict[str, Any]] = []
    cursor = 0
    changed = False
    for entry in reversed(items):
        if cursor >= len(history):
            result.append(entry)
            continue
        if entry["method"] == MANUAL_EDIT:
            names = entry.get("undo_names", [])
            start = _find(history, names, cursor)
            if start is not None:
                if start > cursor:  # further GUI transactions right after it: the same manual edit
                    entry = {**entry, "undo_names": history[cursor:start] + names}
                    changed = True
                cursor = start + len(names)  # already noted
            result.append(entry)
            continue
        try:
            position = history.index(entry.get("undo_name", ""), cursor)
        except ValueError:
            changed = True  # undone by the user
            continue
        foreign = history[cursor:position]
        if foreign:
            result.append({"method": MANUAL_EDIT, "undo_names": foreign, "time": _now()})
            changed = True
        result.append(entry)
        cursor = position + 1
    result.reverse()
    if changed:
        _write(doc, result)
    return result


def _find(history: list[str], names: list[str], start: int) -> int | None:
    """Index of the first occurrence of ``names`` as a run in ``history`` from ``start`` on."""
    for index in range(start, len(history) - len(names) + 1):
        if history[index : index + len(names)] == names:
            return index
    return None


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
    existing = [point["name"] for point in storepoints(items)]
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
        marker.Steps = len(items) - (storepoints(items)[-1]["position"] + 1 if existing else 0)
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
