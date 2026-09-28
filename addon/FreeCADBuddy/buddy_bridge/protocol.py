"""JSON-RPC 2.0 over newline-delimited JSON (one UTF-8 JSON object per line).

Only named parameters and requests with an id are supported; notifications and batches
are rejected. See ``docs/architecture.md`` (RPC-Vertrag) for the method namespace.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

JSONRPC_VERSION = "2.0"
MAX_MESSAGE_BYTES = 32 * 1024 * 1024

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
UNAUTHORIZED = 1001
BUSY_USER_TRANSACTION = 1002
NOT_FOUND = 1003
AMBIGUOUS = 1004
RECOMPUTE_FAILED = 1005
SKETCH_INVALID = 1006
UNSUPPORTED = 1007
VALIDATION = 1008
GUI_TIMEOUT = 1009

ERROR_NAMES: dict[int, str] = {
    PARSE_ERROR: "parse_error",
    INVALID_REQUEST: "invalid_request",
    METHOD_NOT_FOUND: "method_not_found",
    INVALID_PARAMS: "invalid_params",
    INTERNAL_ERROR: "internal_error",
    UNAUTHORIZED: "unauthorized",
    BUSY_USER_TRANSACTION: "busy_user_transaction",
    NOT_FOUND: "not_found",
    AMBIGUOUS: "ambiguous",
    RECOMPUTE_FAILED: "recompute_failed",
    SKETCH_INVALID: "sketch_invalid",
    UNSUPPORTED: "unsupported",
    VALIDATION: "validation",
    GUI_TIMEOUT: "gui_timeout",
}

RequestId = int | str


class RpcError(Exception):
    """Error that travels to the peer as a JSON-RPC error object."""

    def __init__(self, code: int, message: str, data: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data or {}

    @property
    def name(self) -> str:
        return ERROR_NAMES.get(self.code, "error")


@dataclass(frozen=True)
class Request:
    id: RequestId
    method: str
    params: dict[str, Any] = field(default_factory=dict)


def encode(message: dict[str, Any]) -> bytes:
    data = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(data) > MAX_MESSAGE_BYTES:
        raise RpcError(INTERNAL_ERROR, f"Nachricht zu groß ({len(data)} Bytes, max. {MAX_MESSAGE_BYTES})")
    return data


def decode(line: bytes) -> Any:
    if len(line) > MAX_MESSAGE_BYTES:
        raise RpcError(INVALID_REQUEST, f"Nachricht zu groß (max. {MAX_MESSAGE_BYTES} Bytes)")
    try:
        return json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RpcError(PARSE_ERROR, f"Ungültiges JSON: {error}") from None


def parse_request(message: Any) -> Request:
    if not isinstance(message, dict):
        raise RpcError(INVALID_REQUEST, "Anfrage muss ein JSON-Objekt sein")
    if message.get("jsonrpc") != JSONRPC_VERSION:
        raise RpcError(INVALID_REQUEST, "Feld 'jsonrpc' muss '2.0' sein")
    request_id = message.get("id")
    if isinstance(request_id, bool) or not isinstance(request_id, int | str):
        raise RpcError(
            INVALID_REQUEST, "Feld 'id' (Zahl oder Text) fehlt; Notifications werden nicht unterstützt"
        )
    method = message.get("method")
    if not isinstance(method, str) or not method:
        raise RpcError(INVALID_REQUEST, "Feld 'method' fehlt")
    params = message.get("params", {})
    if not isinstance(params, dict):
        raise RpcError(INVALID_PARAMS, "Nur benannte Parameter (JSON-Objekt) werden unterstützt")
    return Request(id=request_id, method=method, params=params)


def request_message(
    request_id: RequestId, method: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "method": method, "params": params or {}}


def result_message(request_id: RequestId | None, result: Any) -> dict[str, Any]:
    return {"jsonrpc": JSONRPC_VERSION, "id": request_id, "result": result}


def error_message(request_id: RequestId | None, error: RpcError) -> dict[str, Any]:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "id": request_id,
        "error": {"code": error.code, "message": error.message, "data": {"name": error.name, **error.data}},
    }


def error_from_message(message: dict[str, Any]) -> RpcError:
    error = message.get("error") or {}
    data = dict(error.get("data") or {})
    data.pop("name", None)
    return RpcError(
        int(error.get("code", INTERNAL_ERROR)), str(error.get("message", "Unbekannter Fehler")), data
    )
