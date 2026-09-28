"""Runs the MCP server (uvicorn) and the bridge watchdog in the current asyncio loop.

Used by both front ends: the Textual TUI runs it as a worker, headless mode directly.
"""

from __future__ import annotations

import asyncio
import contextlib
import socket

import uvicorn
from sse_starlette.sse import AppStatus

from buddy_server.app import build_app
from buddy_server.bridge import Bridge
from buddy_server.config import Settings
from buddy_server.events import EventBus, ServerFailed, ServerStarted


class PortInUse(RuntimeError):
    pass


def ensure_port_free(host: str, port: int) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            raise PortInUse(
                f"Port {port} ist belegt – läuft freecad-buddy schon? Anderen Port mit --port wählen."
            ) from None


SHUTDOWN_GRACE_SECONDS = 2


class ServerRunner:
    def __init__(self, settings: Settings, bus: EventBus, bridge: Bridge | None = None) -> None:
        self.settings = settings
        self.bus = bus
        self.bridge = bridge or Bridge(settings, bus)
        self.tool_names: list[str] = []
        self._server: uvicorn.Server | None = None
        self.started = asyncio.Event()

    async def run(self) -> None:
        try:
            ensure_port_free(self.settings.host, self.settings.port)
        except PortInUse as error:
            self.bus.publish(ServerFailed(str(error)))
            raise
        # sse_starlette keeps a process-wide "should exit" flag; once a previous server shut down it would
        # end every SSE stream of this one immediately (restart from the TUI, several servers in tests).
        AppStatus.should_exit = False
        app, self.tool_names = build_app(self.settings, self.bridge, self.bus)
        config = uvicorn.Config(
            app,
            host=self.settings.host,
            port=self.settings.port,
            log_level="warning",
            lifespan="on",
            access_log=False,
            # Never wait forever for clients that keep connections or streams open.
            timeout_graceful_shutdown=SHUTDOWN_GRACE_SECONDS,
        )
        self._server = uvicorn.Server(config)
        self._server.install_signal_handlers = lambda: None  # type: ignore[method-assign]  # front end owns Ctrl+C
        watchdog = asyncio.create_task(self.bridge.watchdog())
        serving = asyncio.create_task(self._server.serve())
        while not self._server.started and not serving.done():
            await asyncio.sleep(0.02)
        if self._server.started:
            self.started.set()
            self.bus.publish(ServerStarted(self.settings.url, self.settings.allow_python))
        try:
            await serving
        finally:
            watchdog.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await watchdog
            self.bridge.close()

    def stop(self) -> None:
        """Graceful stop; a second call forces the exit without waiting for open connections."""
        AppStatus.should_exit = True  # sse_starlette cannot see uvicorn's flag without its signal handlers
        if self._server is not None:
            if self._server.should_exit:
                self._server.force_exit = True
            self._server.should_exit = True
