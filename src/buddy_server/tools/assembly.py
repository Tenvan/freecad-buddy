"""Baugruppe (Assembly): Assemblies (Assembly4 convention), fasteners, STEP parts, configurations."""

from __future__ import annotations

from typing import Annotated, Any

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from buddy_server.addon_service import CatalogError
from buddy_server.catalog import Group
from buddy_server.tools.base import Doc, Purpose, Registration

GROUP = Group("assembly", "Assembly", "Baugruppe")


def register(reg: Registration) -> None:
    tool, ctx = reg.tool, reg.ctx

    @tool
    async def create_assembly(
        label: Annotated[str, Field(description="Assembly label")] = "Assembly",
        document: Doc = None,
    ) -> dict[str, Any]:
        """Create an Assembly4 assembly in the document (bodies move into a 'Parts' group). Then
        add_to_assembly for each body, add_fastener for standard parts, explode_assembly for an exploded view."""
        return await ctx.call("create_assembly", "assembly.create", label=label, document=document)

    @tool
    async def add_to_assembly(
        part: Annotated[str, Field(description="Body or App::Part label")],
        label: Annotated[str | None, Field(description="Link label; empty = part label")] = None,
        offset: Annotated[
            list[float] | None, Field(description="[x, y, z] from the modelled position; empty = in place")
        ] = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Insert a body into the assembly as App::Link placed by Assembly4 (LCS_Origin * AttachmentOffset)."""
        return await ctx.call(
            "add_to_assembly", "assembly.add", part=part, label=label, offset=offset, document=document
        )

    @tool
    async def add_fastener(
        type: Annotated[
            str,
            Field(description="Fasteners type, e.g. ISO4032 (hex nut), ISO7089 (washer), ISO4762 (screw)"),
        ],
        diameter: Annotated[str, Field(description="Size, e.g. 'M10'")],
        positions: Annotated[
            list[list[float]], Field(description="One [x, y, z] per fastener (bottom face)")
        ],
        thread: Annotated[bool, Field(description="Model the real thread (slower)")] = False,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Standard parts from the Fasteners workbench (needs the addon), placed in the assembly if there
        is one. Stack e.g. a washer on the plate and the nut on top of the washer."""
        return await ctx.call(
            "add_fastener", "assembly.fastener", type=type, diameter=diameter, positions=positions,
            thread=thread, purpose=purpose, document=document,
        )  # fmt: skip

    @tool
    async def search_parts(
        query: Annotated[
            str, Field(description="Search terms, all must match, e.g. 'raspberry pi 5' or '608 bearing'")
        ],
        category: Annotated[
            str | None,
            Field(description="e.g. fastener, electronics, bearing, motion, thermal, power-transmission"),
        ] = None,
        limit: Annotated[int, Field(ge=1, le=50)] = 10,
    ) -> dict[str, Any]:
        """Search the step.parts catalogue of open STEP models (boards, fans, motors, bearings, profiles,
        fasteners): reference geometry for fits and cut-outs. Insert a hit with insert_part."""
        try:
            return await ctx.parts_catalog().search(query, category, limit)
        except CatalogError as error:
            raise ToolError(f"[{error.code}] {error}\nHint: check network/proxy") from None

    @tool
    async def insert_part(
        part_id: Annotated[str, Field(description="id from search_parts, e.g. 'raspberry_pi_5'")],
        position: Annotated[list[float] | None, Field(description="[x, y, z]; empty = origin")] = None,
        purpose: Purpose = None,
        document: Doc = None,
    ) -> dict[str, Any]:
        """Download a step.parts STEP model (cached) and insert it as a plain solid, in the assembly if
        there is one. Reference only: model own parts around it, do not print it."""
        catalog = ctx.parts_catalog()
        try:
            part = await catalog.find(part_id)
            if part is None:
                raise ToolError(f"[not_found] No part '{part_id}' in step.parts\nHint: search_parts first")
            path = await catalog.step_file(part_id)
        except CatalogError as error:
            raise ToolError(f"[{error.code}] {error}") from None
        result = await ctx.call(
            "insert_part", "assembly.insert_step", timeout=120, path=str(path),
            label=purpose or part_id, position=position, document=document,
        )  # fmt: skip
        result["source"] = {"id": part_id, "name": part.get("name"), "catalogue": "step.parts (MIT)"}
        return result

    @tool
    async def explode_assembly(
        moves: Annotated[
            dict[str, list[float]], Field(description="Label -> [dx, dy, dz] from the assembled position")
        ],
        name: Annotated[str, Field(description="Configuration name")] = "Exploded",
        document: Doc = None,
    ) -> dict[str, Any]:
        """Exploded view as Assembly4 configuration: saves 'Assembled' once, moves the listed parts and
        saves the result. Switch back and forth with apply_configuration."""
        return await ctx.call(
            "explode_assembly", "assembly.explode", moves=moves, name=name, document=document
        )

    @tool
    async def apply_configuration(
        name: Annotated[str, Field(description="Configuration, e.g. 'Assembled' or 'Exploded'")],
        document: Doc = None,
    ) -> dict[str, Any]:
        """Apply a saved Assembly4 configuration (positions of all assembly parts)."""
        return await ctx.call("apply_configuration", "assembly.configuration", name=name, document=document)
