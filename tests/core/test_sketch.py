from typing import Any

import pytest

from buddy_core.errors import SKETCH_INVALID, VALIDATION, CoreError
from buddy_core.sketch import assist, lowlevel, model

from .conftest import profile, set_params, sketch_on

PROFILES = {
    "rectangle": {"width": 60, "height": 40},
    "rectangle_offset": {"width": 20, "height": 10, "center": [15, -5]},
    "rectangle_corner": {"width": 20, "height": 10, "anchor": "corner"},
    "rounded_rectangle": {"width": 60, "height": 40, "radius": 5},
    "slot": {"length": 30, "width": 8},
    "circle": {"diameter": 10, "center": [0, 12]},
    "polygon": {"sides": 6, "across_flats": 13},
    "hole_rect": {"width": 50, "height": 30, "diameter": 3.4},
}


@pytest.mark.parametrize("name", PROFILES)
def test_profiles_are_fully_constrained_like_hand_drawn(doc: Any, part: Any, name: str) -> None:
    sketch = sketch_on(doc)
    kind = name.removesuffix("_offset").removesuffix("_corner")

    result = profile(doc, sketch, kind, **PROFILES[name])

    report = result["sketch"]
    assert report["dof"] == 0, report
    assert report["fully_constrained"]
    assert not (report["conflicting"] or report["redundant"] or report["malformed"])
    assert report["closed_wires"] >= 1
    assert all(c.Type != "Block" for c in sketch.Constraints)
    dims = [
        c
        for c in sketch.Constraints
        if c.Type in {"Distance", "DistanceX", "DistanceY", "Radius", "Diameter"}
    ]
    assert dims and all(c.Name for c in dims)


def test_rectangle_uses_symmetry_instead_of_position_dimensions(doc: Any, part: Any) -> None:
    sketch = sketch_on(doc)
    profile(doc, sketch, "rectangle", width=60, height=40)

    types = sorted(c.Type for c in sketch.Constraints)
    assert types.count("Symmetric") == 1
    assert {c.Name for c in sketch.Constraints if c.Name} == {"Width", "Height"}


def test_dimensions_bind_to_parameters_and_follow_changes(doc: Any, part: Any) -> None:
    set_params(doc, Box_Width=60, Box_Depth=40)
    sketch = sketch_on(doc)
    result = profile(doc, sketch, "rectangle", width="Box_Width", height="Box_Depth")

    assert result["sketch"]["lint"] == []  # all dimensions named and bound
    set_params(doc, Box_Width=80)
    doc.recompute()
    assert abs(sketch.Shape.BoundBox.XLength - 80) < 1e-6


def test_scaled_parameter_expression_for_slot_radius(doc: Any, part: Any) -> None:
    set_params(doc, Slot_Width=8)
    sketch = sketch_on(doc)
    profile(doc, sketch, "slot", length=30, width="Slot_Width")

    set_params(doc, Slot_Width=10)
    doc.recompute()
    assert abs(sketch.Shape.BoundBox.YLength - 10) < 1e-6


def test_two_profiles_in_one_sketch_get_unique_names(doc: Any, part: Any) -> None:
    sketch = sketch_on(doc)
    profile(doc, sketch, "circle", diameter=5, center=[-10, 0])
    result = profile(doc, sketch, "circle", diameter=5, center=[10, 0])

    assert result["sketch"]["dof"] == 0
    names = [c.Name for c in sketch.Constraints if c.Name]
    assert len(names) == len(set(names))


def test_unknown_profile_and_missing_values(doc: Any, part: Any) -> None:
    sketch = sketch_on(doc)
    with pytest.raises(CoreError) as unknown:
        profile(doc, sketch, "star")
    with pytest.raises(CoreError) as missing:
        profile(doc, sketch, "rectangle", width=10)

    assert unknown.value.name == missing.value.name == VALIDATION


def test_conflicting_constraint_is_rolled_back(doc: Any, part: Any) -> None:
    sketch = sketch_on(doc)
    profile(doc, sketch, "rectangle", width=60, height=40)
    count = sketch.ConstraintCount

    with pytest.raises(CoreError) as info:
        lowlevel.add_constraints(
            sketch.Name, [{"type": "distance_x", "a": "g0.start", "b": "g0.end", "value": 70}], doc.Name
        )

    assert info.value.name == SKETCH_INVALID
    assert sketch.ConstraintCount == count


def test_lowlevel_geometry_and_constraints(doc: Any, part: Any) -> None:
    sketch = sketch_on(doc)
    geo = lowlevel.add_geometry(
        sketch.Name, [{"type": "line", "start": [0, 0], "end": [10, 0]}], doc.Name
    ).to_dict()
    assert geo["geometry"] == ["g0"]

    result = lowlevel.add_constraints(
        sketch.Name,
        [
            {"type": "coincident", "a": "g0.start", "b": "origin"},
            {"type": "horizontal", "a": "g0"},
            {"type": "distance", "a": "g0", "value": 25, "name": "Length"},
        ],
        doc.Name,
    ).to_dict()

    assert result["sketch"]["dof"] == 0
    assert abs(sketch.Geometry[0].length() - 25) < 1e-6
    assert result["warnings"]  # open wire warning


def test_polyline_then_assistant_reaches_zero_dof(doc: Any, part: Any) -> None:
    sketch = sketch_on(doc)
    first = profile(doc, sketch, "polyline", points=[[0, 0], [40, 0], [40, 10], [10, 25]])
    assert first["sketch"]["dof"] > 0

    preview = assist.fully_constrain_sketch(sketch.Name, apply=False, document=doc.Name).to_dict()
    assert preview["free_points"]

    applied = assist.fully_constrain_sketch(sketch.Name, apply=True, document=doc.Name).to_dict()
    assert applied["sketch"]["dof"] == 0
    assert not applied["sketch"]["redundant"]
    assert all(c.Type != "Block" for c in sketch.Constraints)


def test_face_attachment_requires_opt_in(doc: Any, part: Any) -> None:
    with pytest.raises(CoreError) as info:
        model.create_sketch(plane="face:top", document=doc.Name)

    assert info.value.name == VALIDATION


def test_sketch_offset_bound_to_parameter(doc: Any, part: Any) -> None:
    set_params(doc, Lid_Height=30)
    sketch = sketch_on(doc, purpose="Lid", offset="Lid_Height")

    set_params(doc, Lid_Height=35)
    doc.recompute()
    assert abs(sketch.Placement.Base.z - 35) < 1e-6
