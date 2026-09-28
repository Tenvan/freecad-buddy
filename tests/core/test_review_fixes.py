"""Regression tests for findings of the independent review (2026-09-27)."""

from pathlib import Path
from typing import Any

import pytest

from buddy_core import documents, features, values
from buddy_core.errors import BUSY_USER_TRANSACTION, VALIDATION, CoreError
from buddy_core.printing import export, profile

from .conftest import profile as add_profile
from .conftest import set_params, sketch_on


def test_numbers_in_sums_get_the_parameter_unit(doc: Any, part: Any) -> None:
    set_params(doc, Height=10)
    sketch = sketch_on(doc)
    add_profile(doc, sketch, "rectangle", width=20, height=20)

    result = features.pad(sketch.Name, length="Height + 2", document=doc.Name).to_dict()

    assert abs(result["volume"] - 20 * 20 * 12) < 1e-6
    set_params(doc, Height=20)
    assert abs(doc.getObject(result["feature"]["name"]).Shape.Volume - 20 * 20 * 22) < 1e-6


def test_expression_units_for_differences_and_factors(doc: Any) -> None:
    set_params(
        doc, Length=80, Wall=2, Angle={"value": 30, "type": "angle"}, Count={"value": 3, "type": "integer"}
    )

    assert values.resolve(doc, "Length - 2*Wall - 0.5", "x").expression == (
        "((<<Parameters>>.Length - (2 * <<Parameters>>.Wall)) - 0.5 mm)"
    )
    assert values.resolve(doc, "Angle + 15", "x").expression == "(<<Parameters>>.Angle + 15 deg)"
    assert values.resolve(doc, "Count + 1", "x").expression == "(<<Parameters>>.Count + 1)"
    assert values.resolve(doc, "10 / 4", "x") == values.Value(2.5)


@pytest.mark.parametrize("name", ["N", "mm", "pi", "e", "h", "deg"])
def test_parameter_names_that_are_units_are_rejected(doc: Any, name: str) -> None:
    with pytest.raises(CoreError) as info:
        set_params(doc, **{name: 5})

    assert info.value.name == VALIDATION
    assert "Einheit" in info.value.message


def test_export_enforces_extension_and_overwrite(doc: Any, part: Any, tmp_path: Path) -> None:
    sketch = sketch_on(doc)
    add_profile(doc, sketch, "rectangle", width=20, height=20)
    features.pad(sketch.Name, length=5, document=doc.Name)
    profile_file = str(tmp_path / "profile.toml")

    with pytest.raises(CoreError, match="Dateiendung"):
        export.export_body(
            "3mf", path=str(tmp_path / "teil.stl"), document=doc.Name, profile_path=profile_file
        )
    target = tmp_path / "teil.3mf"
    export.export_body("3mf", path=str(target), document=doc.Name, profile_path=profile_file)
    with pytest.raises(CoreError, match="existiert bereits"):
        export.export_body("3mf", path=str(target), document=doc.Name, profile_path=profile_file)
    assert export.export_body(
        "3mf", path=str(target), document=doc.Name, profile_path=profile_file, overwrite=True
    )["ok"]


def test_undo_respects_user_edit(doc: Any, part: Any) -> None:
    sketch_on(doc)
    doc.openTransaction("Nutzer")
    doc.addObject("App::FeaturePython", "UserChange")
    try:
        with pytest.raises(CoreError) as info:
            documents.undo(doc.Name)
    finally:
        doc.abortTransaction()

    assert info.value.name == BUSY_USER_TRANSACTION
    assert doc.getObjectsByLabel("Sketch_Base")


def test_material_with_control_characters_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(CoreError, match="Steuerzeichen"):
        profile.set_printer_profile({"material": "PLA\nnozzle = 0"}, path=str(tmp_path / "p.toml"))
