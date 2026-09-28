from typing import Any

import pytest

from buddy_core import features, select, values
from buddy_core.errors import NOT_FOUND, VALIDATION, CoreError

from .conftest import profile, set_params, sketch_on


def test_numbers_names_and_expressions(doc: Any) -> None:
    set_params(doc, Length=80, Wall=2)

    assert values.resolve(doc, 5, "x") == values.Value(5.0)
    assert values.resolve(doc, "Length", "x") == values.Value(80.0, "<<Parameters>>.Length")
    derived = values.resolve(doc, "Length - 2*Wall + (Wall / 2)", "x")
    assert derived.number == 77.0
    assert derived.expression == (
        "((<<Parameters>>.Length - (2 * <<Parameters>>.Wall)) + (<<Parameters>>.Wall / 2))"
    )
    assert values.resolve(doc, "-Length / 2", "x").number == -40.0


@pytest.mark.parametrize(
    ("spec", "error"),
    [
        ("Missing + 1", NOT_FOUND),
        ("Length ** 2", VALIDATION),
        ("__import__('os')", VALIDATION),
        ("1 +", VALIDATION),
    ],
)
def test_unsafe_or_invalid_expressions_are_rejected(doc: Any, spec: str, error: str) -> None:
    set_params(doc, Length=80)

    with pytest.raises(CoreError) as info:
        values.resolve(doc, spec, "x")

    assert info.value.name == error


def test_derived_dimension_follows_parameters(doc: Any, part: Any) -> None:
    set_params(doc, Outer=60, Wall=2)
    sketch = sketch_on(doc)
    profile(doc, sketch, "rectangle", width="Outer - 2*Wall", height=10)

    set_params(doc, Wall=5)
    doc.recompute()

    assert abs(sketch.Shape.BoundBox.XLength - 50) < 1e-6


def test_coordinate_selector_with_parameter_tracks_inner_corner(doc: Any, part: Any) -> None:
    set_params(doc, Thickness=5)
    sketch = sketch_on(doc, plane="YZ", purpose="Profile")
    profile(doc, sketch, "polyline", points=[[0, 0], [40, 0], [40, 5], [5, 5], [5, 50], [0, 50]])
    from buddy_core.sketch import lowlevel

    lowlevel.add_constraints(
        sketch.Name,
        [
            {"type": "distance", "a": "g0", "value": 40, "name": "Arm"},
            {"type": "distance", "a": "g1", "value": "Thickness", "name": "ArmT"},
            {"type": "distance", "a": "g4", "value": "Thickness", "name": "PlateT"},
            {"type": "distance", "a": "g5", "value": 50, "name": "Height"},
        ],
        doc.Name,
    )
    features.pad(sketch.Name, length=20, mode="symmetric", document=doc.Name)
    fillet = features.fillet(
        "edges:parallel=X,y=Thickness,z=Thickness", radius=2, document=doc.Name
    ).to_dict()
    assert len(fillet["selected"]) == 1

    set_params(doc, Thickness=8)
    doc.recompute()

    feature = doc.getObject(fillet["feature"]["name"])
    assert feature.isValid()
    edge = feature.Base[0].Shape.getElement(feature.Base[1][0])
    assert abs(edge.BoundBox.YMin - 8) < 1e-6 and abs(edge.BoundBox.ZMin - 8) < 1e-6


@pytest.mark.parametrize("bad", ["top", "planes:top", "faces:", "edges:sideways", "faces:normal=+W"])
def test_selector_grammar_errors(doc: Any, part: Any, bad: str) -> None:
    import Part

    with pytest.raises(CoreError) as info:
        select.resolve(Part.makeBox(1, 1, 1), bad)

    assert info.value.name == VALIDATION
