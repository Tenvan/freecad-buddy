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

    def function(self, name: str) -> Callable[..., Any]:
        method = self._methods.get(name)
        if method is None:
            raise RpcError(METHOD_NOT_FOUND, f"Unknown method '{name}'")
        return method.fn

    def execute(self, name: str, params: dict[str, Any]) -> Any:
        """Run a method on the current thread and record it in the design stream of every document
        it changed (the one execution path, shared by RPC calls and the replay)."""
        fn = self.function(name)
        try:
            inspect.signature(fn).bind(**params)  # stream entries are data - check them like a request
        except TypeError as error:
            raise RpcError(INVALID_PARAMS, f"Invalid parameters for '{name}': {error}") from None
        before = stream.snapshot()
        result = fn(**params)
        payload = result.to_dict() if hasattr(result, "to_dict") else result
        stream.record(name, params, payload, before, store=not name.startswith(NOT_RECORDED))
        return payload

    def invoke(self, request: Request, dispatcher: Dispatcher) -> Any:
        method = self._methods.get(request.method)
        if method is None:
            raise RpcError(METHOD_NOT_FOUND, f"Unknown method '{request.method}'")
        try:
            inspect.signature(method.fn).bind(**request.params)
        except TypeError as error:
            raise RpcError(INVALID_PARAMS, f"Invalid parameters for '{request.method}': {error}") from None

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
