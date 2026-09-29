import socket
import time

import FreeCAD
import pytest

from buddy_bridge import protocol
from buddy_bridge.client import BridgeClient, BridgeConnectionError
from buddy_bridge.dispatch import InlineDispatcher
from buddy_bridge.protocol import RpcError
from buddy_bridge.registry import MethodRegistry
from buddy_bridge.server import MAX_CLIENTS, BridgeServer

from .conftest import TOKEN


def _client(server: BridgeServer, token: str = TOKEN) -> BridgeClient:
    return BridgeClient(token, port=server.port, connect_timeout=2, request_timeout=5)


def test_authenticated_ping(server: BridgeServer) -> None:
    with _client(server) as client:
        assert client.hello["bridge_version"]
        assert client.call("system.ping")["pong"] is True


def test_status_reports_freecad_and_no_missing_types(server: BridgeServer) -> None:
    with _client(server) as client:
        status = client.call("system.status")

    assert status["freecad"]["version"] == ".".join(FreeCAD.Version()[:3])
    assert status["missing_types"] == []
    assert isinstance(status["documents"], list)


def test_wrong_token_is_rejected_and_connection_closed(server: BridgeServer) -> None:
    client = _client(server, token="wrong")

    with pytest.raises(RpcError) as info:
        client.connect()

    assert info.value.code == protocol.UNAUTHORIZED
    with pytest.raises(BridgeConnectionError):
        client.call("system.ping")


def test_request_before_hello_is_rejected(server: BridgeServer) -> None:
    with socket.create_connection(("127.0.0.1", server.port), timeout=5) as sock:
        sock.sendall(protocol.encode(protocol.request_message(1, "system.ping")))
        reply = protocol.decode(sock.makefile("rb").readline())

    assert reply["error"]["code"] == protocol.UNAUTHORIZED


def test_garbage_line_gets_parse_error_but_connection_survives(server: BridgeServer) -> None:
    with _client(server) as client:
        assert client._sock is not None
        client._sock.sendall(b"not json\n")
        reply = protocol.decode(client._reader.readline())
        assert reply["error"]["code"] == protocol.PARSE_ERROR

        assert client.call("system.ping")["pong"] is True


def test_unknown_method_and_invalid_params(server: BridgeServer) -> None:
    with _client(server) as client:
        with pytest.raises(RpcError) as unknown:
            client.call("system.nope")
        with pytest.raises(RpcError) as invalid:
            client.call("system.ping", {"unexpected": 1})

    assert unknown.value.code == protocol.METHOD_NOT_FOUND
    assert invalid.value.code == protocol.INVALID_PARAMS


def test_exception_in_method_becomes_internal_error() -> None:
    registry = MethodRegistry()

    def boom() -> None:
        raise ValueError("kaputt")

    registry.add("test.boom", boom)
    bridge = BridgeServer(registry, InlineDispatcher(), TOKEN, port=0)
    bridge.start()
    try:
        with _client(bridge) as client, pytest.raises(RpcError) as info:
            client.call("test.boom")
    finally:
        bridge.stop()

    assert info.value.code == protocol.INTERNAL_ERROR
    assert "ValueError: kaputt" in info.value.message


def test_only_loopback_binding_is_allowed(registry: MethodRegistry) -> None:
    for host in ("0.0.0.0", "192.168.1.10", "localhost"):
        with pytest.raises(ValueError, match="loopback"):
            BridgeServer(registry, InlineDispatcher(), TOKEN, host=host)


def test_client_limit(server: BridgeServer) -> None:
    clients = [_client(server) for _ in range(MAX_CLIENTS)]
    for client in clients:
        client.connect()
    try:
        extra = _client(server)
        with pytest.raises((RpcError, BridgeConnectionError)):
            extra.connect()
            extra.call("system.ping")
    finally:
        for client in clients:
            client.close()


def test_stop_disconnects_clients(server: BridgeServer) -> None:
    client = _client(server)
    client.connect()

    server.stop()

    with pytest.raises(BridgeConnectionError):
        client.call("system.ping")
    assert not server.running


def test_connection_slot_is_released_after_disconnect(server: BridgeServer) -> None:
    with _client(server) as client:
        client.call("system.ping")
    deadline = time.monotonic() + 2
    while server.client_count() and time.monotonic() < deadline:
        time.sleep(0.01)

    assert server.client_count() == 0


def test_client_reports_unreachable_bridge() -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]

    with pytest.raises(BridgeConnectionError, match="not reachable"):
        BridgeClient(TOKEN, port=free_port, connect_timeout=1).connect()
