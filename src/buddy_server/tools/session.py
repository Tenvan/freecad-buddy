"""Session & Dokument (Session): Session status, document lifecycle and undo."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.tools.base import Doc, Registration

GROUP = Group("session", "Session", "Session & Dokument")  # ui-de


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def get_status() -> dict[str, Any]:
        """Status of FreeCAD and the bridge: version, open documents, missing object types. Call first."""
        return await ctx.call("get_status", "system.status")

    @tool
    async def storepoint(
        name: Annotated[str, Field(description="Unique name of the milestone, e.g. 'Base body'")],
        snapshot: Annotated[
            bool,
            Field(description="Also save a copy of the document next to its file (needs a saved document)"),
        ] = False,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Mark a milestone in the design stream: a marker in the group 'Storepoints' linked to the current
        feature plus the description 'Storepoint n: name' on that feature. replay rebuilds the design up to
        a storepoint in a new document."""
        return await ctx.call(
            "storepoint", "stream.storepoint", name=name, snapshot=snapshot, document=document
        )  # fmt: skip

    @tool
    async def list_storepoints(document: Doc = None) -> dict[str, Any]:
        """Storepoints of the document with position, timestamp, steps since the previous one and the
        linked feature; also the number of recorded steps and detected manual edits."""
        return await ctx.call("list_storepoints", "stream.list", document=document)

    @tool
    async def replay(
        storepoint: Annotated[str, Field(description="Storepoint to rebuild up to (inclusive)")],
        into: Annotated[str, Field(description="Name of the new document (must not exist yet)")],
        document: Doc = None,
    ) -> dict[str, Any]:
        """Rebuild the design from its recorded stream up to a storepoint in a new document, over the same
        tools and without changes: recover a broken model, rebuild after a FreeCAD update or branch a
        variant. Python execution and addon installation are skipped and reported; manual GUI edits in the
        original are not part of the stream (warning)."""
        return await ctx.call(
            "replay", "stream.replay", timeout=600, storepoint=storepoint, into=into, document=document
        )  # fmt: skip

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
        steps: Annotated[int, Field(ge=1, le=20, description="Number of steps")] = 1, document: Doc = None
    ) -> dict[str, Any]:
        """Undo the last change(s). Every tool call is exactly one step."""
        return await ctx.call("undo", "document.undo", steps=steps, document=document)
