"""Screenshots of the 3D view (GUI only)."""

from __future__ import annotations

import base64
import os
import tempfile
from typing import Any

import FreeCAD

from buddy_core.documents import resolve_document, resolve_object
from buddy_core.errors import UNSUPPORTED, CoreError, validation

VIEWS = {
    "iso": "viewIsometric",
    "front": "viewFront",
    "back": "viewRear",
    "top": "viewTop",
    "bottom": "viewBottom",
    "left": "viewLeft",
    "right": "viewRight",
}
MAX_SIZE = 1600


def screenshot(
    view: str = "iso",
    width: int = 800,
    height: int = 600,
    fit: bool = True,
    isolate: str | None = None,
    document: str | None = None,
) -> dict[str, Any]:
    if not FreeCAD.GuiUp:
        raise CoreError(UNSUPPORTED, "Screenshots sind nur mit laufender FreeCAD-GUI möglich")
    if view != "current" and view not in VIEWS:
        raise validation(f"Unbekannte Ansicht '{view}' (erlaubt: current, {', '.join(VIEWS)})")
    if not (16 <= width <= MAX_SIZE and 16 <= height <= MAX_SIZE):
        raise validation(f"Bildgröße muss zwischen 16 und {MAX_SIZE} Pixeln liegen")

    import FreeCADGui

    doc = resolve_document(document)
    gui_doc = FreeCADGui.getDocument(doc.Name)
    previous_doc = FreeCADGui.ActiveDocument
    FreeCADGui.setActiveDocument(doc.Name)
    active_view = gui_doc.ActiveView
    if active_view is None or not hasattr(active_view, "saveImage") or not hasattr(active_view, "getCamera"):
        raise CoreError(UNSUPPORTED, "Keine 3D-Ansicht aktiv (z. B. Tabelle oder Zeichnung im Vordergrund)")
    camera = active_view.getCamera()
    hidden: list[Any] = []
    if isolate:
        keep = resolve_object(doc, isolate)
        # keep the object, what it is built from and its containers (e.g. the body of a feature)
        keep_names = {
            keep.Name,
            *(o.Name for o in keep.OutListRecursive),
            *(o.Name for o in keep.InListRecursive),
        }
        for obj in doc.Objects:
            view_obj = getattr(obj, "ViewObject", None)
            if view_obj is not None and view_obj.Visibility and obj.Name not in keep_names:
                view_obj.Visibility = False
                hidden.append(view_obj)
    try:
        if view != "current":
            getattr(active_view, VIEWS[view])()
        if fit:
            active_view.fitAll()
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            active_view.saveImage(path, width, height, "Current")
            with open(path, "rb") as image:
                data = base64.b64encode(image.read()).decode("ascii")
        finally:
            os.unlink(path)
    finally:
        for view_obj in hidden:
            view_obj.Visibility = True
        active_view.setCamera(camera)  # leave the user's view as it was
        if previous_doc is not None and previous_doc.Document.Name != doc.Name:
            FreeCADGui.setActiveDocument(previous_doc.Document.Name)
    return {"mime_type": "image/png", "data": data, "width": width, "height": height, "view": view}
