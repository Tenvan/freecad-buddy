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
        """Regeln für menschlich wirkende, parametrische PartDesign-Modelle und den FDM-Druck."""
        return await rulebook()

    @mcp.prompt()
    async def design_part(description: str) -> str:
        """Workflow-Prompt: Bauteil aus einer Beschreibung Schritt für Schritt konstruieren."""
        return (
            f"Konstruiere mit FreeCAD Buddy: {description}\n\n"
            "Vorgehen:\n"
            "1. get_status und get_model_tree lesen.\n"
            "2. Maße klären und als Parameter anlegen (set_parameters).\n"
            "3. Prüfen, ob ein Design-Tool die Aufgabe abdeckt (Regeln unter design_tools).\n"
            "4. create_body, dann Basisskizze (create_sketch + add_profile) und pad.\n"
            "5. Weitere Features (pocket, hole, pattern, revolve), danach fillet/chamfer/shell.\n"
            "6. Nach jedem Schritt warnings und DoF prüfen; bei Fehlern Hinweise befolgen oder undo.\n"
            "7. check_printability ausführen, Befunde beheben, export_body (3mf).\n"
            "8. Zusammenfassung: Parameter, Features, Druckhinweise.\n\n" + await rulebook()
        )

    @mcp.resource(RULES_URI, name="design-rules", title="Designregeln (Übersicht)", mime_type="text/markdown")
    async def rules_overview() -> str:
        return design_rules.render_overview(available)

    @mcp.resource(
        RULES_URI + "/{topic}",
        name="design-rules-topic",
        title="Designregeln (Thema)",
        mime_type="text/markdown",
    )
    async def rules_topic(topic: str) -> str:
        try:
            return design_rules.render_topic(topic, await ctx.printer_profile(), available)
        except KeyError:
            keys = ", ".join(t.key for t in design_rules.visible_topics(available))
            raise ValueError(f"Unbekanntes Thema '{topic}'. Gültig: {keys}") from None
