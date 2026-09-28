"""Shared-secret handling. Tokens live version-independently in ``%APPDATA%\\FreeCADBuddy``."""

from __future__ import annotations

import hmac
import os
import secrets
from pathlib import Path

BRIDGE_TOKEN_FILE = "bridge-token"
MCP_TOKEN_FILE = "mcp-token"


def buddy_home(environ: dict[str, str] | None = None) -> Path:
    """Directory for FreeCAD Buddy runtime files; ``FREECAD_BUDDY_HOME`` overrides the default."""
    env = os.environ if environ is None else environ
    override = env.get("FREECAD_BUDDY_HOME")
    if override:
        return Path(override)
    appdata = env.get("APPDATA")
    return Path(appdata) / "FreeCADBuddy" if appdata else Path.home() / ".freecad-buddy"


def load_or_create_token(path: Path) -> str:
    """Return the token stored at ``path``, creating a new random one if missing or empty."""
    if path.is_file():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token
    path.parent.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    # Create with owner-only permissions (effective on POSIX; on Windows %APPDATA% is per user).
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(token)
    return token


def read_token(path: Path) -> str | None:
    """Return the stored token or ``None`` if it does not exist (clients never create tokens)."""
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip() or None


def tokens_match(expected: str, candidate: object) -> bool:
    return isinstance(candidate, str) and hmac.compare_digest(expected.encode(), candidate.encode())
