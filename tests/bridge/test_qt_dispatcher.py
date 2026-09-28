"""The Qt dispatcher must run work on the main thread even when called from worker threads.

Runs headless: a bare QCoreApplication stands in for FreeCAD's GUI event loop.
"""

import threading
import time
from collections.abc import Callable

import pytest
from PySide import QtCore

from buddy_bridge.protocol import GUI_TIMEOUT, RpcError
from buddy_bridge.qt_dispatcher import QtMainThreadDispatcher


@pytest.fixture(scope="module")
def app() -> QtCore.QCoreApplication:
    return QtCore.QCoreApplication.instance() or QtCore.QCoreApplication([])


def _pump_until(done: Callable[[], bool], app: QtCore.QCoreApplication, timeout: float = 5.0) -> None:
    deadline = time.monotonic() + timeout
    while not done() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.005)


def test_call_from_worker_runs_on_main_thread(app: QtCore.QCoreApplication) -> None:
    dispatcher = QtMainThreadDispatcher()
    main = threading.current_thread()
    results: list[object] = []

    worker = threading.Thread(
        target=lambda: results.append(dispatcher.call(lambda: threading.current_thread() is main, 5))
    )
    worker.start()
    _pump_until(lambda: bool(results), app)
    worker.join(1)

    assert results == [True]


def test_exceptions_propagate_to_caller(app: QtCore.QCoreApplication) -> None:
    dispatcher = QtMainThreadDispatcher()
    errors: list[BaseException] = []

    def call() -> None:
        try:
            dispatcher.call(lambda: 1 / 0, 5)
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=call)
    worker.start()
    _pump_until(lambda: bool(errors), app)
    worker.join(1)

    assert isinstance(errors[0], ZeroDivisionError)


def test_timeout_cancels_job_that_never_ran(app: QtCore.QCoreApplication) -> None:
    dispatcher = QtMainThreadDispatcher()
    ran: list[bool] = []
    errors: list[RpcError] = []

    def call() -> None:
        try:
            dispatcher.call(lambda: ran.append(True), 0.2)
        except RpcError as error:
            errors.append(error)

    worker = threading.Thread(target=call)
    worker.start()
    worker.join(2)  # main loop is deliberately not pumped: the job cannot run
    _pump_until(lambda: False, app, timeout=0.2)  # deliver the queued job late

    assert errors and errors[0].code == GUI_TIMEOUT
    assert ran == []


def test_call_on_main_thread_runs_inline(app: QtCore.QCoreApplication) -> None:
    assert QtMainThreadDispatcher().call(lambda: threading.current_thread() is threading.main_thread(), 1)


def test_post_is_delivered_without_waiting(app: QtCore.QCoreApplication) -> None:
    dispatcher = QtMainThreadDispatcher()
    seen: list[bool] = []

    worker = threading.Thread(target=lambda: dispatcher.post(lambda: seen.append(True)))
    worker.start()
    worker.join(1)
    _pump_until(lambda: bool(seen), app)

    assert seen == [True]


def test_busy_gui_rejects_job_without_running_it(app: QtCore.QCoreApplication) -> None:
    from buddy_bridge.protocol import BUSY_USER_TRANSACTION

    dispatcher = QtMainThreadDispatcher(busy_check=lambda: "Dialog offen")
    ran: list[bool] = []
    errors: list[RpcError] = []

    def call() -> None:
        try:
            dispatcher.call(lambda: ran.append(True), 5)
        except RpcError as error:
            errors.append(error)

    worker = threading.Thread(target=call)
    worker.start()
    _pump_until(lambda: bool(errors), app)
    worker.join(1)

    assert errors and errors[0].code == BUSY_USER_TRANSACTION
    assert ran == []
