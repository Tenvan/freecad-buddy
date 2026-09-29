"""Gears (freecad.gears) and STEP reference parts (step.parts) in FreeCAD."""

from pathlib import Path
from typing import Any

import Part
import pytest

from buddy_core import assembly, body, gears
from buddy_core.errors import UNSUPPORTED, VALIDATION, CoreError

from .conftest import set_params


def _step(tmp_path: Path) -> str:
    path = tmp_path / "block.step"
    Part.makeBox(20, 10, 5).exportStep(str(path))
    return str(path)


def test_step_part_is_a_plain_solid_at_the_position(doc: Any, tmp_path: Path) -> None:
    result = assembly.insert_step(_step(tmp_path), "Block", [5, 0, 3], document=doc.Name).to_dict()

    obj = doc.getObject(result["part"]["name"])
    assert obj.TypeId == "Part::Feature" and obj.Label == "Part_Block"
    assert result["size"] == [20, 10, 5]
    assert list(obj.Placement.Base) == [5, 0, 3]


def test_step_part_joins_the_assembly(doc: Any, tmp_path: Path) -> None:
    assembly.create_assembly(document=doc.Name)
    result = assembly.insert_step(_step(tmp_path), "Block", [0, 0, 7], document=doc.Name).to_dict()

    obj = doc.getObject(result["part"]["name"])
    assert obj.getParentGeoFeatureGroup().Name == assembly.ASSEMBLY
    assert obj.SolverId == "Asm4EE" and obj.AttachmentOffset.Base.z == pytest.approx(7)


def test_unreadable_step_file_is_a_validation_error(doc: Any, tmp_path: Path) -> None:
    broken = tmp_path / "broken.step"
    broken.write_text("no step", encoding="utf-8")
    with pytest.raises(CoreError) as info:
        assembly.insert_step(str(broken), "Broken", document=doc.Name)
    assert info.value.name == VALIDATION


def test_gear_without_addon_reports_the_install_hint(doc: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> Any:
        raise ImportError(name)

    monkeypatch.setattr(gears.importlib, "import_module", missing)
    with pytest.raises(CoreError) as info:
        gears.add_gear(document=doc.Name)
    assert info.value.name == UNSUPPORTED
    assert "freecad.gears" in info.value.data["hints"][0]


def test_involute_gear_is_a_parametric_body_feature(doc: Any) -> None:
    pytest.importorskip("freecad.gears.involutegear")
    body.create_body("Gear", document=doc.Name)
    set_params(doc, Gear_Teeth=20)

    result = gears.add_gear(
        teeth="Gear_Teeth", module=2, height=6, purpose="Drive", document=doc.Name
    ).to_dict()

    gear = doc.getObject(result["feature"]["name"])
    assert gear.Label == "Gear_Drive" and doc.getObjectsByLabel("Gear")[0].Tip == gear
    assert result["gear"]["pitch_diameter"] == pytest.approx(40)
    set_params(doc, Gear_Teeth=30)
    doc.recompute()
    assert gear.pitch_diameter.Value == pytest.approx(60)
    with pytest.raises(CoreError):
        gears.add_gear(properties={"no_such": 1}, document=doc.Name)
