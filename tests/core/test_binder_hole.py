"""shape_binder across bodies and parametric hole cuts."""

from typing import Any

import pytest

from buddy_core import binder, body, features
from buddy_core.errors import VALIDATION, CoreError
from buddy_core.sketch import lowlevel

from .conftest import profile, set_params, sketch_on


def box_and_lid(doc: Any) -> tuple[Any, Any]:
    """Body 'Part' with Sketch_Base (Box_Width x 40) and an empty body 'Lid'."""
    set_params(doc, Box_Width=60)
    base = sketch_on(doc, purpose="Base")
    profile(doc, base, "rectangle", width="Box_Width", height=40)
    features.pad(base.Name, length=10, document=doc.Name)
    body.create_body("Lid", document=doc.Name)
    return base, doc.getObjectsByLabel("Lid")[0]


def test_binder_follows_source_and_drives_external_geometry(doc: Any, part: Any) -> None:
    _, lid = box_and_lid(doc)

    result = binder.shape_binder(["Part:Sketch_Base"], body="Lid", purpose="BoxOutline", document=doc.Name)

    data = result.to_dict()
    bound = doc.getObjectsByLabel("Binder_BoxOutline")[0]
    assert bound.TypeId == "PartDesign::SubShapeBinder" and bound in lid.Group
    assert data["elements"]["edges"] == 4
    sketch = sketch_on(doc, purpose="LidOutline", body="Lid")
    added = lowlevel.add_geometry(
        sketch.Name,
        [
            {"type": "external", "source": bound.Label, "element": f"Edge{i}", "defining": True}
            for i in range(1, 5)
        ],
        doc.Name,
    ).to_dict()
    assert added["geometry"] == ["x0", "x1", "x2", "x3"]

    set_params(doc, Box_Width=80)
    doc.recompute()
    assert abs(sketch.Shape.BoundBox.XLength - 80) < 1e-6
    assert bound.isValid() and sketch.isValid()


def test_binder_of_single_sketch_element(doc: Any, part: Any) -> None:
    box_and_lid(doc)

    binder.shape_binder(["Sketch_Base:g0"], body="Lid", purpose="Edge", document=doc.Name)

    assert len(doc.getObjectsByLabel("Binder_Edge")[0].Shape.Edges) == 1


@pytest.mark.parametrize(
    ("sources", "fragment"),
    [
        (["Lid"], "already in body"),
        (["Sketch_Base:g9"], "does not exist"),
        (["A:B:C"], "not_found"),  # error code; the legacy message is still German (#5.4 other sprint)
        ([], "must not be empty"),
    ],
)
def test_binder_rejects_invalid_sources(doc: Any, part: Any, sources: list[str], fragment: str) -> None:
    box_and_lid(doc)
    before = list(doc.UndoNames)

    with pytest.raises(CoreError) as info:
        binder.shape_binder(sources, body="Lid", document=doc.Name)

    assert fragment in (info.value.message, info.value.name) or fragment in info.value.message
    assert list(doc.UndoNames) == before


def hole_setup(doc: Any) -> Any:
    set_params(doc, Head_D=6.5, Plate=10, Floor=3)
    plate = sketch_on(doc, purpose="Plate")
    profile(doc, plate, "rectangle", width=40, height=40)
    features.pad(plate.Name, length="Plate", document=doc.Name)
    holes = sketch_on(doc, purpose="Holes", offset="Plate")
    profile(doc, holes, "circle", diameter=3.4)
    return holes


def test_counterbore_uses_parametric_diameter_and_depth(doc: Any, part: Any) -> None:
    holes = hole_setup(doc)

    features.hole(
        holes.Name, cut="counterbore", diameter=3.4, cut_diameter="Head_D", cut_depth="Plate - Floor",
        document=doc.Name,
    )  # fmt: skip

    feature = doc.getObjectsByLabel("Hole_M3Counterbore")[0]
    assert feature.HoleCutCustomValues
    assert abs(feature.HoleCutDiameter.Value - 6.5) < 1e-9 and abs(feature.HoleCutDepth.Value - 7) < 1e-9
    set_params(doc, Floor=2)
    doc.recompute()
    assert abs(feature.HoleCutDepth.Value - 8) < 1e-9 and feature.isValid()


def test_countersink_angle_and_diameter(doc: Any, part: Any) -> None:
    holes = hole_setup(doc)

    features.hole(
        holes.Name, cut="countersink", diameter=3.4, cut_diameter=7, countersink_angle=82, document=doc.Name
    )

    feature = doc.getObjectsByLabel("Hole_M3Countersink")[0]
    assert abs(feature.HoleCutCountersinkAngle.Value - 82) < 1e-9
    assert abs(feature.HoleCutDiameter.Value - 7) < 1e-9 and feature.isValid()


@pytest.mark.parametrize(
    ("kwargs", "fragment"),
    [
        ({"cut": "none", "cut_depth": 3}, "need cut="),
        ({"cut": "counterbore", "countersink_angle": 90}, "only applies to cut='countersink'"),
        ({"cut": "countersink", "cut_depth": 3}, "only applies to cut='counterbore'"),
        ({"cut": "counterbore", "diameter": 3.4, "cut_diameter": 3}, "must be larger"),
    ],
)
def test_invalid_hole_cut_combinations(doc: Any, part: Any, kwargs: dict[str, Any], fragment: str) -> None:
    holes = hole_setup(doc)
    before = list(doc.UndoNames)

    with pytest.raises(CoreError) as info:
        features.hole(holes.Name, document=doc.Name, **kwargs)

    assert info.value.name == VALIDATION and fragment in info.value.message
    assert list(doc.UndoNames) == before
