"""Dispatcher that runs calls on the Qt main thread.

A worker thread emits a signal with a queued connection to an object owned by the main
thread; Qt delivers it through the main event loop, so no polling timer is needed.

Queued signals are also delivered inside nested event loops (modal dialogs, task panels).
A ``busy_check`` therefore rejects jobs while the user is inside such an interaction instead
of running them re-entrantly in the middle of a user command.
"""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Callable
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any, TypeVar

from PySide import QtCore

from buddy_bridge.protocol import BUSY_USER_TRANSACTION, GUI_TIMEOUT, INTERNAL_ERROR, RpcError

T = TypeVar("T")
BusyCheck = Callable[[], "str | None"]

_Job = tuple[Callable[[], Any], "Future[Any] | None"]


def _wrap(error: BaseException) -> BaseException:
    """Keep ordinary exceptions; turn SystemExit & co. into an RpcError so no thread dies."""
    if isinstance(error, Exception):
        return error
    return RpcError(INTERNAL_ERROR, f"Aborted by {type(error).__name__} - not allowed in scripts")


class _Invoker(QtCore.QObject):
    requested = QtCore.Signal(object)

    def __init__(self, busy_check: BusyCheck | None) -> None:
        super().__init__()
        self._busy_check = busy_check
        self.requested.connect(self._run, QtCore.Qt.ConnectionType.QueuedConnection)

    @QtCore.Slot(object)
    def _run(self, job: _Job) -> None:
        fn, future = job
        if future is None:
            with contextlib.suppress(BaseException):  # fire-and-forget (logging): never propagate into Qt
                fn()
            return
        if not future.set_running_or_notify_cancel():
            return  # caller gave up (timeout) before the main thread got to it
        busy = self._busy_check() if self._busy_check else None
        if busy:
            future.set_exception(RpcError(BUSY_USER_TRANSACTION, busy))
            return
        try:
            future.set_result(fn())
        except BaseException as error:
            future.set_exception(_wrap(error))


class QtMainThreadDispatcher:
    """Must be created on the Qt main thread (e.g. from a FreeCAD command or startup timer)."""

    def __init__(self, busy_check: BusyCheck | None = None) -> None:
        if QtCore.QCoreApplication.instance() is None:
            raise RuntimeError("QtMainThreadDispatcher needs a running Qt application")
        self._main_thread = threading.current_thread()
        self._invoker = _Invoker(busy_check)

    def call(self, fn: Callable[[], T], timeout: float) -> T:
        if threading.current_thread() is self._main_thread:
            return fn()
        future: Future[T] = Future()
        self._invoker.requested.emit((fn, future))
        try:
            return future.result(timeout)
        except FutureTimeoutError:
            if future.cancel():
                raise RpcError(
                    GUI_TIMEOUT,
                    f"FreeCAD did not respond within {timeout:.0f} s (blocking operation?). "
                    "The request was discarded, the model is unchanged.",
                ) from None
            raise RpcError(
                GUI_TIMEOUT,
                f"The operation is still running in FreeCAD after {timeout:.0f} s and will finish there. "
                "Check the result with get_model_tree, do not simply repeat it.",
            ) from None

    def post(self, fn: Callable[[], object]) -> None:
        if threading.current_thread() is self._main_thread:
            fn()
        else:
            self._invoker.requested.emit((fn, None))
