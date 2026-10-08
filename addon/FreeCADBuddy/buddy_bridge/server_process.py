"""Optional MCP server child process: started with FreeCAD, stopped with it. Stdlib only."""

from __future__ import annotations

import atexit
import os
import re
import shutil
import subprocess
import sys
import threading
from collections.abc import Callable, Mapping
from pathlib import Path

SERVER_EXECUTABLE = "freecad-buddy"
SERVER_LOG_FILE = "server.jsonl"
ENV_COMMAND = "FREECAD_BUDDY_SERVER_CMD"
# FreeCAD's interpreter settings must not leak into the venv python behind the console script.
_PYTHON_ENV = ("PYTHONHOME", "PYTHONPATH", "VIRTUAL_ENV")
_PORT_IN_USE = 2  # exit code of ``freecad-buddy`` when its MCP port is taken

Log = Callable[[str, str], None]
_TOOL_LINE = re.compile(r"^\d\d:\d\d:\d\d [→←] ")  # tool calls stay in the JSONL log, not the console
_REPO_ROOT = (
    Path(__file__).resolve().parents[3]
)  # addon/FreeCADBuddy/buddy_bridge -> checkout (junction-safe)


def resolve_command(configured: str, environ: Mapping[str, str] | None = None) -> str | None:
    """Server executable: preference, then environment, then ``PATH``; ``None`` if not found."""
    env = os.environ if environ is None else environ
    candidate = configured.strip() or env.get(ENV_COMMAND, "").strip()
    if candidate:
        return candidate if Path(candidate).is_file() else shutil.which(candidate)
    return shutil.which(SERVER_EXECUTABLE) or _checkout_command()


def _checkout_command() -> str | None:
    """``freecad-buddy`` from the project venv, when the addon is linked from a checkout."""
    for folder in ("Scripts", "bin"):
        for suffix in (".exe", ""):
            path = _REPO_ROOT / ".venv" / folder / f"{SERVER_EXECUTABLE}{suffix}"
            if path.is_file():
                return str(path)
    return None


def child_env(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ if environ is None else environ)
    for name in _PYTHON_ENV:
        env.pop(name, None)
    return env


class ServerProcess:
    """Runs ``freecad-buddy --headless`` as a child. Lifecycle lines go to ``log`` (FreeCAD console); tool calls
    only to the size-rotated JSONL ``log_path``, so the console cannot overflow."""

    def __init__(self, command: str, bridge_port: int, log_path: Path, log: Log) -> None:
        self._argv = [command, "--headless", "--bridge-port", str(bridge_port), "--log-file", str(log_path)]
        self._log_path = log_path
        self._log = log
        self._process: subprocess.Popen[bytes] | None = None

    @property
    def running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self) -> None:
        if self.running:
            return
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        self._process = subprocess.Popen(
            self._argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=child_env(),
            creationflags=flags,
        )
        threading.Thread(
            target=self._pump, args=(self._process,), name="buddy-server-output", daemon=True
        ).start()
        atexit.register(self.stop)  # ponytail: a hard kill of FreeCAD leaves an orphan; it keeps serving

    def _pump(self, process: subprocess.Popen[bytes]) -> None:
        """Forward the child's non-tool output; keeps the pipe drained so the child never blocks."""
        assert process.stdout is not None
        for raw in process.stdout:
            line = raw.decode("utf-8", errors="replace").strip()
            if line and not _TOOL_LINE.match(line):
                self._log("error" if "FEHLER" in line else "info", f"[Server] {line}")

    def stop(self) -> None:
        process, self._process = self._process, None
        if process is None or process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    def check(self) -> None:
        """Report an unexpected exit once; call from a periodic main-thread check."""
        process = self._process
        if process is None or (code := process.poll()) is None:
            return
        self._process = None
        if code == _PORT_IN_USE:
            self._log("info", "MCP-Server-Port belegt – ein anderer freecad-buddy läuft bereits.")  # ui-de
        else:
            self._log("error", f"MCP-Server beendet (Code {code}), siehe {self._log_path}")  # ui-de
