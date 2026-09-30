"""One tool call = one named undo step; failures roll the document back."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import FreeCAD

from buddy_core import diagnostics
from buddy_core.errors import BUSY_USER_TRANSACTION, RECOMPUTE_FAILED, CoreError

_open: set[str] = set()
"""Documents with an open Buddy transaction; design tools nest the tools they are built from."""

commits: dict[str, int] = {}
"""Committed Buddy transactions per document; the design stream detects changing calls with it
(``UndoCount`` stops growing once FreeCAD's undo stack is full)."""


def invalid_objects(doc: Any) -> dict[str, str]:
    """Objects whose last recompute failed, mapped to FreeCAD's status text."""
    return {obj.Name: obj.getStatusString() for obj in doc.Objects if not obj.isValid()}


def _user_is_editing(doc: Any) -> bool:
    if doc.HasPendingTransaction:
        return True
    if FreeCAD.GuiUp:
        import FreeCADGui

        gui_doc = FreeCADGui.getDocument(doc.Name)
        if gui_doc is not None and gui_doc.getInEdit() is not None:
            return True
        return bool(FreeCADGui.Control.activeDialog())
    return False


def ensure_user_not_editing(doc: Any) -> None:
    """Refuse to touch a document the user is currently working in (also for undo/save)."""
    if _user_is_editing(doc):
        raise CoreError(
            BUSY_USER_TRANSACTION,
            f"Document '{doc.Label}' is being edited (open transaction, task panel or "
            "edit mode). Finish the edit in FreeCAD and try again.",
        )


@contextmanager
def transaction(doc: Any, label: str) -> Iterator[None]:
    """Run the block as a single undoable step and recompute.

    Raises ``busy_user_transaction`` without touching the document while the user edits,
    and ``recompute_failed`` (after rollback) if the block leaves new invalid objects.
    Nested calls join the outer transaction, which owns the undo step and the checks.
    """
    if doc.Name in _open:
        yield
        return
    ensure_user_not_editing(doc)
    before = invalid_objects(doc)
    if not doc.UndoMode:
        doc.UndoMode = 1
    doc.openTransaction(label)
    _open.add(doc.Name)
    try:
        yield
        doc.recompute()
        failed = {name: status for name, status in invalid_objects(doc).items() if name not in before}
        if failed:
            raise CoreError(
                RECOMPUTE_FAILED,
                "Recompute failed: " + "; ".join(f"{doc.getObject(n).Label}: {s}" for n, s in failed.items()),
                {
                    "objects": [
                        {"name": n, "label": doc.getObject(n).Label, "status": s} for n, s in failed.items()
                    ],
                    "hints": diagnostics.hints(list(failed.values())),
                },
            )
        doc.commitTransaction()
        commits[doc.Name] = commits.get(doc.Name, 0) + 1
    except BaseException as error:
        doc.abortTransaction()
        doc.recompute()
        if isinstance(error, CoreError):
            error.data.setdefault("state", "rolled_back")
        raise
    finally:
        _open.discard(doc.Name)
