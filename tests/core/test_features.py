from typing import Any

import pytest

from buddy_core import documents, features, select
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

    assert any("reversed automatically" in w for w in result["warnings"])
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


def test_consecutive_patterns_advance_the_tip_and_keep_every_copy(doc: Any, part: Any) -> None:
    _box(doc, width=100, depth=40, height=10)
    sketch = sketch_on(doc, purpose="Peg", offset=10)
    profile(doc, sketch, "circle", diameter=6, center=[-40, -10])
    peg = features.pad(sketch.Name, length=5, purpose="Peg", document=doc.Name).to_dict()
    peg_volume = 3.14159265 * 9 * 5
    base = 100 * 40 * 10 + peg_volume

    first = features.pattern([peg["feature"]["name"]], "mirrored", plane="YZ", document=doc.Name).to_dict()
    second = features.pattern([peg["feature"]["name"]], "mirrored", plane="XZ", document=doc.Name).to_dict()
    third = features.pattern(
        [peg["feature"]["name"]], "polar", axis="Z", angle=360, count=2, document=doc.Name
    )

    names = [first["feature"]["name"], second["feature"]["name"], third.to_dict()["feature"]["name"]]
    assert part.Tip.Name == names[-1]
    order = [o.Name for o in part.Group]
    assert order.index(names[0]) < order.index(names[1]) < order.index(names[2])
    assert first["volume"] == pytest.approx(base + peg_volume, abs=1e-2)
    assert second["volume"] == pytest.approx(base + 2 * peg_volume, abs=1e-2)
    assert third.to_dict()["volume"] == pytest.approx(base + 3 * peg_volume, abs=1e-2)
    assert doc.getObject(names[-1]).Visibility and not doc.getObject(names[0]).Visibility


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


def test_grid_pattern_shows_only_the_multitransform_and_nests_its_steps(doc: Any, part: Any) -> None:
    _box(doc, width=60, depth=40, height=5)
    sketch = sketch_on(doc, purpose="Hole", offset=5)
    profile(doc, sketch, "circle", diameter=2, center=[-20, -10])
    hole = features.pocket(sketch.Name, mode="through_all", purpose="Hole", document=doc.Name).to_dict()
    pocket = doc.getObject(hole["feature"]["name"])

    grid = features.pattern(
        [pocket.Name], "grid", length=40, count=3, length2=20, count2=2, purpose="Cells", document=doc.Name
    ).to_dict()

    feature = doc.getObject(grid["feature"]["name"])
    steps = list(feature.Transformations)
    assert part.Tip is feature and feature.Visibility
    assert not pocket.Visibility
    assert len(steps) == 2 and not any(step.Visibility for step in steps)
    assert all(step in part.Group for step in steps)  # in the body like FreeCAD's own command

    tree = documents.model_tree(doc.Name)
    assert [o["name"] for o in tree["objects"]] == [part.Name]
    body_node = tree["objects"][0]
    assert not {step.Name for step in steps} & {f["name"] for f in body_node["features"]}
    grid_node = next(f for f in body_node["features"] if f["name"] == feature.Name)
    assert [s["name"] for s in grid_node["transformations"]] == [step.Name for step in steps]

    step_names = [step.Name for step in steps]
    documents.delete_object(feature.Name, document=doc.Name)
    assert not any(doc.getObject(name) for name in step_names)


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


def test_u_path_is_fully_constrained_and_sweep_makes_a_round_handle(doc: Any, part: Any) -> None:
    import math

    set_params(doc, Handle_Length=100, Handle_Height=40, Handle_Radius=10, Handle_Diameter=10)
    path = sketch_on(doc, plane="XZ", purpose="HandlePath")
    analysis = profile(
        doc, path, "u_path", length="Handle_Length", height="Handle_Height", radius="Handle_Radius"
    )
    assert analysis["sketch"]["dof"] == 0 and analysis["sketch"]["open_wires"] == 1

    section = sketch_on(doc, purpose="HandleSection")
    profile(doc, section, "circle", diameter="Handle_Diameter", center=["-Handle_Length / 2", 0])
    result = features.sweep(section.Name, path.Name, purpose="Handle", document=doc.Name).to_dict()

    centre_line = 2 * 40 + 100 - 4 * 10 + math.pi * 10
    assert result["created"][0]["label"] == "Sweep_Handle"
    assert abs(result["volume"] - math.pi * 5**2 * centre_line) < 1.0

    set_params(doc, Handle_Length=80)  # the handle follows its parameters
    doc.recompute()
    assert abs(part.Tip.Shape.Volume - math.pi * 25 * (centre_line - 20)) < 1.0


def test_sweep_rejects_empty_path_and_bad_radius(doc: Any, part: Any) -> None:
    from buddy_core.errors import CoreError as Error

    path = sketch_on(doc, plane="XZ", purpose="Empty")
    section = sketch_on(doc, purpose="Section")
    profile(doc, section, "circle", diameter=5)
    with pytest.raises(Error):
        features.sweep(section.Name, path.Name, document=doc.Name)
    with pytest.raises(Error):
        profile(doc, path, "u_path", length=20, height=5, radius=10)
