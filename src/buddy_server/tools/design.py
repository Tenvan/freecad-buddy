"""Design-Tools (Design tools): recurring multi-step tasks as one call, and proposals for missing ones."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from buddy_server.catalog import Group
from buddy_server.events import DesignToolProposed
from buddy_server.tools.base import Registration

GROUP = Group("design", "Design tools", "Design-Tools")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def fill_pattern(
        size: Annotated[
            float, Field(gt=0, description="Cell size in mm: hole diameter (round) or across flats (hex)")
        ],
        pitch: Annotated[
            float, Field(gt=0, description="Centre distance of neighbouring cells in mm; web = pitch - size")
        ],
        cell: Annotated[
            Literal["round", "hex"], Field(description="round = holes (sieve, vent), hex = honeycomb cells")
        ] = "round",
        count: Annotated[
            list[int] | None, Field(description="[cells per row, rows]; alternatively field")
        ] = None,
        field: Annotated[
            list[float | str] | None,
            Field(
                description="[width, height] of the field: mm, parameters or expressions "
                "(e.g. 'Plate_Width - 2*Rim_Width'); the counts follow changes"
            ),
        ] = None,
        margin: Annotated[float, Field(ge=0, description="field: free border inside the field in mm")] = 0,
        center: Annotated[
            list[float | str] | None, Field(description="[x, y] of the field centre (numbers or parameters)")
        ] = None,
        plane: Literal["XY", "XZ", "YZ"] = "XY",
        offset: Annotated[
            float | str, Field(description="Sketch plane offset, e.g. the plate thickness for the top face")
        ] = 0,
        depth: Annotated[
            float | None, Field(gt=0, description="Cut depth in mm; empty = through all")
        ] = None,
        layout: Annotated[
            Literal["rect", "hex"] | None,
            Field(
                description="hex offsets every second row by half a pitch; empty = hex for hex cells, else rect"
            ),
        ] = None,
        name: Annotated[
            str, Field(description="Prefix of parameters and labels, e.g. Sieve → Sieve_Pitch, Grid_Sieve")
        ] = "Fill",
        body: Annotated[
            str | None, Field(description="Body label; empty when there is only one body")
        ] = None,
        document: Annotated[str | None, Field(description="Document name or label; empty = active")] = None,
    ) -> dict[str, Any]:
        """Fill a rectangular field with cut cells in one call and one undo step: round holes (sieve, perforation,
        vent, speaker grille) or hex cells (honeycomb). Native and parametric: parameters <name>_Size/_Pitch/_Count_X/
        _Count_Y, a fully constrained start-cell sketch, a pocket and one grid pattern; no addon needed."""
        return await ctx.call(
            "fill_pattern", "design.fill_pattern", timeout=120.0, size=size, pitch=pitch, cell=cell, count=count,
            field=field, margin=margin, center=center, plane=plane, offset=offset, depth=depth, layout=layout,
            name=name, body=body, document=document,
        )  # fmt: skip  # fmt: skip

    @tool
    async def propose_design_tool(
        name: Annotated[str, Field(description="snake_case name of the missing tool, e.g. screw_boss")],
        problem: Annotated[str, Field(description="Which recurring task it solves")],
        inputs: Annotated[list[str], Field(description="Inputs, e.g. ['outer_diameter', 'screw_size']")],
        steps: Annotated[list[str], Field(description="Tool calls it replaces, in order")],
        example: Annotated[str, Field(description="Concrete call as it would look, e.g. from this project")],
    ) -> dict[str, Any]:
        """Propose a missing design tool (task recurs or needs >= 5 tool calls, no design tool or addon fits).
        Proposals with the same name are merged and counted; a developer builds them as Buddy tools.
        Still solve the current task with single steps."""
        if ctx.proposals is None:
            raise ToolError("[unsupported] No proposal store configured in this server")
        try:
            entry = ctx.proposals.propose(name, problem, inputs, steps, example)
        except ValueError as error:
            raise ToolError(f"[validation] {error}") from None
        ctx.bus.publish(DesignToolProposed(entry["name"], entry["count"], problem))
        return {"proposal": entry, "merged": entry["count"] > 1}

    @tool
    async def list_design_tool_proposals() -> dict[str, Any]:
        """All design tool proposals, most requested first (name, count, problems, inputs, steps, examples)."""
        if ctx.proposals is None:
            raise ToolError("[unsupported] No proposal store configured in this server")
        proposals = sorted(ctx.proposals.all(), key=lambda p: (-p["count"], p["name"]))
        return {"count": len(proposals), "proposals": proposals}
