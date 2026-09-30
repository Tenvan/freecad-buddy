"""GUI checks from the acceptance catalogue (``docs/acceptance.md``), run inside the FreeCAD GUI.

Transition until the GUI test run (backlog E-27): with ``execute_python`` switched on by Ralf, load
this file from the repository and set ``result``, for example::

    ns = {}
    exec(open(r"<repo>/tools/gui_checks.py", encoding="utf-8").read(), ns)
    result = {
        "G13": ns["task_panels"]("Abnahme_G13", ["Loft_Funnel", "Helix_Spring", "Sphere_Knob"]),
        "G14": ns["storepoint_tree"]("Abnahme_G15", "Storepoint_Mulde"),
    }

Everything goes through FreeCADGui and Qt in-process - no mouse, no screen coordinates. A synthetic
mouse double-click in the tree (``QTest.mouseDClick``) proved flaky (sometimes nothing, sometimes only
the marker selected), so the double-click is checked at the ViewProvider; the real mouse stays manual.
"""

from typing import Any

import FreeCAD
import FreeCADGui

try:
    from PySide6 import QtWidgets
except ImportError:  # FreeCAD's PySide shim
    from PySide import QtWidgets  # type: ignore[no-redef]


def _pump() -> None:
    for _ in range(5):
        QtWidgets.QApplication.processEvents()


def _document(label: str) -> Any:
    return next(doc for doc in FreeCAD.listDocuments().values() if label in (doc.Name, doc.Label))


def task_panels(document: str, labels: list[str]) -> dict[str, Any]:
    """G13: every feature opens its task panel and closes again; the document stays valid."""
    doc = _document(document)
    gui_doc = FreeCADGui.getDocument(doc.Name)
    found: dict[str, Any] = {}
    for label in labels:
        opened = gui_doc.setEdit(doc.getObjectsByLabel(label)[0], 0)
        _pump()
        active = bool(FreeCADGui.Control.activeDialog())
        gui_doc.resetEdit()
        FreeCADGui.Control.closeDialog()
        _pump()
        found[label] = {
            "opened": bool(opened),
            "panel": active,
            "closed": not FreeCADGui.Control.activeDialog(),
        }
    doc.recompute()
    found["valid"] = all(obj.isValid() for obj in doc.Objects)
    return found


def _tree_items(document_label: str) -> dict[str, Any]:
    """Items of one document in the model tree, by label."""
    tree = next(t for t in FreeCADGui.getMainWindow().findChildren(QtWidgets.QTreeWidget) if t.isVisible())
    roots = (tree.topLevelItem(i) for i in range(tree.topLevelItemCount()))
    pending = [item for item in roots if item.text(0) == document_label]
    items: dict[str, Any] = {}
    while pending:
        item = pending.pop()
        items.setdefault(item.text(0), item)
        pending.extend(item.child(i) for i in range(item.childCount()))
    return items


def storepoint_tree(document: str, marker_label: str) -> dict[str, Any]:
    """G14: marker icon, description column of the linked feature, double-click selects the feature."""
    doc = _document(document)
    marker = doc.getObjectsByLabel(marker_label)[0]
    feature = marker.Feature
    items = _tree_items(doc.Label)
    marker_item, feature_item = items[marker_label], items[feature.Label]
    found: dict[str, Any] = {
        "icon": not marker_item.icon(0).isNull(),
        "description": feature_item.text(1),
        "description_is_label2": feature_item.text(1) == feature.Label2 != "",
        "tooltip": feature_item.toolTip(0),
    }
    FreeCADGui.Selection.clearSelection()
    view = marker.ViewObject
    found["double_click_handled"] = bool(view.Proxy.doubleClicked(view))
    _pump()
    found["selected"] = [obj.Label for obj in FreeCADGui.Selection.getSelection()]
    found["selects_feature"] = found["selected"] == [feature.Label]
    found["no_panel"] = not FreeCADGui.Control.activeDialog()
    if not found["no_panel"]:
        FreeCADGui.Control.closeDialog()
    return found
