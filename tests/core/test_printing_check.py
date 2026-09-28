from collections.abc import Iterator
from typing import Any

import FreeCAD
import Part
import pytest

from buddy_core.printing import check as check_module
from buddy_core.printing.profile import set_printer_profile


@pytest.fixture
def doc() -> Iterator[Any]:
    document = FreeCAD.newDocument("PrintingCheckTest", hidden=True, temp=True)
    yield document
    FreeCAD.closeDocument(document.Name)


def _add_shape(document: Any, shape: Any, label: str = "Body") -> Any:
    obj = document.addObject("Part::Feature", "Feature")
    obj.Label = label
    obj.Shape = shape
    document.recompute()
    return obj


def test_valid_cube_has_no_issues(doc: Any, tmp_path: Any) -> None:
    obj = _add_shape(doc, Part.makeBox(20, 20, 20), "Cube")

    result = check_module.check_printability(
        target=obj.Label, document=doc.Name, profile_path=str(tmp_path / "profile.toml")
    )

    assert result["ok"] is True
    assert result["issues"] == []
    assert result["stats"]["size"] == [20.0, 20.0, 20.0]


def test_oversized_box_reports_build_volume_error(doc: Any, tmp_path: Any) -> None:
    obj = _add_shape(doc, Part.makeBox(300, 50, 50), "TooBig")

    result = check_module.check_printability(
        target=obj.Label, document=doc.Name, profile_path=str(tmp_path / "profile.toml")
    )

    assert result["ok"] is False
    codes = [issue["code"] for issue in result["issues"]]
    assert "build_volume" in codes


def test_overhang_detected_on_cantilever(doc: Any, tmp_path: Any) -> None:
    # A base block with a beam that overlaps it volumetrically (true fuse, not a face touch)
    # and cantilevers past the base's edge; the beam's underside there hangs in free air.
    base = Part.makeBox(40, 40, 10)
    beam = Part.makeBox(60, 10, 15)
    beam.translate(FreeCAD.Vector(30, 15, 5))
    obj = _add_shape(doc, base.fuse(beam), "Cantilever")

    result = check_module.check_printability(
        target=obj.Label, document=doc.Name, profile_path=str(tmp_path / "profile.toml")
    )

    overhang = next(issue for issue in result["issues"] if issue["code"] == "overhang")
    assert overhang["severity"] == "warning"
    assert overhang["value"]["area"] > 0
    assert overhang["faces"]


def test_thin_wall_detected(doc: Any, tmp_path: Any) -> None:
    outer = Part.makeBox(20, 20, 20)
    inner = Part.makeBox(19.2, 19.2, 20)
    inner.translate(FreeCAD.Vector(0.4, 0.4, 0))
    obj = _add_shape(doc, outer.cut(inner), "ThinWallBox")
    profile_path = tmp_path / "profile.toml"
    set_printer_profile({"min_wall": 0.8}, str(profile_path))

    result = check_module.check_printability(
        target=obj.Label, document=doc.Name, profile_path=str(profile_path)
    )

    thin_wall = next(issue for issue in result["issues"] if issue["code"] == "thin_wall")
    assert thin_wall["severity"] == "warning"
    assert thin_wall["value"] < 0.8
    assert result["stats"]["min_wall_sampled"] == thin_wall["value"]


def test_multiple_solids_detected(doc: Any, tmp_path: Any) -> None:
    cube_a = Part.makeBox(10, 10, 10)
    cube_b = Part.makeBox(10, 10, 10)
    cube_b.translate(FreeCAD.Vector(50, 0, 0))
    obj = _add_shape(doc, Part.makeCompound([cube_a, cube_b]), "TwoCubes")

    result = check_module.check_printability(
        target=obj.Label, document=doc.Name, profile_path=str(tmp_path / "profile.toml")
    )

    assert result["ok"] is False
    codes = [issue["code"] for issue in result["issues"]]
    assert "multiple_solids" in codes


def test_hints_follow_findings_and_profile(doc: Any, tmp_path: Any) -> None:
    from buddy_core.printing.check import design_hints
    from buddy_core.printing.profile import PrinterProfile

    hints = design_hints([{"code": "thin_wall"}], PrinterProfile())

    assert any("0.8 mm" in hint for hint in hints)
    assert any("Elefantenfuß" in hint for hint in hints)
    assert not any("Überhänge" in hint for hint in hints)
