"""Display style of created objects: thicker edges and larger vertices for selecting in the 3D view.

FreeCAD's global defaults (View → DefaultShapeLineWidth/PointSize) do not reach PartDesign
features created from Python, so every body and feature gets the style explicitly.
Override per user: ``Preferences/Mod/FreeCADBuddy`` → ``LineWidth`` / ``PointSize`` (float).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import FreeCAD

LINE_WIDTH = 4.0
POINT_SIZE = 8.0
_PARAM_GROUP = "User parameter:BaseApp/Preferences/Mod/FreeCADBuddy"


def _gui_up() -> bool:
    return bool(FreeCAD.GuiUp)


def style() -> tuple[float, float]:
    params = FreeCAD.ParamGet(_PARAM_GROUP)
    return params.GetFloat("LineWidth", LINE_WIDTH), params.GetFloat("PointSize", POINT_SIZE)


def show_only(shown: Any, hidden: Iterable[Any]) -> None:
    """Show ``shown`` and hide ``hidden`` – on the object and, with GUI, on its view provider.

    ``shown`` goes first: making a PartDesign feature visible in the GUI hides the other features
    of its body, the explicit hiding afterwards covers everything outside that rule (headless too).
    """
    for obj, visible in ((shown, True), *((obj, False) for obj in hidden)):
        obj.Visibility = visible
        view_object = getattr(obj, "ViewObject", None) if _gui_up() else None
        if view_object is not None:
            view_object.Visibility = visible


def apply_selection_style(obj: Any) -> bool:
    """Set LineWidth/PointSize on ``obj``'s view provider; ``False`` without GUI or view provider."""
    view_object = getattr(obj, "ViewObject", None) if _gui_up() else None
    if view_object is None:
        return False
    line_width, point_size = style()
    changed = False
    for prop, value in (("LineWidth", line_width), ("PointSize", point_size)):
        if hasattr(view_object, prop):
            setattr(view_object, prop, value)
            changed = True
    return changed
