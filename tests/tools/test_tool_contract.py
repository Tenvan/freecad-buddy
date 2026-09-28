"""Static contract check: every MCP tool calls a bridge method that the bridge actually registers.

Runs in the project venv (the bridge's method table imports FreeCAD, so it is parsed, not imported).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "src" / "buddy_server" / "tools.py"
METHODS = ROOT / "addon" / "FreeCADBuddy" / "buddy_bridge" / "methods.py"


def test_server_tools_only_use_registered_bridge_methods() -> None:
    source = TOOLS.read_text(encoding="utf-8")
    called = set(re.findall(r'ctx\.call\(\s*"[a-z_]+",\s*"([a-z_.]+)"', source))
    called |= set(re.findall(r'self\.bridge\.call\(\s*"([a-z_.]+)"', source))  # used inside ToolContext
    registered = set(re.findall(r'^\s*"([a-z_]+\.[a-z_]+)": \(', METHODS.read_text(encoding="utf-8"), re.M))

    assert called, "keine Tool-Aufrufe gefunden – Regex veraltet?"
    assert called <= registered, f"nicht registriert: {sorted(called - registered)}"
    unused = registered - called - {"system.ping"}  # ping is used by the watchdog
    assert not unused, f"Bridge-Methoden ohne Tool: {sorted(unused)}"
