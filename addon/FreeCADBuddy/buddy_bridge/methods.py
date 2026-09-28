"""Bridge methods exposed over JSON-RPC. FreeCAD-specific work is delegated to ``buddy_core``."""

from __future__ import annotations

import contextlib
import functools
import io
import time
from typing import Any

import FreeCAD

import buddy_core
from buddy_bridge import __version__
from buddy_bridge.registry import MethodRegistry
from buddy_core import body, compat, documents, features, select, view
from buddy_core import parameters as model_parameters
from buddy_core.addons import status as addon_status
from buddy_core.documents import resolve_document
from buddy_core.errors import validation
from buddy_core.printing import check, export, profile
from buddy_core.result import ToolResult
from buddy_core.sketch import assist, lowlevel, model, profiles
from buddy_core.transaction import transaction


def ping() -> dict[str, Any]:
    return {"pong": True, "time": time.time()}


@functools.cache
def _missing_types() -> tuple[str, ...]:
    # Document types cannot change while FreeCAD is running; probe once.
    return tuple(compat.missing_types())


def status() -> dict[str, Any]:
    active = FreeCAD.ActiveDocument
    return {
        "freecad": compat.freecad_info().as_dict(),
        "bridge_version": __version__,
        "core_version": buddy_core.__version__,
        "missing_types": list(_missing_types()),
        "documents": [
            {"name": doc.Name, "label": doc.Label, "file": doc.FileName}
            for doc in FreeCAD.listDocuments().values()
        ],
        "active_document": active.Name if active else None,
    }


def set_parameters(parameters: dict[str, Any], document: str | None = None) -> ToolResult:
    return model_parameters.set_parameters(resolve_document(document), parameters)


def list_parameters(document: str | None = None) -> list[dict[str, Any]]:
    return model_parameters.list_parameters(resolve_document(document))


def execute_python(code: str, document: str | None = None) -> dict[str, Any]:
    """Opt-in escape hatch (the server only exposes it with FREECAD_BUDDY_ALLOW_PYTHON=1).

    Runs as one undoable transaction; ``result`` in the script namespace is returned.
    """
    doc = resolve_document(document)
    namespace: dict[str, Any] = {"App": FreeCAD, "FreeCAD": FreeCAD, "doc": doc}
    output = io.StringIO()
    with transaction(doc, "Python-Skript"), contextlib.redirect_stdout(output):
        try:
            exec(compile(code, "<freecad-buddy>", "exec"), namespace)
        except SystemExit:
            raise validation(
                "exit()/SystemExit ist in Skripten nicht erlaubt – Änderungen zurückgerollt"
            ) from None
    value = namespace.get("result")
    try:
        import json

        json.dumps(value)
    except TypeError:
        value = repr(value)
    return {"stdout": output.getvalue(), "result": value}


METHODS: dict[str, tuple[Any, dict[str, Any]]] = {
    "system.ping": (ping, {"main_thread": False}),
    "system.status": (status, {}),
    "document.new": (documents.new_document, {}),
    "document.open": (documents.open_document, {}),
    "document.save": (documents.save_document, {}),
    "document.tree": (documents.model_tree, {}),
    "document.object": (documents.get_object, {}),
    "document.delete": (documents.delete_object, {}),
    "document.undo": (documents.undo, {}),
    "parameters.set": (set_parameters, {}),
    "parameters.list": (list_parameters, {}),
    "body.create": (body.create_body, {}),
    "sketch.create": (model.create_sketch, {}),
    "sketch.add_profile": (profiles.add_profile, {}),
    "sketch.add_geometry": (lowlevel.add_geometry, {}),
    "sketch.add_constraints": (lowlevel.add_constraints, {}),
    "sketch.analyze": (model.analyze_sketch, {}),
    "sketch.fully_constrain": (assist.fully_constrain_sketch, {}),
    "feature.pad": (features.pad, {}),
    "feature.pocket": (features.pocket, {}),
    "feature.revolve": (features.revolve, {}),
    "feature.sweep": (features.sweep, {}),
    "feature.hole": (features.hole, {}),
    "feature.fillet": (features.fillet, {}),
    "feature.chamfer": (features.chamfer, {}),
    "feature.shell": (features.shell, {}),
    "feature.pattern": (features.pattern, {}),
    "feature.datum_plane": (features.datum_plane, {}),
    "select.preview": (select.select_geometry, {}),
    "view.set": (view.set_view, {}),
    "view.screenshot": (view.screenshot, {"timeout": 60.0}),
    "addons.status": (addon_status.addon_status, {}),
    "print.get_profile": (profile.get_printer_profile, {}),
    "print.set_profile": (profile.set_printer_profile, {}),
    "print.check": (check.check_printability, {"timeout": 120.0}),
    "print.export": (export.export_body, {"timeout": 120.0}),
    "python.execute": (execute_python, {"timeout": 120.0}),
}


OPT_IN_METHODS = frozenset({"python.execute"})


def build_registry(allow_python: bool = False) -> MethodRegistry:
    """All methods; ``python.execute`` only with an explicit opt-in on the FreeCAD side."""
    registry = MethodRegistry()
    for name, (fn, options) in METHODS.items():
        if name in OPT_IN_METHODS and not allow_python:
            continue
        registry.add(name, fn, **options)
    return registry
