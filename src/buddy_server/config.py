"""Runtime settings of the FreeCAD Buddy server."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from buddy_bridge.tokens import BRIDGE_TOKEN_FILE, MCP_TOKEN_FILE, buddy_home, load_or_create_token

DEFAULT_PORT = 8765
DEFAULT_BRIDGE_PORT = 9876
LOCAL_HOST = "127.0.0.1"


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name, "").strip().lower()
    return default if not value else value in ("1", "true", "yes", "on")


@dataclass
class Settings:
    port: int = DEFAULT_PORT
    bridge_port: int = DEFAULT_BRIDGE_PORT
    home: Path = field(default_factory=buddy_home)
    allow_python: bool = field(default_factory=lambda: _env_flag("FREECAD_BUDDY_ALLOW_PYTHON"))
    # On by default: FreeCAD's own opt-in and the confirmation dialog of every install stay in place.
    allow_addon_install: bool = field(
        default_factory=lambda: _env_flag("FREECAD_BUDDY_ALLOW_ADDON_INSTALL", default=True)
    )
    host: str = LOCAL_HOST
    bridge_host: str = LOCAL_HOST
    connect_timeout: float = 3.0
    # Longer than the bridge's own 30 s default, so the bridge reports gui_timeout first.
    request_timeout: float = 45.0
    watchdog_interval: float = 3.0

    @property
    def bridge_token_path(self) -> Path:
        return self.home / BRIDGE_TOKEN_FILE

    @property
    def mcp_token_path(self) -> Path:
        return self.home / MCP_TOKEN_FILE

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/mcp"

    def mcp_token(self) -> str:
        return load_or_create_token(self.mcp_token_path)

    def claude_add_command(self) -> str:
        return (
            f"claude mcp add --transport http freecad-buddy {self.url} "
            f'--header "Authorization: Bearer {self.mcp_token()}"'
        )
