"""Synchronous bridge client (standard library only).

Used by developer tools, tests and the FreeCAD Buddy server.
"""

from __future__ import annotations

import contextlib
import itertools
import socket
from types import TracebackType
from typing import Any

from buddy_bridge import protocol
from buddy_bridge.protocol import RpcError

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876


class BridgeConnectionError(ConnectionError):
    """Transport failure. ``sent`` tells whether the request may already have reached FreeCAD –
    then it must not be retried (it might be executed twice)."""

    def __init__(self, message: str, *, sent: bool = False, timed_out: bool = False) -> None:
        super().__init__(message)
        self.sent = sent
        self.timed_out = timed_out


class BridgeClient:
    def __init__(
        self,
        token: str,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        connect_timeout: float = 5.0,
        request_timeout: float = 45.0,
    ) -> None:
        self._token = token
        self._address = (host, port)
        self._connect_timeout = connect_timeout
        self._request_timeout = request_timeout
        self._ids = itertools.count(1)
        self._sock: socket.socket | None = None
        self._reader: Any = None
        self.hello: dict[str, Any] = {}

    @property
    def connected(self) -> bool:
        return self._sock is not None

    def connect(self) -> dict[str, Any]:
        try:
            self._sock = socket.create_connection(self._address, timeout=self._connect_timeout)
        except OSError as error:
            host, port = self._address
            raise BridgeConnectionError(f"Bridge at {host}:{port} not reachable: {error}") from None
        self._reader = self._sock.makefile("rb")
        try:
            self.hello = self.call("auth.hello", {"token": self._token})
        except BaseException:
            self.close()
            raise
        return self.hello

    def call(self, method: str, params: dict[str, Any] | None = None, timeout: float | None = None) -> Any:
        sock = self._sock
        if sock is None:
            raise BridgeConnectionError("Nicht verbunden")
        request_id = next(self._ids)
        sent = False
        try:
            sock.settimeout(timeout or self._request_timeout)
            sock.sendall(protocol.encode(protocol.request_message(request_id, method, params)))
            sent = True
            line = self._reader.readline(protocol.MAX_MESSAGE_BYTES + 1)
        except TimeoutError:
            self.close()
            raise BridgeConnectionError(
                f"Timeout for '{method}' - the operation may still be running in FreeCAD",
                sent=sent,
                timed_out=True,
            ) from None
        except (OSError, AttributeError, ValueError) as error:  # socket/reader closed concurrently
            self.close()
            raise BridgeConnectionError(f"Connection to the bridge lost: {error}", sent=sent) from None
        if not line:
            self.close()
            raise BridgeConnectionError("The bridge closed the connection", sent=sent)
        message = protocol.decode(line)
        if message.get("id") is None and "error" in message:
            self.close()  # connection-level rejection (auth, client limit)
            raise protocol.error_from_message(message)
        if message.get("id") != request_id:
            self.close()
            raise BridgeConnectionError("Response does not match the request (id)", sent=True)
        if "error" in message:
            raise protocol.error_from_message(message)
        return message.get("result")

    def close(self) -> None:
        """Close the connection; safe to call from another thread to abort a blocked call."""
        sock, reader = self._sock, self._reader
        self._sock = None
        self._reader = None
        if sock is not None:
            with contextlib.suppress(OSError):
                sock.shutdown(socket.SHUT_RDWR)
        for closable in (reader, sock):
            if closable is not None:
                with contextlib.suppress(OSError):
                    closable.close()

    def __enter__(self) -> BridgeClient:
        self.connect()
        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: TracebackType | None
    ) -> None:
        self.close()


__all__ = ["DEFAULT_HOST", "DEFAULT_PORT", "BridgeClient", "BridgeConnectionError", "RpcError"]
