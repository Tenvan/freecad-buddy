"""Where bridge methods run.

FreeCAD's document and GUI API is only safe on the Qt main thread. The server threads
therefore hand every FreeCAD call to a dispatcher. ``InlineDispatcher`` serialises calls
on the caller's thread (headless use, tests); ``qt_dispatcher.QtMainThreadDispatcher``
marshals them onto the Qt main thread.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Protocol, TypeVar

T = TypeVar("T")


class Dispatcher(Protocol):
    def call(self, fn: Callable[[], T], timeout: float) -> T:
        """Run ``fn`` in the dispatcher's context and return its result (blocking)."""
        ...

    def post(self, fn: Callable[[], object]) -> None:
        """Run ``fn`` in the dispatcher's context without waiting for it."""
        ...


class InlineDispatcher:
    """Runs calls on the calling thread, one at a time."""

    def __init__(self) -> None:
        self._lock = threading.Lock()

    def call(self, fn: Callable[[], T], timeout: float) -> T:
        with self._lock:
            return fn()

    def post(self, fn: Callable[[], object]) -> None:
        with self._lock:
            fn()
