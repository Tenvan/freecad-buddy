"""TCP server of the bridge: loopback only, token handshake, one thread per connection."""

from __future__ import annotations

import contextlib
import ipaddress
import socket
import threading
import time
from collections.abc import Callable
from typing import Any, BinaryIO

from buddy_bridge import __version__, protocol
from buddy_bridge.dispatch import Dispatcher
from buddy_bridge.protocol import INTERNAL_ERROR, INVALID_REQUEST, UNAUTHORIZED, RpcError
from buddy_bridge.registry import MethodRegistry
from buddy_bridge.tokens import tokens_match

MAX_CLIENTS = 4
HANDSHAKE_TIMEOUT = 10.0
REJECT_LOG_INTERVAL = 30.0

LogFn = Callable[[str, str], None]  # (level, message); level in {"info", "warning", "error"}


def _no_log(level: str, message: str) -> None:
    pass


def _is_loopback(host: str) -> bool:
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class BridgeServer:
    def __init__(
        self,
        registry: MethodRegistry,
        dispatcher: Dispatcher,
        token: str,
        host: str = "127.0.0.1",
        port: int = 9876,
        log: LogFn = _no_log,
    ) -> None:
        if not _is_loopback(host):
            raise ValueError(f"Die Bridge darf nur an eine Loopback-Adresse binden, nicht an '{host}'")
        self._registry = registry
        self._dispatcher = dispatcher
        self._token = token
        self._host = host
        self._requested_port = port
        self._log = log
        self._sock: socket.socket | None = None
        self._accept_thread: threading.Thread | None = None
        self._connections: set[socket.socket] = set()
        self._lock = threading.Lock()
        self._running = threading.Event()
        self._last_reject_log = -REJECT_LOG_INTERVAL

    @property
    def port(self) -> int:
        if self._sock is None:
            return self._requested_port
        return self._sock.getsockname()[1]

    @property
    def running(self) -> bool:
        return self._running.is_set()

    def client_count(self) -> int:
        with self._lock:
            return len(self._connections)

    def start(self) -> None:
        if self.running:
            return
        self._sock = socket.create_server((self._host, self._requested_port), reuse_port=False)
        self._running.set()
        self._accept_thread = threading.Thread(
            target=self._accept_loop, name="buddy-bridge-accept", daemon=True
        )
        self._accept_thread.start()
        self._log("info", f"Bridge lauscht auf {self._host}:{self.port}")

    def stop(self) -> None:
        if not self.running:
            return
        self._running.clear()
        if self._sock is not None:
            self._sock.close()
        with self._lock:
            connections = list(self._connections)
        for conn in connections:
            self._shutdown(conn)
        if self._accept_thread is not None:
            self._accept_thread.join(timeout=5)
        self._log("info", "Bridge gestoppt")

    def _accept_loop(self) -> None:
        assert self._sock is not None
        while self.running:
            try:
                conn, address = self._sock.accept()
            except OSError:
                break  # socket closed by stop()
            if not _is_loopback(address[0]):
                conn.close()
                continue
            with self._lock:
                too_many = len(self._connections) >= MAX_CLIENTS
                if not too_many:
                    self._connections.add(conn)
            if too_many:
                self._reject(conn, RpcError(INVALID_REQUEST, f"Zu viele Verbindungen (max. {MAX_CLIENTS})"))
                continue
            threading.Thread(
                target=self._serve_connection, args=(conn,), name="buddy-bridge-conn", daemon=True
            ).start()

    def _serve_connection(self, conn: socket.socket) -> None:
        reader = conn.makefile("rb")
        try:
            conn.settimeout(HANDSHAKE_TIMEOUT)
            if not self._handshake(conn, reader):
                return
            conn.settimeout(None)
            while self.running:
                line = reader.readline(protocol.MAX_MESSAGE_BYTES + 1)
                if not line:
                    return
                if not self._handle_line(conn, line):
                    return
        except (OSError, TimeoutError):
            return
        finally:
            reader.close()
            with self._lock:
                self._connections.discard(conn)
            self._shutdown(conn)

    def _handshake(self, conn: socket.socket, reader: BinaryIO) -> bool:
        line = reader.readline(protocol.MAX_MESSAGE_BYTES + 1)
        if not line:
            return False
        try:
            request = protocol.parse_request(protocol.decode(line))
            if request.method != "auth.hello" or not tokens_match(self._token, request.params.get("token")):
                raise RpcError(UNAUTHORIZED, "Anmeldung fehlgeschlagen: erst 'auth.hello' mit gültigem Token")
        except RpcError as error:
            now = time.monotonic()
            if now - self._last_reject_log > REJECT_LOG_INTERVAL:  # a retrying client must not flood the log
                self._last_reject_log = now
                self._log("warning", f"Verbindung abgewiesen: {error.message}")
            self._send(conn, protocol.error_message(None, error))
            return False
        self._send(conn, protocol.result_message(request.id, {"bridge_version": __version__}))
        return True

    def _handle_line(self, conn: socket.socket, line: bytes) -> bool:
        request_id: protocol.RequestId | None = None
        try:
            request = protocol.parse_request(protocol.decode(line))
            request_id = request.id
            result: Any = (
                {"bridge_version": __version__}
                if request.method == "auth.hello"
                else self._registry.invoke(request, self._dispatcher)
            )
            response = protocol.result_message(request_id, result)
        except RpcError as error:
            if error.__cause__ is not None:
                self._log("error", f"{error.message}")
            response = protocol.error_message(request_id, error)
        except Exception as error:  # defensive: a request must never end the connection thread
            response = protocol.error_message(
                request_id, RpcError(INTERNAL_ERROR, f"{type(error).__name__}: {error}")
            )
        try:
            return self._send(conn, response)
        except (RpcError, TypeError, ValueError) as error:  # too large or not JSON-serialisable
            reason = (
                error
                if isinstance(error, RpcError)
                else RpcError(INTERNAL_ERROR, f"Antwort nicht serialisierbar: {error}")
            )
            return self._send(conn, protocol.error_message(request_id, reason))

    def _send(self, conn: socket.socket, message: dict[str, Any]) -> bool:
        try:
            conn.sendall(protocol.encode(message))
            return True
        except OSError:
            return False

    def _reject(self, conn: socket.socket, error: RpcError) -> None:
        self._send(conn, protocol.error_message(None, error))
        self._shutdown(conn)

    @staticmethod
    def _shutdown(conn: socket.socket) -> None:
        with contextlib.suppress(OSError):
            conn.shutdown(socket.SHUT_RDWR)
        conn.close()
