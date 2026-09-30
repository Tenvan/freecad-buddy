"""Method registry: maps JSON-RPC method names to functions and runs them via a dispatcher."""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from buddy_bridge.dispatch import Dispatcher
from buddy_bridge.protocol import (
    ERROR_NAMES,
    INTERNAL_ERROR,
    INVALID_PARAMS,
    METHOD_NOT_FOUND,
    Request,
    RpcError,
)
from buddy_core import stream
from buddy_core.errors import CoreError

DEFAULT_TIMEOUT = 30.0
# never part of a design stream: session, scripts, addons, document lifecycle, read-only calls, exports
NOT_RECORDED = (
    "system.",
    "python.",
    "addons.",
    "select.",
    "view.",
    "print.",
    "document.new",
    "document.open",
    "document.save",
    "document.close",
    "document.revert",
    "document.undo",
    "document.tree",
    "document.object",
    "stream.list",
    "stream.replay",
    "assembly.insert_step",  # carries a local file path and is never replayed
)
CODES_BY_NAME = {name: code for code, name in ERROR_NAMES.items()}


@dataclass(frozen=True)
class Method:
    fn: Callable[..., Any]
    main_thread: bool = True
    timeout: float = DEFAULT_TIMEOUT


def _check_params(method: Method, name: str, params: dict[str, Any]) -> None:
    try:
        inspect.signature(method.fn).bind(**params)
    except TypeError as error:
        raise RpcError(INVALID_PARAMS, f"Invalid parameters for '{name}': {error}") from None


class MethodRegistry:
    def __init__(self) -> None:
        self._methods: dict[str, Method] = {}

    def add(
        self, name: str, fn: Callable[..., Any], *, main_thread: bool = True, timeout: float = DEFAULT_TIMEOUT
    ) -> None:
        if name in self._methods:
            raise ValueError(f"Method '{name}' is already registered")
        self._methods[name] = Method(fn, main_thread, timeout)

    def names(self) -> list[str]:
        return sorted(self._methods)

    def _method(self, name: str) -> Method:
        method = self._methods.get(name)
        if method is None:
            raise RpcError(METHOD_NOT_FOUND, f"Unknown method '{name}'")
        return method

    def function(self, name: str) -> Callable[..., Any]:
        return self._method(name).fn

    def execute(self, name: str, params: dict[str, Any]) -> Any:
        """Run a method on the current thread and record it in the design stream of every document
        it changed (the one execution path, shared by RPC calls and the replay). Methods off the main
        thread never touch the stream: FreeCAD documents are not thread-safe."""
        method = self._method(name)
        _check_params(method, name, params)  # stream entries are data - check them like a request
        before = stream.snapshot() if method.main_thread else None
        result = method.fn(**params)
        payload = result.to_dict() if hasattr(result, "to_dict") else result
        if before is not None:
            stream.record(name, params, payload, before, store=not name.startswith(NOT_RECORDED))
        return payload

    def invoke(self, request: Request, dispatcher: Dispatcher) -> Any:
        method = self._method(request.method)
        _check_params(method, request.method, request.params)  # reject before the main-thread hop

        def run() -> Any:
            return self.execute(request.method, request.params)

        try:
            return dispatcher.call(run, method.timeout) if method.main_thread else run()
        except RpcError:
            raise
        except CoreError as error:
            raise RpcError(CODES_BY_NAME.get(error.name, INTERNAL_ERROR), error.message, error.data) from None
        except BaseException as error:  # incl. SystemExit from scripts: never kill the connection thread
            raise RpcError(
                INTERNAL_ERROR,
                f"{type(error).__name__}: {error}",
                {"method": request.method},
            ) from error
