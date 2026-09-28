"""Selection style (LineWidth 4, PointSize 8) for created bodies and features."""

from types import SimpleNamespace
from typing import Any

import FreeCAD
import pytest

from buddy_core import display


def test_without_gui_nothing_is_touched() -> None:
    assert display.apply_selection_style(SimpleNamespace(ViewObject=SimpleNamespace(LineWidth=1.0))) is False


def test_style_is_applied_with_gui_and_overridable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(display, "_gui_up", lambda: True)
    view_object = SimpleNamespace(LineWidth=1.0, PointSize=2.0)

    assert display.apply_selection_style(SimpleNamespace(ViewObject=view_object)) is True
    assert (view_object.LineWidth, view_object.PointSize) == (4.0, 8.0)

    params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/FreeCADBuddy")
    params.SetFloat("LineWidth", 3.0)
    try:
        display.apply_selection_style(SimpleNamespace(ViewObject=view_object))
        assert view_object.LineWidth == 3.0
    finally:
        params.RemFloat("LineWidth")


def test_objects_without_view_provider_are_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(display, "_gui_up", lambda: True)
    obj: Any = SimpleNamespace(ViewObject=None)
    assert display.apply_selection_style(obj) is False


def test_show_only_sets_object_and_view_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(display, "_gui_up", lambda: True)
    shown: Any = SimpleNamespace(Visibility=False, ViewObject=SimpleNamespace(Visibility=False))
    hidden: Any = SimpleNamespace(Visibility=True, ViewObject=SimpleNamespace(Visibility=True))

    display.show_only(shown, [hidden])

    assert shown.Visibility and shown.ViewObject.Visibility
    assert not hidden.Visibility and not hidden.ViewObject.Visibility
