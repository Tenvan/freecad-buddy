"""Regelwerk & Addons (Rules & addons): Design rulebook and the FreeCAD addon catalogue."""

from __future__ import annotations

import asyncio
import time
from typing import Annotated, Any, Literal

from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

from buddy_server import design_rules
from buddy_server.addon_catalog import AddonEntry, search
from buddy_server.addon_service import UNTRUSTED_NOTE
from buddy_server.catalog import Group
from buddy_server.tools.base import Registration

GROUP = Group("rules", "Rules & addons", "Regelwerk & Addons")


def _installed_flag(entry: AddonEntry, status: dict[str, Any] | None) -> bool | None:
    if status is None:
        return None
    if entry.kind == "macro":
        return entry.filename in status["macros"] or f"Macro_{entry.filename}" in status["macros"]
    return entry.id in status["addons"]


def _version(status: dict[str, Any] | None) -> tuple[int, int, int] | None:
    if status is None:
        return None
    major, minor, patch = (int(part) for part in status["freecad_version"][:3])
    return major, minor, patch


def _install_blocker(entry: AddonEntry, status: dict[str, Any]) -> str | None:
    """Why Buddy refuses to install ``entry`` (the Addon Manager can still do it), or ``None``."""
    version = _version(status)
    if _installed_flag(entry, status):
        return f"'{entry.id}' is already installed (updates stay with the Addon Manager)"
    if version is not None and not entry.compatible_with(version):
        return f"'{entry.id}' is not compatible with FreeCAD {'.'.join(map(str, version))}"
    if entry.python_dependencies:
        packages = ", ".join(entry.python_dependencies[:5])
        return f"'{entry.id}' needs Python packages ({packages}); Buddy does not run pip"
    if entry.addon_dependencies:
        return f"'{entry.id}' depends on other addons ({', '.join(entry.addon_dependencies[:5])})"
    if entry.kind == "preference_pack":
        return "Preference packs can only be searched, not installed, through Buddy"
    if entry.sparse:
        return f"'{entry.id}' is installed via git only"
    return None


def register(reg: Registration) -> None:
    tool, ctx, names = reg.tool, reg.ctx, reg.names

    @tool
    async def get_design_rules(
        topic: Annotated[
            str | None,
            Field(description=f"Topic: {', '.join(design_rules.TOPIC_KEYS)}; empty = topic overview"),
        ] = None,
    ) -> str:
        """Design rulebook for FreeCAD modelling and FDM printing (values from the active printer profile).
        Read the matching topics before a new design, e.g. sketches and printing."""

        available = set(names)
        if topic is None:
            return design_rules.render_overview(available)
        profile = await ctx.printer_profile()
        try:
            text = design_rules.render_topic(topic, profile, available)
        except KeyError:
            keys = ", ".join(t.key for t in design_rules.visible_topics(available))
            raise ToolError(f"[validation] Unknown topic '{topic}'. Valid: {keys}") from None
        if profile is None:
            text += "\n\n(FreeCAD not reachable - values from the default printer profile)"
        return text

    @tool
    async def search_addons(
        query: Annotated[str, Field(description="Search terms, all must match, e.g. 'grid' or 'honeycomb'")],
        kind: Literal["any", "workbench", "macro", "preference_pack"] = "any",
        limit: Annotated[int, Field(ge=1, le=50)] = 10,
        refresh: Annotated[
            bool, Field(description="Reload the catalogue now (otherwise at most daily)")
        ] = False,
    ) -> dict[str, Any]:
        """Search the official FreeCAD addon catalogue (workbenches, macros, preference packs): hits with
        compatibility to the running FreeCAD and install status. Check before proposing an own design tool."""
        service, state = await ctx.catalog(refresh)
        status = await ctx.installed()
        version = _version(status)
        hits = search(service.entries(), query, None if kind == "any" else kind, limit)
        results = [
            {**e.summary(version), "installed": _installed_flag(e, status), "score": s} for e, s in hits
        ]
        warnings = [state["warning"]] if "warning" in state else []
        if status is None:
            warnings.append("FreeCAD not reachable: compatibility and install status unknown")
        return {"catalog": state, "freecad_version": status and status["freecad_version"], "query": query,
                "count": len(results), "results": results, "warnings": warnings}  # fmt: skip

    @tool
    async def get_addon(
        addon_id: Annotated[str, Field(description="Id or name from search_addons, e.g. 'lattice2'")],
        readme: Annotated[bool, Field(description="Load a README excerpt from the repository")] = True,
    ) -> dict[str, Any]:
        """Details of an addon or macro: licence, maintainer, repository, last update,
        dependencies (FreeCAD, addons, Python), compatibility, install status and README excerpt."""
        service, state = await ctx.catalog()
        entry = service.find(addon_id)
        if entry is None:
            raise ToolError(f"[not_found] No addon '{addon_id}' in the catalogue\nHint: use search_addons")
        status = await ctx.installed()
        details = {**entry.details(_version(status)), "installed": _installed_flag(entry, status),
                   "catalog": state}  # fmt: skip
        if readme:
            text = await service.readme(entry)
            details["readme"] = text
            details["readme_note"] = UNTRUSTED_NOTE if text else "README not available"
        return details

    if reg.allow_addon_install:

        @tool
        async def install_addon(
            addon_id: Annotated[str, Field(description="Id from search_addons/get_addon")],
            wait_seconds: Annotated[
                int, Field(ge=0, le=900, description="How long to wait for completion")
            ] = 300,
        ) -> dict[str, Any]:
            """Install an addon or macro through FreeCAD's Addon Manager (needs FreeCAD's opt-in). FreeCAD shows the user
            a confirmation dialog - ask in the chat first. Workbenches need a FreeCAD restart afterwards."""
            service, state = await ctx.catalog()
            entry = service.find(addon_id)
            if entry is None:
                raise ToolError(f"[not_found] No addon '{addon_id}' in the catalog\nHint: use search_addons")
            status = await ctx.installed()
            if status is None:
                raise ToolError("[bridge_unavailable] FreeCAD is not reachable - cannot install")
            reason = _install_blocker(entry, status)
            if reason:
                raise ToolError(
                    f"[validation] {reason}\nHint: install it with FreeCAD's Addon Manager instead"
                )
            job = await ctx.call(
                "install_addon", "addons.install", addon_id=entry.id, kind=entry.kind, entry=service.raw(entry),
                details=entry.details(_version(status)), branch=entry.branch,
            )  # fmt: skip
            deadline = time.monotonic() + wait_seconds
            while not job["done"] and time.monotonic() < deadline:
                await asyncio.sleep(1)
                job = await ctx.call("install_addon", "addons.install_status", job_id=job["job_id"])
            if not job["done"]:
                job["hint"] = (
                    "Waiting for the user to confirm the dialog in FreeCAD - call install_addon again for the status."
                    if job["state"] == "awaiting_confirmation"
                    else "Still downloading/installing - call install_addon again for the status."
                )
            if job["state"] == "declined":
                raise ToolError(
                    "[user_declined] Installation declined in the FreeCAD dialog - nothing changed"
                )
            if job["state"] == "failed":
                raise ToolError(
                    f"[install_failed] {job['message']}\nHint: retry with FreeCAD's Addon Manager"
                )
            return {**job, "catalog": state}
