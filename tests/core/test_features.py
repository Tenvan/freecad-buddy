from typing import Any

import pytest

from buddy_core import features, select
from buddy_core.errors import RECOMPUTE_FAILED, CoreError

from .conftest import profile, set_params, sketch_on


def _box(doc: Any, width: Any = 60, depth: Any = 40, height: Any = 20) -> Any:
    sketch = sketch_on(doc)
    profile(doc, sketch, "rectangle", width=width, height=depth)
    result = features.pad(sketch.Name, length=height, purpose="Base", document=doc.Name).to_dict()
    return doc.getObject(result["feature"]["name"])


def test_pad_creates_labelled_solid(doc: Any, part: Any) -> None:
    pad = _box(doc)

    assert pad.Label == "Pad_Base"
    assert abs(pad.Shape.Volume - 60 * 40 * 20) < 1e-6
    assert part.Tip is pad


def test_pocket_on_bottom_plane_is_flipped_automatically(doc: Any, part: Any) -> None:
    _box(doc)
    sketch = sketch_on(doc, purpose="Cutout")
    profile(doc, sketch, "circle", diameter=10)

    result = features.pocket(sketch.Name, depth=5, purpose="Cutout", document=doc.Name).to_dict()

    assert any("umgekehrt" in w for w in result["warnings"])
    assert abs(result["volume"] - (60 * 40 * 20 - 3.14159265 * 25 * 5)) < 1e-2


def test_pocket_through_all(doc: Any, part: Any) -> None:
    _box(doc)
    sketch = sketch_on(doc, purpose="Window", offset=20)
    profile(doc, sketch, "rectangle", width=10, height=10)

    result = features.pocket(sketch.Name, mode="through_all", document=doc.Name).to_dict()

    assert abs(result["volume"] - (60 * 40 * 20 - 10 * 10 * 20)) < 1e-6


def test_pad_that_misses_body_is_rejected(doc: Any, part: Any) -> None:
    _box(doc)
    sketch = sketch_on(doc, purpose="Island")
    profile(doc, sketch, "circle", diameter=5, center=[100, 0])
    objects = len(doc.Objects)

    with pytest.raises(CoreError) as info:
        features.pad(sketch.Name, length=5, document=doc.Name)

    assert info.value.name == RECOMPUTE_FAILED
    assert len(doc.Objects) == objects


def test_hole_pattern_with_countersink(doc: Any, part: Any) -> None:
    pad = _box(doc)
    sketch = sketch_on(doc, purpose="Holes", offset=20)
    profile(doc, sketch, "hole_rect", width=40, height=20, diameter=3)

    result = features.hole(sketch.Name, size="M3", cut="countersink", document=doc.Name).to_dict()

    assert result["volume"] < pad.Shape.Volume
    assert "M3" in doc.getObject(result["feature"]["name"]).ThreadSize


def test_revolution_and_groove(doc: Any, part: Any) -> None:
    sketch = sketch_on(doc, plane="XZ", purpose="Knob")
    profile(doc, sketch, "rectangle", width=10, height=20, anchor="corner")
    revolution = features.revolve(sketch.Name, axis="V_Axis", document=doc.Name).to_dict()
    assert abs(revolution["volume"] - 3.14159265 * 100 * 20) < 1e-2

    groove_sketch = sketch_on(doc, plane="XZ", purpose="Groove")
    profile(doc, groove_sketch, "rectangle", width=2, height=2, center=[10, 10])
    groove = features.revolve(groove_sketch.Name, subtractive=True, document=doc.Name).to_dict()
    assert groove["volume"] < revolution["volume"]


def test_fillet_chamfer_and_shell_use_selectors(doc: Any, part: Any) -> None:
    _box(doc)
    fillet = features.fillet("edges:vertical", radius=3, document=doc.Name).to_dict()
    assert len(fillet["selected"]) == 4

    chamfer = features.chamfer("edges:bottom", size=0.5, document=doc.Name).to_dict()
    assert chamfer["selected"]

    shell = features.shell("face:top", thickness=2, document=doc.Name).to_dict()
    feature = doc.getObject(shell["feature"]["name"])
    assert feature.Shape.Volume < 0.5 * 60 * 40 * 20
    assert feature.BuddySelector == "face:top"


def test_patterns(doc: Any, part: Any) -> None:
    _box(doc, width=100, depth=40, height=10)
    sketch = sketch_on(doc, purpose="Peg", offset=10)
    profile(doc, sketch, "circle", diameter=6, center=[-40, 0])
    peg = features.pad(sketch.Name, length=5, purpose="Peg", document=doc.Name).to_dict()
    peg_volume = 3.14159265 * 9 * 5

    linear = features.pattern(
        [peg["feature"]["name"]], "linear", direction="X", length=60, count=4, document=doc.Name
    )
    assert abs(linear.to_dict()["volume"] - (100 * 40 * 10 + 4 * peg_volume)) < 1e-2

    mirrored = features.pattern([peg["feature"]["name"]], "mirrored", plane="YZ", document=doc.Name).to_dict()
    assert mirrored["volume"] > 100 * 40 * 10


def test_polar_pattern_with_parameter_count(doc: Any, part: Any) -> None:
    set_params(doc, Rib_Count={"value": 6, "type": "integer"})
    sketch = sketch_on(doc, purpose="Disc")
    profile(doc, sketch, "circle", diameter=40)
    features.pad(sketch.Name, length=5, document=doc.Name)
    notch = sketch_on(doc, purpose="Notch", offset=5)
    profile(doc, notch, "circle", diameter=4, center=[17, 0])
    cut = features.pocket(notch.Name, depth=2, document=doc.Name).to_dict()

    polar = features.pattern(
        [cut["feature"]["name"]], "polar", axis="Z", count="Rib_Count", document=doc.Name
    )
    feature = doc.getObject(polar.to_dict()["feature"]["name"])
    assert feature.Occurrences == 6
    set_params(doc, Rib_Count=8)
    assert feature.Occurrences == 8


def test_datum_plane_and_sketch_on_it(doc: Any, part: Any) -> None:
    _box(doc)
    plane = features.datum_plane(base="XY", offset=20, purpose="Top", document=doc.Name).to_dict()
    sketch = sketch_on(doc, plane=plane["plane"]["label"], purpose="Boss")

    assert abs(sketch.Placement.Base.z - 20) < 1e-6


def test_selector_preview_and_errors(doc: Any, part: Any) -> None:
    _box(doc)
    preview = select.select_geometry("faces:top", document=doc.Name)
    assert [m["name"] for m in preview["matches"]] and preview["matches"][0]["normal"] == [0, 0, 1]

    with pytest.raises(CoreError) as ambiguous:
        select.resolve(part.Tip.Shape, "edge:vertical")
    assert ambiguous.value.name == "ambiguous"
    with pytest.raises(CoreError) as empty:
        select.resolve(part.Tip.Shape, "edges:circular")
    assert empty.value.name == "not_found"


def test_grid_pattern_as_multitransform_follows_parameters(doc: Any, part: Any) -> None:
    set_params(doc, Pitch=3, Count_X={"value": 5, "type": "integer"}, Count_Y={"value": 4, "type": "integer"})
    _box(doc, width=60, depth=40, height=5)
    sketch = sketch_on(doc, purpose="Hole", offset=5)
    profile(
        doc, sketch, "circle", diameter=1, center=["-(Count_X - 1) * Pitch / 2", "-(Count_Y - 1) * Pitch / 2"]
    )
    hole = features.pocket(sketch.Name, mode="through_all", purpose="Hole", document=doc.Name).to_dict()

    grid = features.pattern(
        [hole["feature"]["name"]], "grid", direction="X", length="(Count_X - 1) * Pitch", count="Count_X",
        direction2="Y", length2="(Count_Y - 1) * Pitch", count2="Count_Y", purpose="Sieve", document=doc.Name,
    ).to_dict()  # fmt: skip

    hole_volume = 3.14159265 * 0.25 * 5
    feature = doc.getObject(grid["feature"]["name"])
    assert feature.TypeId == "PartDesign::MultiTransform" and part.Tip is feature
    assert abs(grid["volume"] - (60 * 40 * 5 - 20 * hole_volume)) < 1e-3
    set_params(doc, Count_X=6)
    assert abs(feature.Shape.Volume - (60 * 40 * 5 - 24 * hole_volume)) < 1e-3
    assert abs(feature.Shape.BoundBox.XLength - 60) < 1e-6  # field stays centred inside the plate


def test_pattern_of_pattern_is_rejected_with_hint(doc: Any, part: Any) -> None:
    _box(doc)
    sketch = sketch_on(doc, purpose="Hole", offset=20)
    profile(doc, sketch, "circle", diameter=2, center=[-20, 0])
    hole = features.pocket(sketch.Name, depth=2, document=doc.Name).to_dict()
    row = features.pattern(
        [hole["feature"]["name"]], "linear", length=20, count=3, document=doc.Name
    ).to_dict()

    with pytest.raises(CoreError, match="grid"):
        features.pattern(
            [row["feature"]["name"]], "linear", direction="Y", length=10, count=2, document=doc.Name
        )
