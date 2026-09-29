"""MCP prompts and resources that steer the agent towards human-style models.

All texts come from ``buddy_server.design_rules`` – there is no second copy of any rule here.
"""

from __future__ import annotations

from mcp.server import MCPServer

from buddy_server import design_rules
from buddy_server.tools import ToolContext

RULES_URI = "buddy://design-rules"


def register_prompts(mcp: MCPServer, ctx: ToolContext, available: set[str]) -> None:
    async def rulebook() -> str:
        return design_rules.render_all(await ctx.printer_profile(), available)

    @mcp.prompt()
    async def human_modeling_guide() -> str:
        """Rules for human-style, parametric PartDesign models and FDM printing."""
        return await rulebook()

    @mcp.prompt()
    async def design_part(description: str) -> str:
        """Workflow prompt: design a part from a description step by step."""
        return (
            f"Design with FreeCAD Buddy: {description}\n\n"
            "Procedure:\n"
            "1. Read get_status and get_model_tree (the server sets the view after the first pad itself).\n"
            "2. Clarify dimensions and create them as parameters (set_parameters).\n"
            "3. Check whether a design tool covers the task (rules under design_tools).\n"
            "4. create_body, then the base sketch (create_sketch + add_profile) and pad.\n"
            "5. Further features (pocket, hole, pattern, revolve), then fillet/chamfer/shell.\n"
            "6. After every step check warnings and DoF; on errors follow the hints or undo.\n"
            "7. Run check_printability, fix the findings, export_body (3mf).\n"
            "8. set_view (iso), so the finished part is completely visible.\n"
            "9. Summary: parameters, features, printing notes.\n\n" + await rulebook()
        )

    @mcp.resource(RULES_URI, name="design-rules", title="Design rules (overview)", mime_type="text/markdown")
    async def rules_overview() -> str:
        return design_rules.render_overview(available)

    @mcp.resource(
        RULES_URI + "/{topic}",
        name="design-rules-topic",
        title="Design rules (topic)",
        mime_type="text/markdown",
    )
    async def rules_topic(topic: str) -> str:
        try:
            return design_rules.render_topic(topic, await ctx.printer_profile(), available)
        except KeyError:
            keys = ", ".join(t.key for t in design_rules.visible_topics(available))
            raise ValueError(f"Unknown topic '{topic}'. Valid: {keys}") from None
