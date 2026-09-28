"""Das Addon läuft in FreeCADs Python: fremde Abhängigkeiten dürfen dort nicht auftauchen."""

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ADDON_DIR = REPO_ROOT / "addon" / "FreeCADBuddy"

ALLOWED_MODULES = frozenset(sys.stdlib_module_names) | {
    "FreeCAD",
    "FreeCADGui",
    "Part",
    "Sketcher",
    "PartDesign",
    "Mesh",
    "MeshPart",
    "PySide",
    "buddy_core",
    "buddy_bridge",
}
FORBIDDEN_QT_MODULES = frozenset({"PySide6", "PySide2"})


def _top_level_module(dotted_name: str) -> str:
    return dotted_name.split(".", 1)[0]


def _iter_forbidden_imports() -> list[str]:
    violations = []
    for path in sorted(ADDON_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = _top_level_module(alias.name)
                    if module in FORBIDDEN_QT_MODULES or module not in ALLOWED_MODULES:
                        violations.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}:{module}")
            elif isinstance(node, ast.ImportFrom):
                # level > 0 = relative Import ("from . import x"), immer erlaubt.
                if node.level > 0 or node.module is None:
                    continue
                module = _top_level_module(node.module)
                if module in FORBIDDEN_QT_MODULES or module not in ALLOWED_MODULES:
                    violations.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}:{module}")
    return violations


def test_addon_only_imports_allowed_modules() -> None:
    violations = _iter_forbidden_imports()

    assert violations == [], "Unzulässige Top-Level-Imports:\n" + "\n".join(violations)
