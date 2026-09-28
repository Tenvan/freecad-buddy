"""ASGI application: MCP over Streamable HTTP behind bearer auth, with session tracking."""

from __future__ import annotations

import hmac
import json
from typing import Any

from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings

from buddy_bridge.tokens import read_token
from buddy_server import __version__
from buddy_server.addon_service import AddonCatalogService
from buddy_server.bridge import Bridge
from buddy_server.calllog import ToolCallLog
from buddy_server.config import Settings
from buddy_server.design_rules import build_instructions
from buddy_server.events import Console, EventBus, SessionsChanged
from buddy_server.payloads import Masker
from buddy_server.prompts import register_prompts
from buddy_server.tools import NameCollector, ToolContext, register_tools

Scope = dict[str, Any]
Receive = Any
Send = Any
ASGIApp = Any


def _header(scope: Scope, name: bytes) -> str | None:
    for key, value in scope.get("headers", []):
        if key.lower() == name:
            return value.decode("latin-1")
    return None


class BearerAuth:
    """Rejects HTTP requests without ``Authorization: Bearer <mcp-token>``."""

    def __init__(self, app: ASGIApp, token: str, bus: EventBus) -> None:
        self._app = app
        self._expected = f"Bearer {token}".encode()
        self._bus = bus

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            provided = (_header(scope, b"authorization") or "").encode()
            if not hmac.compare_digest(provided, self._expected):
                self._bus.publish(
                    Console("warning", f"MCP-Anfrage ohne gültiges Token abgewiesen ({scope['path']})")
                )
                body = json.dumps(
                    {"error": "unauthorized", "message": "Bearer-Token fehlt oder ist falsch"}
                ).encode()
                await send(
                    {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [(b"content-type", b"application/json"), (b"www-authenticate", b"Bearer")],
                    }
                )
                await send({"type": "http.response.body", "body": body})
                return
        await self._app(scope, receive, send)


class SessionTracker:
    """Counts MCP sessions from the ``mcp-session-id`` header (created on response, ended by DELETE)."""

    def __init__(self, app: ASGIApp, bus: EventBus) -> None:
        self._app = app
        self._bus = bus
        self.sessions: set[str] = set()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        requested = _header(scope, b"mcp-session-id")
        if scope["method"] == "DELETE" and requested:
            self._update(lambda: self.sessions.discard(requested))

        async def tracking_send(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start" and scope["method"] != "DELETE":
                for key, value in message.get("headers", []):
                    if key.lower() == b"mcp-session-id":
                        self._add(value.decode("latin-1"))
            await send(message)

        await self._app(scope, receive, tracking_send)

    def _add(self, session: str) -> None:
        self._update(lambda: self.sessions.add(session))

    def _update(self, change: Any) -> None:
        before = len(self.sessions)
        change()
        if len(self.sessions) != before:
            self._bus.publish(SessionsChanged(len(self.sessions)))


def transport_security(settings: Settings) -> TransportSecuritySettings:
    hosts = [f"{name}:{settings.port}" for name in ("127.0.0.1", "localhost")]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=[f"http://{host}" for host in hosts],
    )


def build_mcp(settings: Settings, bridge: Bridge, bus: EventBus) -> tuple[MCPServer, list[str]]:
    ctx = ToolContext(bridge, bus, AddonCatalogService(settings.home / "addon-catalog"))
    # Instructions only mention registered tools, so collect the names before creating the server.
    available = set(register_tools(NameCollector(), ctx, settings.allow_python, settings.allow_addon_install))
    secrets = [settings.mcp_token(), read_token(settings.bridge_token_path) or ""]
    mcp = MCPServer(
        "FreeCAD Buddy",
        instructions=build_instructions(available),
        version=__version__,
        log_level="WARNING",
        middleware=[ToolCallLog(bus, Masker(secrets))],
    )
    names = register_tools(mcp, ctx, settings.allow_python, settings.allow_addon_install)
    register_prompts(mcp, ctx, set(names))
    return mcp, names


def build_app(settings: Settings, bridge: Bridge, bus: EventBus) -> tuple[ASGIApp, list[str]]:
    mcp, names = build_mcp(settings, bridge, bus)
    inner = mcp.streamable_http_app(transport_security=transport_security(settings), host=settings.host)
    return BearerAuth(SessionTracker(inner, bus), settings.mcp_token(), bus), names
