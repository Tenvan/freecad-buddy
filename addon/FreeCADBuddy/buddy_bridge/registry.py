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
from buddy_core.errors import CoreError

DEFAULT_TIMEOUT = 30.0
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

    def invoke(self, request: Request, dispatcher: Dispatcher) -> Any:
        method = self._methods.get(request.method)
        if method is None:
            raise RpcError(METHOD_NOT_FOUND, f"Unknown method '{request.method}'")
        try:
            inspect.signature(method.fn).bind(**request.params)
        except TypeError as error:
            raise RpcError(INVALID_PARAMS, f"Invalid parameters for '{request.method}': {error}") from None

        def run() -> Any:
            result = method.fn(**request.params)
            return result.to_dict() if hasattr(result, "to_dict") else result

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
