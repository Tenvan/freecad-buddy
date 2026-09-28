"""FreeCAD GUI commands of the FreeCAD Buddy workbench."""

from __future__ import annotations

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


class _ToggleAutostart:
    def GetResources(self) -> dict[str, Any]:
        return {
            "MenuText": "Autostart umschalten",
            "ToolTip": "Bridge beim Start von FreeCAD automatisch starten",
        }

    def Activated(self) -> None:
        enabled = not service.autostart_enabled()
        service.set_autostart(enabled)
        service.console("info", f"Autostart {'aktiviert' if enabled else 'deaktiviert'}")

    def IsActive(self) -> bool:
        return True


class _TogglePython:
    def GetResources(self) -> dict[str, Any]:
        return {
            "MenuText": "Python-Ausführung umschalten",
            "ToolTip": "execute_python auf FreeCAD-Seite erlauben/sperren (wirkt nach Neustart der Bridge)",
        }

    def Activated(self) -> None:
        enabled = not service.python_allowed()
        service.set_python_allowed(enabled)
        bridge = service.get_service()
        if bridge.running:
            bridge.stop()
            _start()
        service.console("info", f"Python-Ausführung {'erlaubt' if enabled else 'gesperrt'}")

    def IsActive(self) -> bool:
        return True


class _ToggleAddonInstall:
    def GetResources(self) -> dict[str, Any]:
        return {
            "MenuText": "Addon-Installation umschalten",
            "ToolTip": "install_addon auf FreeCAD-Seite erlauben/sperren; jede Installation fragt trotzdem nach",
        }

    def Activated(self) -> None:
        enabled = not service.addon_install_allowed()
        service.set_addon_install_allowed(enabled)
        bridge = service.get_service()
        if bridge.running:
            bridge.stop()
            _start()
        service.console("info", f"Addon-Installation {'erlaubt' if enabled else 'gesperrt'}")

    def IsActive(self) -> bool:
        return True


COMMANDS: dict[str, Any] = {
    "Buddy_StartBridge": _StartBridge(),
    "Buddy_StopBridge": _StopBridge(),
    "Buddy_BridgeStatus": _BridgeStatus(),
    "Buddy_ToggleAutostart": _ToggleAutostart(),
    "Buddy_TogglePython": _TogglePython(),
    "Buddy_ToggleAddonInstall": _ToggleAddonInstall(),
}


def register() -> None:
    for name, command in COMMANDS.items():
        FreeCADGui.addCommand(name, command)


def autostart() -> None:
    if service.autostart_enabled():
        _start()
