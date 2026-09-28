"""Domain errors of the core. The bridge maps ``CoreError.name`` onto JSON-RPC error codes.

Must not import FreeCAD, so the bridge registry can use it without FreeCAD.
"""

from __future__ import annotations

from typing import Any

BUSY_USER_TRANSACTION = "busy_user_transaction"
NOT_FOUND = "not_found"
AMBIGUOUS = "ambiguous"
RECOMPUTE_FAILED = "recompute_failed"
SKETCH_INVALID = "sketch_invalid"
UNSUPPORTED = "unsupported"
VALIDATION = "validation"


class CoreError(Exception):
    def __init__(self, name: str, message: str, data: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.name = name
        self.message = message
        self.data = data or {}


def not_found(message: str, **data: Any) -> CoreError:
    return CoreError(NOT_FOUND, message, data)


def validation(message: str, **data: Any) -> CoreError:
    return CoreError(VALIDATION, message, data)
