"""FreeCAD GUI commands of the FreeCAD Buddy workbench."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import FreeCADGui

from buddy_bridge import service


def _start() -> None:
    bridge = service.get_service()
    try:
        bridge.start()
    except OSError as error:
        service.console(
            "error",
            f"Bridge konnte nicht auf Port {bridge.port} starten: {error}. "
            "Port belegt? Einstellung 'Port' unter Mod/FreeCADBuddy anpassen.",
        )
        return
    bridge.start_server_process()
    from PySide import QtCore

    QtCore.QTimer.singleShot(3000, bridge.check_server_process)  # reports an early exit (e.g. port taken)


def _restart_bridge() -> None:
    """Rebuild the method registry – the bridge reads the opt-ins only when it starts."""
    bridge = service.get_service()
    if bridge.running:
        bridge.stop()
        _start()


class _StartBridge:
    def GetResources(self) -> dict[str, Any]:
        return {
            "MenuText": "Bridge starten",
            "ToolTip": "Startet die Verbindung für den FreeCAD-Buddy-Server",
        }

    def Activated(self) -> None:
        _start()

    def IsActive(self) -> bool:
        return not service.get_service().running


class _StopBridge:
    def GetResources(self) -> dict[str, Any]:
        return {"MenuText": "Bridge stoppen", "ToolTip": "Beendet die Bridge und trennt alle Verbindungen"}

    def Activated(self) -> None:
        service.get_service().stop()

    def IsActive(self) -> bool:
        return service.get_service().running


class _BridgeStatus:
    def GetResources(self) -> dict[str, Any]:
        return {"MenuText": "Bridge-Status", "ToolTip": "Zeigt den Bridge-Status in der Ausgabeansicht"}

    def Activated(self) -> None:
        service.console("info", service.get_service().describe())

    def IsActive(self) -> bool:
        return True


@dataclass(frozen=True)
class _Setting:
    """An on/off setting shown as two buttons, like starting and stopping the bridge."""

    name: str
    enabled: Callable[[], bool]
    store: Callable[[bool], None]
    on_text: str
    off_text: str
    restart_bridge: bool = False


@dataclass(frozen=True)
class _SetSetting:
    setting: _Setting
    value: bool
    menu_text: str
    tool_tip: str

    def GetResources(self) -> dict[str, Any]:
        return {"MenuText": self.menu_text, "ToolTip": self.tool_tip}

    def Activated(self) -> None:
        setting = self.setting
        setting.store(self.value)
        if setting.restart_bridge:
            _restart_bridge()
        state = setting.enabled()
        service.console("info", f"{setting.name} {setting.on_text if state else setting.off_text}")
        if state != self.value:
            service.console("warning", f"{setting.name} bleibt an: per Umgebungsvariable erzwungen")

    def IsActive(self) -> bool:
        return self.setting.enabled() != self.value


_AUTOSTART = _Setting(
    "Autostart", service.autostart_enabled, service.set_autostart, "aktiviert", "deaktiviert"
)
_SERVER_AUTOSTART = _Setting(
    "MCP-Server-Autostart",
    service.server_autostart_enabled,
    service.set_server_autostart,
    "aktiviert",
    "deaktiviert",
)
_PYTHON = _Setting(
    "Python-Ausführung",
    service.python_allowed,
    service.set_python_allowed,
    "erlaubt",
    "gesperrt",
    restart_bridge=True,
)
_ADDON_INSTALL = _Setting(
    "Addon-Installation",
    service.addon_install_allowed,
    service.set_addon_install_allowed,
    "erlaubt",
    "gesperrt",
    restart_bridge=True,
)


COMMANDS: dict[str, Any] = {
    "Buddy_StartBridge": _StartBridge(),
    "Buddy_StopBridge": _StopBridge(),
    "Buddy_BridgeStatus": _BridgeStatus(),
    "Buddy_EnableAutostart": _SetSetting(
        _AUTOSTART, True, "Autostart an", "Bridge beim Start von FreeCAD automatisch starten"
    ),
    "Buddy_DisableAutostart": _SetSetting(
        _AUTOSTART, False, "Autostart aus", "Bridge beim Start von FreeCAD nicht mehr automatisch starten"
    ),
    "Buddy_EnableServerAutostart": _SetSetting(
        _SERVER_AUTOSTART,
        True,
        "MCP-Server-Autostart an",
        "freecad-buddy beim Start der Bridge als Hintergrundprozess mitstarten",
    ),
    "Buddy_DisableServerAutostart": _SetSetting(
        _SERVER_AUTOSTART,
        False,
        "MCP-Server-Autostart aus",
        "freecad-buddy nicht mehr mitstarten (manuell im Terminal starten)",
    ),
    "Buddy_AllowPython": _SetSetting(
        _PYTHON, True, "Python erlauben", "execute_python auf FreeCAD-Seite erlauben (startet die Bridge neu)"
    ),
    "Buddy_BlockPython": _SetSetting(
        _PYTHON, False, "Python sperren", "execute_python auf FreeCAD-Seite sperren (startet die Bridge neu)"
    ),
    "Buddy_AllowAddonInstall": _SetSetting(
        _ADDON_INSTALL,
        True,
        "Addon-Installation erlauben",
        "install_addon auf FreeCAD-Seite erlauben; jede Installation fragt trotzdem nach (startet die Bridge neu)",
    ),
    "Buddy_BlockAddonInstall": _SetSetting(
        _ADDON_INSTALL,
        False,
        "Addon-Installation sperren",
        "install_addon auf FreeCAD-Seite sperren (startet die Bridge neu)",
    ),
}


def register() -> None:
    for name, command in COMMANDS.items():
        FreeCADGui.addCommand(name, command)


def autostart() -> None:
    if service.autostart_enabled():
        _start()
