"""Session & Dokument (Session): Session status, document lifecycle and undo."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.tools.base import Doc, Registration

GROUP = Group("session", "Session", "Session & Dokument")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def get_status() -> dict[str, Any]:
        """Status von FreeCAD und Bridge: Version, offene Dokumente, fehlende Objekttypen. Zuerst aufrufen."""
        return await ctx.call("get_status", "system.status")

    @tool
    async def document(
        action: Annotated[
            Literal["new", "open", "save", "close", "revert"],
            Field(description="new | open | save | close | revert"),
        ],
        name: Annotated[str | None, Field(description="new: name of the new document")] = None,
        path: Annotated[
            str | None,
            Field(
                description="open: .FCStd file; save: target path (empty = current file, new documents need "
                "one); close: target for unsaved='save' on a never-saved document"
            ),
        ] = None,
        unsaved: Annotated[
            Literal["refuse", "save", "discard"],
            Field(
                description="close: unsaved changes - refuse (default, error), save first, or discard them"
            ),
        ] = "refuse",
        document: Doc = None,
    ) -> dict[str, Any]:
        """Document lifecycle. new: create and activate (then set_parameters → create_body → create_sketch →
        add_profile → pad/pocket → details → check_printability → export_body); open: open and activate a
        .FCStd; save: save as .FCStd; close: refuses with unsaved changes unless unsaved='save'/'discard' - ask
        the user before discarding; revert: discard all changes since the last save (ask the user first)."""
        if action == "new":
            if not name:
                raise ToolError("[validation] document(action='new') needs 'name'")
            return await ctx.call("document", "document.new", name=name)
        if action == "open":
            if not path:
                raise ToolError("[validation] document(action='open') needs 'path'")
            return await ctx.call("document", "document.open", path=path)
        if action == "save":
            return await ctx.call("document", "document.save", path=path, document=document)
        if action == "close":
            return await ctx.call("document", "document.close", unsaved=unsaved, path=path, document=document)
        return await ctx.call("document", "document.revert", document=document)

    @tool
    async def undo(
        steps: Annotated[int, Field(ge=1, le=20, description="Anzahl Schritte")] = 1, document: Doc = None
    ) -> dict[str, Any]:
        """Letzte Änderung(en) rückgängig machen. Jeder Tool-Aufruf ist genau ein Schritt."""
        return await ctx.call("undo", "document.undo", steps=steps, document=document)
