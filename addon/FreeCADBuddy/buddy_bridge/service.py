"""Bridge lifecycle inside FreeCAD: settings, token, start/stop, console logging."""

from __future__ import annotations

import os
from pathlib import Path

import FreeCAD

from buddy_bridge.dispatch import Dispatcher, InlineDispatcher
from buddy_bridge.methods import build_registry
from buddy_bridge.server import BridgeServer
from buddy_bridge.tokens import BRIDGE_TOKEN_FILE, buddy_home, load_or_create_token

PARAM_PATH = "User parameter:BaseApp/Preferences/Mod/FreeCADBuddy"
DEFAULT_PORT = 9876
PREFIX = "[FreeCAD Buddy] "


def _params():  # FreeCAD's ParameterGrp has no importable Python type
    return FreeCAD.ParamGet(PARAM_PATH)


def configured_port() -> int:
    return _params().GetInt("Port", DEFAULT_PORT)


def autostart_enabled() -> bool:
    return _params().GetBool("Autostart", True)


def set_autostart(enabled: bool) -> None:
    _params().SetBool("Autostart", enabled)


def python_allowed() -> bool:
    """``python.execute`` needs an opt-in on the FreeCAD side too (setting or environment)."""
    env = os.environ.get("FREECAD_BUDDY_ALLOW_PYTHON", "").strip().lower() in ("1", "true", "yes", "on")
    return env or _params().GetBool("AllowPython", False)


def set_python_allowed(enabled: bool) -> None:
    _params().SetBool("AllowPython", enabled)


def addon_install_allowed() -> bool:
    """Installing addons needs an opt-in on the FreeCAD side too (setting or environment)."""
    env = os.environ.get("FREECAD_BUDDY_ALLOW_ADDON_INSTALL", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    return env or _params().GetBool("AllowAddonInstall", False)


def set_addon_install_allowed(enabled: bool) -> None:
    _params().SetBool("AllowAddonInstall", enabled)


def console(level: str, message: str) -> None:
    printer = {
        "warning": FreeCAD.Console.PrintWarning,
        "error": FreeCAD.Console.PrintError,
    }.get(level, FreeCAD.Console.PrintMessage)
    printer(f"{PREFIX}{message}\n")


def gui_busy() -> str | None:
    """Reason why FreeCAD must not be modified right now (modal dialog or open task panel)."""
    import FreeCADGui
    from PySide import QtWidgets

    app = QtWidgets.QApplication.instance()
    if isinstance(app, QtWidgets.QApplication) and app.activeModalWidget() is not None:
        return "In FreeCAD ist ein Dialog offen. Dialog schließen und erneut versuchen."
    if FreeCADGui.Control.activeDialog():
        return "In FreeCAD ist ein Aufgabenbereich offen (z. B. Skizze oder Feature in Bearbeitung). Erst abschließen."
    return None


class BridgeService:
    def __init__(
        self,
        dispatcher: Dispatcher,
        token_path: Path | None = None,
        port: int | None = None,
        allow_python: bool | None = None,
        allow_addon_install: bool | None = None,
    ) -> None:
        self._dispatcher = dispatcher
        self._token_path = token_path or buddy_home() / BRIDGE_TOKEN_FILE
        self._port = port
        self._allow_python = allow_python
        self._allow_addon_install = allow_addon_install
        self._server: BridgeServer | None = None

    @property
    def running(self) -> bool:
        return self._server is not None and self._server.running

    @property
    def port(self) -> int:
        return self._server.port if self._server else (self._port or configured_port())

    @property
    def token_path(self) -> Path:
        return self._token_path

    @property
    def allow_python(self) -> bool:
        return python_allowed() if self._allow_python is None else self._allow_python

    @property
    def allow_addon_install(self) -> bool:
        return addon_install_allowed() if self._allow_addon_install is None else self._allow_addon_install

    def start(self) -> None:
        if self.running:
            return
        token = load_or_create_token(self._token_path)
        server = BridgeServer(
            build_registry(allow_python=self.allow_python, allow_addon_install=self.allow_addon_install),
            self._dispatcher,
            token,
            port=self._port if self._port is not None else configured_port(),
            log=self._log,
        )
        server.start()
        self._server = server

    def stop(self) -> None:
        if self._server is not None:
            self._server.stop()
            self._server = None

    def describe(self) -> str:
        state = f"läuft auf 127.0.0.1:{self.port}" if self.running else "gestoppt"
        clients = f", {self._server.client_count()} Verbindung(en)" if self._server else ""
        return (
            f"Bridge {state}{clients}; Token: {self._token_path}; Autostart: {autostart_enabled()}; "
            f"Python-Ausführung: {'erlaubt' if self.allow_python else 'gesperrt'}; "
            f"Addon-Installation: {'erlaubt' if self.allow_addon_install else 'gesperrt'}"
        )

    def _log(self, level: str, message: str) -> None:
        # Called from server threads; FreeCAD's report view must only be touched on the main thread.
        self._dispatcher.post(lambda: console(level, message))


_service: BridgeService | None = None


def get_service() -> BridgeService:
    """Process-wide service. The first call must happen on FreeCAD's main thread."""
    global _service
    if _service is None:
        if FreeCAD.GuiUp:
            from buddy_bridge.qt_dispatcher import QtMainThreadDispatcher

            _service = BridgeService(QtMainThreadDispatcher(busy_check=gui_busy))
        else:
            _service = BridgeService(InlineDispatcher())
    return _service
