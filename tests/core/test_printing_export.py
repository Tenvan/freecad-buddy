from collections.abc import Iterator
from typing import Any

import FreeCAD
import Part
import pytest

from buddy_core.errors import CoreError
from buddy_core.printing import export as export_module


@pytest.fixture
def doc() -> Iterator[Any]:
    document = FreeCAD.newDocument("PrintingExportTest", hidden=True, temp=True)
    yield document
    FreeCAD.closeDocument(document.Name)


def _add_cube(document: Any) -> Any:
    obj = document.addObject("Part::Feature", "Feature")
    obj.Label = "Cube"
    obj.Shape = Part.makeBox(20, 20, 20)
    obj.Placement = FreeCAD.Placement(FreeCAD.Vector(5, 5, 5), FreeCAD.Rotation())
    document.recompute()
    return obj


@pytest.mark.parametrize("export_format", ["stl", "3mf", "step"])
def test_export_places_on_bed_with_low_deviation(doc: Any, tmp_path: Any, export_format: str) -> None:
    obj = _add_cube(doc)
    before_placement = obj.Placement
    before_volume = obj.Shape.Volume

    result = export_module.export_body(
        export_format, target=obj.Label, path=str(tmp_path), place_on_bed=True, document=doc.Name
    )

    assert result["ok"] is True
    assert result["format"] == export_format
    assert result["placed_on_bed"] is True
    assert result["deviation_percent"] < 1.0
    assert result["warnings"] == []

    # The model itself must stay untouched by the export.
    assert obj.Placement == before_placement
    assert obj.Shape.Volume == before_volume


def test_export_stl_places_bound_box_at_bed_origin(doc: Any, tmp_path: Any) -> None:
    obj = _add_cube(doc)

    result = export_module.export_body(
        "stl", target=obj.Label, path=str(tmp_path), place_on_bed=True, document=doc.Name
    )

    import Mesh

    mesh = Mesh.Mesh(result["path"])
    box = mesh.BoundBox
    assert box.ZMin == pytest.approx(0.0, abs=1e-6)
    assert (box.XMin + box.XMax) / 2 == pytest.approx(0.0, abs=1e-6)
    assert (box.YMin + box.YMax) / 2 == pytest.approx(0.0, abs=1e-6)


def test_export_rejects_unknown_format(doc: Any, tmp_path: Any) -> None:
    obj = _add_cube(doc)

    with pytest.raises(CoreError) as excinfo:
        export_module.export_body("obj", target=obj.Label, path=str(tmp_path), document=doc.Name)

    assert excinfo.value.name == "validation"


def test_export_without_path_requires_saved_document(doc: Any) -> None:
    obj = _add_cube(doc)

    with pytest.raises(CoreError) as excinfo:
        export_module.export_body("stl", target=obj.Label, document=doc.Name)

    assert excinfo.value.name == "validation"
