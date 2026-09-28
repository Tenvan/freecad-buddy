"""Shared parts of the MCP tool modules: argument types, the bridge context and registration.

Tool descriptions are written for the agent: they state the intended modelling workflow,
so the model stays PartDesign-first and editable by a human.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Any, Protocol

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from buddy_bridge.protocol import RpcError
from buddy_server.addon_service import AddonCatalogService, CatalogError
from buddy_server.bridge import Bridge, BridgeTimeout, BridgeUnavailable
from buddy_server.events import EventBus

Doc = Annotated[str | None, Field(description="Dokumentname oder -label; leer = aktives Dokument")]
Num = Annotated[
    float | str,
    Field(description="Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden)"),
]
Purpose = Annotated[str | None, Field(description="Zweck für das Label, z. B. 'Base' → 'Pad_Base'")]

SELECTOR_HELP = (
    "Semantischer Selektor, z. B. edges:top, edges:vertical, edges:bottom, faces:top, face:top, "
    "edges:circular,radius=2, edges:of_feature=Pocket_Cut. select_geometry zeigt die Treffer vorab."
)


class ToolRegistrar(Protocol):
    def tool(self) -> Callable[[Any], Any]: ...


class NameCollector:
    """Stand-in registrar: collects tool names without an MCP server (for building instructions)."""

    def tool(self) -> Callable[[Any], Any]:
        return lambda fn: fn


def _error_text(error: RpcError) -> str:
    lines = [f"[{error.name}] {error.message}"]
    hints = error.data.get("hints") or []
    lines.extend(f"Hinweis: {hint}" for hint in hints)
    extra = {k: v for k, v in error.data.items() if k not in ("hints", "state")}
    if extra:
        lines.append("Details: " + json.dumps(extra, ensure_ascii=False, default=str)[:4000])
    return "\n".join(lines)


class ToolContext:
    """Forwards tool calls to the bridge and turns bridge failures into MCP tool errors.

    Request/response logging happens in ``calllog.ToolCallLog`` (MCP middleware), not here.
    """

    def __init__(self, bridge: Bridge, bus: EventBus, addons: AddonCatalogService | None = None) -> None:
        self.bridge = bridge
        self.bus = bus
        self.addons = addons

    async def installed(self) -> dict[str, Any] | None:
        """Installed addons/macros and FreeCAD version from the bridge, ``None`` if it cannot answer."""
        try:
            result = await self.bridge.call("addons.status", {}, None)
        except (BridgeUnavailable, BridgeTimeout, RpcError):
            return None
        return result if isinstance(result, dict) else None

    async def catalog(self, refresh: bool = False) -> tuple[AddonCatalogService, dict[str, Any]]:
        if self.addons is None:
            raise ToolError("[unsupported] Addon-Katalog ist in diesem Server nicht konfiguriert")
        try:
            state = await self.addons.ensure(refresh)
        except CatalogError as error:
            hint = "Netz/Proxy prüfen" if error.code == "catalog_unavailable" else "später erneut versuchen"
            raise ToolError(f"[{error.code}] {error}\nHinweis: {hint}") from None
        return self.addons, state.as_dict()

    async def call(self, tool: str, method: str, timeout: float | None = None, **params: Any) -> Any:
        clean = {key: value for key, value in params.items() if value is not None}
        try:
            return await self.bridge.call(method, clean, timeout)
        except BridgeUnavailable as error:
            raise ToolError(f"[bridge_unavailable] {error}") from None
        except BridgeTimeout as error:
            raise ToolError(f"[timeout] {error}") from None
        except RpcError as error:
            raise ToolError(_error_text(error)) from None

    async def printer_profile(self) -> dict[str, Any] | None:
        """Active printer profile from FreeCAD, or ``None`` if the bridge cannot answer."""
        try:
            result = await self.bridge.call("print.get_profile", {}, None)
        except (BridgeUnavailable, BridgeTimeout, RpcError):
            return None
        return result if isinstance(result, dict) else None


@dataclass(frozen=True)
class Registration:
    """What a tool module needs to register its tools."""

    tool: Callable[[Any], Any]
    ctx: ToolContext
    names: list[str]
    """All registered tool names (filled while registering, complete at call time)."""
    allow_python: bool
    allow_addon_install: bool
