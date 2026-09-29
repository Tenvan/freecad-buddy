"""AC-11: design tool fill_pattern (round or hex cells, one call, one undo step, parametric)."""

import math
import time
from typing import Any

import Part
import pytest

from buddy_core import design_tools, features
from buddy_core.errors import CoreError

from .conftest import profile, set_params, sketch_on

THICKNESS = 2.0


def _plate(doc: Any, width: float, depth: float) -> Any:
    sketch = sketch_on(doc, purpose="Plate")
    profile(doc, sketch, "rectangle", width=width, height=depth)
    return features.pad(sketch.Name, length=THICKNESS, purpose="Plate", document=doc.Name)


def _hole(diameter: float) -> float:
    return math.pi * (diameter / 2) ** 2 * THICKNESS


def _hexagon(across_flats: float) -> float:
    return math.sqrt(3) / 2 * across_flats**2 * THICKNESS


def _param(doc: Any, name: str) -> Any:
    return doc.getObjectsByLabel("Parameters")[0].getPropertyByName(name)


def test_sieve_of_the_test_plate_in_one_call_and_one_undo_step(doc: Any, part: Any) -> None:
    _plate(doc, 150, 120)
    undo_before, objects_before = doc.UndoCount, len(doc.Objects)

    started = time.perf_counter()
    result = design_tools.fill_pattern(
        size=1, pitch=3, count=[34, 27], offset=THICKNESS, name="Sieve", document=doc.Name
    ).to_dict()
    elapsed = time.perf_counter() - started

    grid = doc.getObject(result["feature"]["name"])
    assert grid.TypeId == "PartDesign::MultiTransform" and part.Tip is grid
    assert result["cells"] == 34 * 27 and result["cell"] == "round" and result["layout"] == "rect"
    assert abs(grid.Shape.Volume - (150 * 120 * THICKNESS - 34 * 27 * _hole(1))) < 1e-2
    assert doc.UndoCount == undo_before + 1
    sketch = doc.getObjectsByLabel("Sketch_Sieve")[0]
    assert sketch.solve() == 0 and len(sketch.Geometry) == 1
    assert elapsed < 30, f"918 cells took {elapsed:.1f} s"

    set_params(doc, Sieve_Pitch=4)
    assert abs(grid.Shape.Volume - (150 * 120 * THICKNESS - 34 * 27 * _hole(1))) < 1e-2
    assert abs(grid.Shape.BoundBox.XLength - 150) < 1e-6

    doc.undo()  # parameter change
    doc.undo()  # the whole fill
    assert len(doc.Objects) == objects_before


def test_field_mode_derives_counts_that_follow_the_pitch(doc: Any, part: Any) -> None:
    _plate(doc, 80, 60)

    result = design_tools.fill_pattern(
        size=2, pitch=5, field=[60, 40], margin=2, offset=THICKNESS, name="Vent", document=doc.Name
    ).to_dict()

    assert result["count"] == [11, 7]  # floor((60 - 4 - 2) / 5) + 1, floor((40 - 4 - 2) / 5) + 1
    grid = doc.getObject(result["feature"]["name"])
    set_params(doc, Vent_Pitch=6)
    assert (_param(doc, "Vent_Count_X"), _param(doc, "Vent_Count_Y")) == (10, 6)
    assert abs(grid.Shape.Volume - (80 * 60 * THICKNESS - 60 * _hole(2))) < 1e-2


def test_round_cells_in_hex_layout_offset_every_second_row(doc: Any, part: Any) -> None:
    _plate(doc, 80, 60)

    result = design_tools.fill_pattern(
        size=2, pitch=5, count=[6, 4], layout="hex", offset=THICKNESS, name="Staggered", document=doc.Name
    ).to_dict()

    grid = doc.getObject(result["feature"]["name"])
    assert abs(grid.Shape.Volume - (80 * 60 * THICKNESS - 24 * _hole(2))) < 1e-2
    sketch = doc.getObjectsByLabel("Sketch_Staggered")[0]
    assert sketch.solve() == 0 and len(sketch.Geometry) == 2
    first, second = (g.Location for g in sketch.Geometry)
    assert abs(second.x - first.x - 2.5) < 1e-6 and abs(second.y - first.y - 5 * math.sqrt(3) / 2) < 1e-6


def test_honeycomb_with_corner_up_hex_cells(doc: Any, part: Any) -> None:
    _plate(doc, 120, 100)

    started = time.perf_counter()
    result = design_tools.fill_pattern(
        size=5,
        pitch=6,
        cell="hex",
        field=[100, 80],
        margin=3,
        offset=THICKNESS,
        name="Honey",
        document=doc.Name,
    ).to_dict()
    elapsed = time.perf_counter() - started

    assert result["layout"] == "hex"  # default for hex cells
    nx, ny = result["count"]
    assert nx * ny > 150
    grid = doc.getObject(result["feature"]["name"])
    assert abs(grid.Shape.Volume - (120 * 100 * THICKNESS - nx * ny * _hexagon(5))) < 1e-2
    assert grid.Shape.isValid() and elapsed < 30
    sketch = doc.getObjectsByLabel("Sketch_Honey")[0]
    assert sketch.solve() == 0
    edges = [g for g in sketch.Geometry if isinstance(g, Part.LineSegment)]
    vertical = [g for g in edges if abs(g.StartPoint.x - g.EndPoint.x) < 1e-9]
    assert len(edges) == 12 and len(vertical) == 4  # corner up: two vertical flanks per cell

    set_params(doc, Honey_Size=4)
    assert abs(grid.Shape.Volume - (120 * 100 * THICKNESS - nx * ny * _hexagon(4))) < 1e-2


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"size": 3, "pitch": 3, "count": [4, 4]}, "smaller than pitch"),
        ({"size": 1, "pitch": 3, "field": [3, 20]}, "too small"),
        ({"size": 1, "pitch": 3, "count": [4, 5], "layout": "hex"}, "even row count"),
        ({"size": 1, "pitch": 3}, "either count"),
        ({"size": 1, "pitch": 3, "count": [4, 4], "cell": "square"}, "cell must be"),
    ],
)
def test_invalid_fills_are_rejected_with_the_reason(doc: Any, part: Any, kwargs: Any, message: str) -> None:
    _plate(doc, 80, 60)
    objects = len(doc.Objects)

    with pytest.raises(CoreError) as info:
        design_tools.fill_pattern(offset=THICKNESS, document=doc.Name, **kwargs)

    assert info.value.name == "validation" and message in str(info.value)
    assert len(doc.Objects) == objects


def test_second_fill_needs_its_own_name(doc: Any, part: Any) -> None:
    _plate(doc, 80, 60)
    design_tools.fill_pattern(size=1, pitch=3, count=[3, 3], offset=THICKNESS, document=doc.Name)

    with pytest.raises(CoreError) as info:
        design_tools.fill_pattern(size=1, pitch=3, count=[3, 3], offset=THICKNESS, document=doc.Name)

    assert "already exist" in str(info.value)


def test_field_bound_to_part_parameters_follows_the_part(doc: Any, part: Any) -> None:
    set_params(doc, Plate_Width=80, Rim_Width=5)
    _plate(doc, 120, 60)

    result = design_tools.fill_pattern(
        size=2,
        pitch=5,
        field=["Plate_Width - 2*Rim_Width", 50],
        offset=THICKNESS,
        name="Bound",
        document=doc.Name,
    ).to_dict()

    assert result["count"] == [14, 10]  # floor((70 - 2) / 5) + 1, floor((50 - 2) / 5) + 1
    set_params(doc, Plate_Width=100)
    assert _param(doc, "Bound_Width").Value == 90
    assert _param(doc, "Bound_Count_X") == 18  # floor((90 - 2) / 5) + 1
    grid = doc.getObject(result["feature"]["name"])
    assert abs(grid.Shape.Volume - (120 * 60 * THICKNESS - 18 * 10 * _hole(2))) < 1e-2
