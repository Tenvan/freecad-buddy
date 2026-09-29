"""Review finding #1: a request that may already have reached FreeCAD must never be resent."""

from pathlib import Path
from typing import Any

import pytest

from buddy_bridge.client import BridgeConnectionError
from buddy_bridge.protocol import UNAUTHORIZED, RpcError
from buddy_server.bridge import Bridge, BridgeTimeout, BridgeUnavailable
from buddy_server.events import EventBus

from .conftest import make_settings


class FakeClient:
    def __init__(self, errors: list[BaseException | None]) -> None:
        self.errors = errors
        self.calls = 0
        self.closed = False

    def call(self, method: str, params: Any = None, timeout: float | None = None) -> Any:
        self.calls += 1
        error = self.errors.pop(0) if self.errors else None
        if error is not None:
            raise error
        return {"ok": True}

    def close(self) -> None:
        self.closed = True


def _bridge(tmp_path: Path, clients: list[FakeClient]) -> Bridge:
    bridge = Bridge(make_settings(tmp_path, 1), EventBus())
    pool = iter(clients)

    def connect() -> Any:  # like Bridge._connect: remember the live client
        bridge._client = next(pool)  # type: ignore[assignment]
        return bridge._client

    bridge._connect = connect  # type: ignore[method-assign]
    return bridge


def test_failure_before_sending_is_retried_once(tmp_path: Path) -> None:
    stale, fresh = FakeClient([BridgeConnectionError("stale", sent=False)]), FakeClient([])
    bridge = _bridge(tmp_path, [stale, fresh])

    assert bridge.call_sync("feature.pad") == {"ok": True}
    assert (stale.calls, fresh.calls) == (1, 1)


def test_failure_after_sending_is_not_retried(tmp_path: Path) -> None:
    first, second = FakeClient([BridgeConnectionError("lost", sent=True)]), FakeClient([])
    bridge = _bridge(tmp_path, [first, second])

    with pytest.raises(BridgeUnavailable, match="get_model_tree"):
        bridge.call_sync("feature.pad")
    assert second.calls == 0


def test_timeout_is_reported_as_timeout_not_retried(tmp_path: Path) -> None:
    first, second = FakeClient([BridgeConnectionError("slow", sent=True, timed_out=True)]), FakeClient([])
    bridge = _bridge(tmp_path, [first, second])

    with pytest.raises(BridgeTimeout):
        bridge.call_sync("feature.fillet")
    assert second.calls == 0


def test_rejected_token_is_explained(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "bridge-token").write_text("stale", encoding="utf-8")
    bridge = Bridge(make_settings(tmp_path, 1), EventBus())

    def reject(self: Any) -> None:
        raise RpcError(UNAUTHORIZED, "nope")

    monkeypatch.setattr("buddy_server.bridge.BridgeClient.connect", reject)

    with pytest.raises(BridgeUnavailable, match="rejected the token"):
        bridge.call_sync("system.ping")


def test_reconnect_does_not_wait_for_a_running_call(tmp_path: Path) -> None:
    client = FakeClient([])
    bridge = _bridge(tmp_path, [client])
    bridge.call_sync("system.ping")
    bridge._lock.acquire()  # simulate a long-running call holding the lock
    try:
        bridge.reconnect()  # must return immediately
    finally:
        bridge._lock.release()

    assert client.closed and bridge.state == "waiting"
