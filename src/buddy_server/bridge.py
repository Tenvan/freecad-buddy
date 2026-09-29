"""Async access to the FreeCAD bridge with lazy connect, safe reconnect and a status watchdog."""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from buddy_bridge.client import BridgeClient, BridgeConnectionError
from buddy_bridge.protocol import UNAUTHORIZED, RpcError
from buddy_bridge.tokens import read_token
from buddy_server.config import Settings
from buddy_server.events import BridgeState, EventBus


class BridgeUnavailable(Exception):
    """FreeCAD or its bridge cannot be reached; nothing was executed."""


class BridgeTimeout(Exception):
    """The request was sent but no answer arrived in time – it may still complete in FreeCAD."""


HOW_TO_START = (
    "Start FreeCAD and click 'Bridge starten' in the 'FreeCAD Buddy' workbench (or enable autostart)."
)
MAX_WATCHDOG_INTERVAL = 15.0


class Bridge:
    def __init__(self, settings: Settings, bus: EventBus) -> None:
        self._settings = settings
        self._bus = bus
        self._client: BridgeClient | None = None
        self._lock = threading.Lock()  # one request at a time over the single connection
        self.state = "waiting"
        self._last_message = ""
        self.freecad_version: str | None = None

    def _set_state(self, state: str, message: str = "") -> None:
        # Only publish real changes: the watchdog reports the same state every few seconds.
        if (state, message) == (self.state, self._last_message):
            return
        self.state = state
        self._last_message = message
        self._bus.publish(BridgeState(state, message, self.freecad_version))

    def _connect(self) -> BridgeClient:
        token = read_token(self._settings.bridge_token_path)
        if token is None:
            raise BridgeUnavailable(
                f"Kein Bridge-Token unter {self._settings.bridge_token_path}. {HOW_TO_START}"
            )
        client = BridgeClient(
            token,
            host=self._settings.bridge_host,
            port=self._settings.bridge_port,
            connect_timeout=self._settings.connect_timeout,
            request_timeout=self._settings.request_timeout,
        )
        try:
            client.connect()
            status = client.call("system.status", timeout=10)
        except BridgeConnectionError as error:
            client.close()
            raise BridgeUnavailable(f"{error}. {HOW_TO_START}") from None
        except RpcError as error:
            client.close()
            if error.code == UNAUTHORIZED:
                raise BridgeUnavailable(
                    "The bridge rejected the token - does FreeCAD run with a different "
                    f"FREECAD_BUDDY_HOME? Expected: {self._settings.bridge_token_path}"
                ) from None
            raise BridgeUnavailable(f"The bridge refuses the connection: {error.message}") from None
        self.freecad_version = status.get("freecad", {}).get("version")
        self._client = client
        self._set_state("connected", f"FreeCAD {self.freecad_version}")
        return client

    def call_sync(
        self, method: str, params: dict[str, Any] | None = None, timeout: float | None = None
    ) -> Any:
        with self._lock:
            for attempt in (1, 2):
                client = self._client or self._connect()
                try:
                    return client.call(method, params or {}, timeout=timeout)
                except BridgeConnectionError as error:
                    self._client = None
                    if error.timed_out:
                        raise BridgeTimeout(
                            f"{error}. Check with get_model_tree whether the change arrived before "
                            "repeating the call."
                        ) from None
                    if error.sent or attempt == 2:
                        # Never resend: the request may already have run in FreeCAD.
                        self._set_state("waiting", str(error))
                        raise BridgeUnavailable(
                            f"Connection to the bridge lost: {error}. Check the model state with get_model_tree."
                        ) from None
                    # stale connection that failed before sending: reconnect once and send
            raise AssertionError("unreachable")

    async def call(
        self, method: str, params: dict[str, Any] | None = None, timeout: float | None = None
    ) -> Any:
        try:
            return await asyncio.to_thread(self.call_sync, method, params, timeout)
        except BridgeUnavailable as error:
            self._set_state("waiting", str(error))
            raise

    async def watchdog(self) -> None:
        """Keep the status fresh; back off while FreeCAD is unreachable."""
        interval = self._settings.watchdog_interval
        while True:
            try:
                await self.call("system.ping", timeout=5)
                if self.state != "connected":
                    self._set_state("connected", f"FreeCAD {self.freecad_version}")
                interval = self._settings.watchdog_interval
            except (BridgeUnavailable, BridgeTimeout):
                interval = min(interval * 2, MAX_WATCHDOG_INTERVAL)
            except RpcError as error:
                self._set_state("error", error.message)
            await asyncio.sleep(interval)

    def _drop_client(self) -> None:
        # Deliberately without the lock: closing the socket aborts a blocked call instead of waiting
        # for it (which would freeze the event loop for up to the request timeout).
        client, self._client = self._client, None
        if client is not None:
            client.close()

    def reconnect(self) -> None:
        self._drop_client()
        self._set_state("waiting", "Neuverbindung angefordert")

    def close(self) -> None:
        self._drop_client()
