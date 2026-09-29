"""AC-17 (R-13): everything the MCP server hands to clients is English.

Dynamic: instructions, rulebook, prompts, resources and tool schemas. Static: every string literal in
server, core and bridge that can end up in a tool result, warning, hint or error. User interface texts
stay German (OF-09): whole files below, single lines marked with ``# ui-de``.
"""

import ast
import asyncio
import re
from pathlib import Path
from typing import Any

import pytest

from buddy_server import design_rules
from buddy_server.app import build_mcp
from buddy_server.bridge import Bridge
from buddy_server.config import Settings
from buddy_server.events import EventBus

ROOT = Path(__file__).resolve().parents[2]
GERMAN = re.compile(
    r"[äöüÄÖÜß]|\b(und|nicht|oder|muss|müssen|wird|werden|wurde|ist|sind|kein|keine|keinen|eine|einen|einer|der|"
    r"die|das|dem|den|des|mit|für|auf|bei|nach|zum|zur|vom|im|zu|bitte|Fehler|Skizze|Datei|Dokument|fehlt|"
    r"ungültig|Unbekannte?r?s?|erlaubt|Hinweis|bereits|zuerst|verwenden|prüfen|leer|gefunden|möglich|Bauteil|"
    r"Körper|Maß|Anzahl|Richtung|Ebene|Fläche|Kante|Muster|Bohrung|Tiefe|Breite|Höhe|Länge)\b"
)
UI_FILES = {
    "src/buddy_server/tui.py",
    "src/buddy_server/chat.py",
    "src/buddy_server/cli.py",
    "src/buddy_server/payloads.py",
    "src/buddy_server/splitter.py",
    "src/buddy_server/logs.py",
    "src/buddy_server/runner.py",
    "src/buddy_server/catalog.py",  # German headings of docs/tools.md
    "addon/FreeCADBuddy/InitGui.py",
    "addon/FreeCADBuddy/buddy_bridge/commands.py",
    "addon/FreeCADBuddy/buddy_core/naming.py",  # transliterates umlauts
}
UI_MARK = "# ui-de"


def _texts(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _texts(item)]
    if isinstance(value, list):
        return [text for item in value for text in _texts(item)]
    return []


def _german(texts: list[str]) -> list[str]:
    allowed = "'Benötigte Addons'"  # literal README heading the rules ask for (design_rules, # ui-de)
    return [text[:160] for text in texts if GERMAN.search(text.replace(allowed, ""))]


def test_instructions_rulebook_prompts_and_schemas_are_english() -> None:
    settings = Settings(allow_python=True, allow_addon_install=True)
    bus = EventBus()
    mcp, names = build_mcp(settings, Bridge(settings, bus), bus)

    async def collect() -> list[str]:
        tools = await mcp.list_tools()
        texts = [
            mcp.instructions or "",
            design_rules.render_all(None, set(names)),
            design_rules.render_overview(),
        ]
        for tool in tools:
            texts += [tool.description or "", *_texts(tool.input_schema)]
        for prompt in await mcp.list_prompts():
            texts.append(prompt.description or "")
        texts += [resource.title or "" for resource in await mcp.list_resources()]
        texts += [template.title or "" for template in await mcp.list_resource_templates()]
        return texts

    assert _german(asyncio.run(collect())) == []


def _docstrings(tree: ast.AST) -> set[int]:
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                found.add(id(body[0].value))
    return found


def _sources() -> list[Path]:
    files = [*(ROOT / "src/buddy_server").rglob("*.py"), *(ROOT / "addon/FreeCADBuddy").rglob("*.py")]
    return [f for f in files if f.relative_to(ROOT).as_posix() not in UI_FILES]


@pytest.mark.parametrize("path", _sources(), ids=lambda p: p.relative_to(ROOT).as_posix())
def test_messages_in_source_are_english(path: Path) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    tree = ast.parse("\n".join(lines))
    skip = _docstrings(tree)
    found = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)) or id(node) in skip:
            continue
        span = lines[node.lineno - 1 : (node.end_lineno or node.lineno) + 1]
        if GERMAN.search(node.value) and not any(UI_MARK in line for line in span):
            found.append(f"{node.lineno}: {node.value[:120]!r}")
    assert found == []
