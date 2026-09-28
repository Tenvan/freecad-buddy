# FreeCAD executes this file at GUI start-up for every addon in Mod/.


def _setup_freecad_buddy() -> None:
    import FreeCADGui
    from PySide import QtCore

    from buddy_bridge import commands

    class FreeCADBuddyWorkbench(FreeCADGui.Workbench):
        MenuText = "FreeCAD Buddy"
        ToolTip = "Bridge für den FreeCAD-Buddy-Server (MCP)"

        def Initialize(self) -> None:
            self.appendToolbar("FreeCAD Buddy", list(commands.COMMANDS))
            self.appendMenu("FreeCAD Buddy", list(commands.COMMANDS))

        def GetClassName(self) -> str:
            return "Gui::PythonWorkbench"

    commands.register()
    FreeCADGui.addWorkbench(FreeCADBuddyWorkbench())
    # Start once the event loop runs, so the dispatcher is created on the main thread.
    QtCore.QTimer.singleShot(0, commands.autostart)


_setup_freecad_buddy()
