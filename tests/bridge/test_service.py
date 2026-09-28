from pathlib import Path

from buddy_bridge.client import BridgeClient
from buddy_bridge.dispatch import InlineDispatcher
from buddy_bridge.service import BridgeService
from buddy_bridge.tokens import read_token


def test_service_creates_token_and_serves_status(tmp_path: Path) -> None:
    token_path = tmp_path / "bridge-token"
    service = BridgeService(InlineDispatcher(), token_path=token_path, port=0)

    service.start()
    try:
        token = read_token(token_path)
        assert token
        with BridgeClient(token, port=service.port) as client:
            assert client.call("system.status")["bridge_version"]
        assert "läuft auf 127.0.0.1" in service.describe()
    finally:
        service.stop()

    assert not service.running
    assert "gestoppt" in service.describe()


def test_start_is_idempotent(tmp_path: Path) -> None:
    service = BridgeService(InlineDispatcher(), token_path=tmp_path / "t", port=0)
    service.start()
    port = service.port
    try:
        service.start()
        assert service.port == port
    finally:
        service.stop()
