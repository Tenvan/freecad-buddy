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
    "Materials",
    "PySide",
    "buddy_core",
    "buddy_bridge",
}
FORBIDDEN_QT_MODULES = frozenset({"PySide6", "PySide2"})
# FreeCAD's own Addon Manager (ships with FreeCAD) - only the install adapter may import it.
ADDON_MANAGER_MODULES = frozenset(
    {"NetworkManager", "AddonCatalog", "Addon", "addonmanager_installer", "addonmanager_macro"}
)
ADDON_MANAGER_ADAPTER = Path("addon") / "FreeCADBuddy" / "buddy_core" / "addons" / "install.py"
# Optional third-party workbenches: imported lazily, only by their one adapter module.
OPTIONAL_ADDON_ADAPTERS = {"FastenersCmd": Path("addon") / "FreeCADBuddy" / "buddy_core" / "assembly.py"}


def _top_level_module(dotted_name: str) -> str:
    return dotted_name.split(".", 1)[0]


def _allowed_addon_manager(path: Path, module: str) -> bool:
    relative = path.relative_to(REPO_ROOT)
    if module in OPTIONAL_ADDON_ADAPTERS:
        return relative == OPTIONAL_ADDON_ADAPTERS[module]
    return module in ADDON_MANAGER_MODULES and relative == ADDON_MANAGER_ADAPTER


def _iter_forbidden_imports() -> list[str]:
    violations = []
    for path in sorted(ADDON_DIR.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = _top_level_module(alias.name)
                    if _allowed_addon_manager(path, module):
                        continue
                    if module in FORBIDDEN_QT_MODULES or module not in ALLOWED_MODULES:
                        violations.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}:{module}")
            elif isinstance(node, ast.ImportFrom):
                # level > 0 = relative Import ("from . import x"), immer erlaubt.
                if node.level > 0 or node.module is None:
                    continue
                module = _top_level_module(node.module)
                if _allowed_addon_manager(path, module):
                    continue
                if module in FORBIDDEN_QT_MODULES or module not in ALLOWED_MODULES:
                    violations.append(f"{path.relative_to(REPO_ROOT)}:{node.lineno}:{module}")
    return violations


def test_addon_only_imports_allowed_modules() -> None:
    violations = _iter_forbidden_imports()

    assert violations == [], "Unzulässige Top-Level-Imports:\n" + "\n".join(violations)
