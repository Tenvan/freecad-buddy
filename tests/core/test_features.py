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


def _frustum(height: float, radius_bottom: float, radius_top: float) -> float:
    import math

    return math.pi * height / 3 * (radius_bottom**2 + radius_bottom * radius_top + radius_top**2)


def test_loft_makes_a_funnel_that_follows_its_parameters(doc: Any, part: Any) -> None:
    set_params(doc, Funnel_Bottom=40, Funnel_Top=12, Funnel_Height=30)
    bottom = sketch_on(doc, purpose="FunnelBottom")
    profile(doc, bottom, "circle", diameter="Funnel_Bottom")
    plane = features.datum_plane(offset="Funnel_Height", purpose="FunnelTop", document=doc.Name).to_dict()
    top = sketch_on(doc, plane=plane["plane"]["label"], purpose="FunnelTop")
    profile(doc, top, "circle", diameter="Funnel_Top")

    result = features.loft([bottom.Name, top.Name], purpose="Funnel", document=doc.Name).to_dict()

    assert result["created"][0]["label"] == "Loft_Funnel"
    assert abs(result["volume"] - _frustum(30, 20, 6)) < _frustum(30, 20, 6) * 0.01

    set_params(doc, Funnel_Height=50)  # the loft follows the datum plane's parameter
    doc.recompute()
    assert abs(part.Tip.Shape.Volume - _frustum(50, 20, 6)) < _frustum(50, 20, 6) * 0.01


def test_subtractive_loft_cuts_a_tapered_pocket(doc: Any, part: Any) -> None:
    _box(doc)  # 60 x 40 x 20
    bottom = sketch_on(doc, purpose="TaperBottom")
    profile(doc, bottom, "circle", diameter=20)
    plane = features.datum_plane(offset=20, purpose="TaperTop", document=doc.Name).to_dict()
    top = sketch_on(doc, plane=plane["plane"]["label"], purpose="TaperTop")
    profile(doc, top, "circle", diameter=10)

    result = features.loft(
        [bottom.Name, top.Name], subtractive=True, purpose="Taper", document=doc.Name
    ).to_dict()

    removed = _frustum(20, 10, 5)
    assert result["created"][0]["label"] == "LoftCut_Taper"
    assert abs(result["volume"] - (60 * 40 * 20 - removed)) < removed * 0.01


def test_loft_rejects_one_sketch_and_sketches_on_the_same_plane(doc: Any, part: Any) -> None:
    first = sketch_on(doc, purpose="A")
    profile(doc, first, "circle", diameter=10)
    second = sketch_on(doc, purpose="B")
    profile(doc, second, "circle", diameter=5)

    with pytest.raises(CoreError, match="at least two"):
        features.loft([first.Name], document=doc.Name)
    with pytest.raises(CoreError, match="same plane"):
        features.loft([first.Name, second.Name], document=doc.Name)
    assert part.Tip is None


def test_helix_makes_a_spring_whose_volume_follows_the_pitch(doc: Any, part: Any) -> None:
    import math

    set_params(doc, Spring_Pitch=4, Spring_Height=30, Wire_Diameter=2, Spring_Radius=10)
    wire = sketch_on(doc, plane="XZ", purpose="SpringWire")
    profile(doc, wire, "circle", diameter="Wire_Diameter", center=["Spring_Radius", 0])

    result = features.helix(
        wire.Name, pitch="Spring_Pitch", height="Spring_Height", purpose="Spring", document=doc.Name
    ).to_dict()

    def screw_volume(turns: float) -> float:  # area x centroid path (Pappus), independent of pitch
        return math.pi * 1**2 * 2 * math.pi * 10 * turns

    helix = doc.getObject(result["feature"]["name"])
    assert result["created"][0]["label"] == "Helix_Spring" and helix.Mode == "pitch-height-angle"
    assert result["volume"] == pytest.approx(screw_volume(30 / 4), rel=0.02)

    set_params(doc, Spring_Pitch=5)  # fewer turns on the same height
    doc.recompute()
    assert part.Tip.Shape.Volume == pytest.approx(screw_volume(30 / 5), rel=0.02)


def test_subtractive_helix_cuts_a_groove_by_turns(doc: Any, part: Any) -> None:
    pin = sketch_on(doc, purpose="Pin")
    profile(doc, pin, "circle", diameter=20)
    features.pad(pin.Name, length=30, purpose="Pin", document=doc.Name)
    before = part.Tip.Shape.Volume
    groove = sketch_on(doc, plane="XZ", purpose="Groove")
    profile(doc, groove, "rectangle", width=2, height=2, center=[10, 3])

    result = features.helix(
        groove.Name, pitch=5, turns=4, subtractive=True, purpose="Groove", document=doc.Name
    ).to_dict()

    assert result["created"][0]["label"] == "HelixCut_Groove"
    assert 0 < before - result["volume"] < before * 0.2
    assert doc.getObject(result["feature"]["name"]).Mode == "pitch-turns-angle"


def test_helix_rejects_bad_pitch_and_missing_length(doc: Any, part: Any) -> None:
    wire = sketch_on(doc, plane="XZ", purpose="Wire")
    profile(doc, wire, "circle", diameter=2, center=[10, 0])

    with pytest.raises(CoreError, match="either height or turns"):
        features.helix(wire.Name, pitch=4, document=doc.Name)
    with pytest.raises(CoreError, match="either height or turns"):
        features.helix(wire.Name, pitch=4, height=10, turns=2, document=doc.Name)
    with pytest.raises(CoreError, match="pitch must be positive"):
        features.helix(wire.Name, pitch=0, height=10, document=doc.Name)
    assert part.Tip is None


_PRIMITIVE_CASES = {
    "box": ({"length": 20, "width": 10, "height": 5}, 20 * 10 * 5),
    "cylinder": ({"diameter": 10, "height": 8}, 3.141592653589793 * 25 * 8),
    "sphere": ({"diameter": 10}, 4 / 3 * 3.141592653589793 * 125),
    "cone": ({"diameter": 10, "top_diameter": 4, "height": 9}, 3.141592653589793 * 3 * (25 + 10 + 4)),
    "ellipsoid": ({"length": 20, "width": 10, "height": 6}, 4 / 3 * 3.141592653589793 * 10 * 5 * 3),
    "torus": ({"diameter": 20, "tube_diameter": 4}, 2 * 3.141592653589793**2 * 10 * 4),
    "prism": ({"sides": 6, "diameter": 10, "height": 7}, 3 * 25 * 0.8660254037844386 * 7),
    "wedge": ({"length": 20, "width": 10, "height": 6, "top_length": 10, "top_width": 10}, 900.0),
}


@pytest.mark.parametrize(("kind", "dims", "expected"), [(k, *v) for k, v in _PRIMITIVE_CASES.items()])
def test_primitives_have_the_textbook_volume(
    doc: Any, part: Any, kind: str, dims: dict[str, Any], expected: float
) -> None:
    result = features.primitive(kind, dims, purpose="Test", document=doc.Name).to_dict()

    assert result["volume"] == pytest.approx(expected, rel=0.01)
    assert result["created"][0]["label"].endswith("_Test") and part.Tip.Shape.isValid()


def test_subtractive_primitive_cuts_and_follows_its_parameter(doc: Any, part: Any) -> None:
    import math

    _box(doc)  # 60 x 40 x 20, symmetric about the origin
    set_params(doc, Bore_Diameter=10)

    result = features.primitive(
        "cylinder", {"diameter": "Bore_Diameter", "height": 20}, subtractive=True, purpose="Bore",
        document=doc.Name,
    ).to_dict()  # fmt: skip

    assert result["created"][0]["label"] == "CylinderCut_Bore"
    assert result["volume"] == pytest.approx(48000 - math.pi * 25 * 20, rel=0.01)
    set_params(doc, Bore_Diameter=20)
    doc.recompute()
    assert part.Tip.Shape.Volume == pytest.approx(48000 - math.pi * 100 * 20, rel=0.01)


def test_primitive_center_and_datum_plane_offset_are_parametric(doc: Any, part: Any) -> None:
    set_params(doc, Knob_Diameter=12, Knob_Height=25)
    plane = features.datum_plane(offset="Knob_Height", purpose="KnobTop", document=doc.Name).to_dict()

    result = features.primitive(
        "sphere", {"diameter": "Knob_Diameter"}, plane=plane["plane"]["label"], center=[5, -3],
        purpose="Knob", document=doc.Name,
    ).to_dict()  # fmt: skip

    sphere = doc.getObject(result["feature"]["name"])
    centre = sphere.Shape.Solids[0].CenterOfMass
    assert (centre.x, centre.y, centre.z) == pytest.approx((5, -3, 25), abs=1e-3)
    set_params(doc, Knob_Height=40)
    doc.recompute()
    assert sphere.Shape.Solids[0].CenterOfMass.z == pytest.approx(40, abs=1e-3)


def test_primitive_rejects_unknown_kind_missing_dims_and_empty_cut(doc: Any, part: Any) -> None:
    with pytest.raises(CoreError, match="kind must be"):
        features.primitive("pyramid", {}, document=doc.Name)
    with pytest.raises(CoreError, match="missing"):
        features.primitive("box", {"length": 1}, document=doc.Name)
    _box(doc)
    with pytest.raises(CoreError, match="removes no material"):
        features.primitive("sphere", {"diameter": 5}, offset=100, subtractive=True, document=doc.Name)
    assert part.Tip.Label == "Pad_Base"


def test_datum_point_line_and_lcs_follow_their_parameters(doc: Any, part: Any) -> None:
    import math

    import FreeCAD

    set_params(doc, Axis_X=20, Lcs_Height=30)
    point = features.datum("point", offset=[5, 7, 9], purpose="Anchor", document=doc.Name).to_dict()
    line = features.datum("line", offset=["Axis_X", 0, 0], purpose="HingeAxis", document=doc.Name).to_dict()
    lcs = features.datum(
        "lcs", offset=[0, 0, "Lcs_Height"], angle=45, purpose="Tilted", document=doc.Name
    ).to_dict()

    labels = [d["datum"]["label"] for d in (point, line, lcs)]
    assert labels == ["DatumPoint_Anchor", "DatumLine_HingeAxis", "LCS_Tilted"]
    pt, ln, cs = (doc.getObject(d["datum"]["name"]) for d in (point, line, lcs))
    assert (pt.Placement.Base.x, pt.Placement.Base.y, pt.Placement.Base.z) == pytest.approx((5, 7, 9))
    assert (ln.Placement.Base.x, ln.Placement.Base.y, ln.Placement.Base.z) == pytest.approx((20, 0, 0))
    direction = ln.Placement.Rotation.multVec(FreeCAD.Vector(0, 0, 1))
    assert (direction.x, direction.y, direction.z) == pytest.approx((0, 0, 1))
    assert cs.Placement.Base.z == pytest.approx(30)
    assert cs.Placement.Rotation.Angle == pytest.approx(math.radians(45))

    set_params(doc, Axis_X=25, Lcs_Height=40)  # datums follow their parameters
    doc.recompute()
    assert ln.Placement.Base.x == pytest.approx(25) and cs.Placement.Base.z == pytest.approx(40)


def test_sketch_on_lcs_and_axes_through_a_datum_line(doc: Any, part: Any) -> None:
    import math

    lcs = features.datum("lcs", offset=[0, 0, 30], purpose="Top", document=doc.Name).to_dict()
    on_lcs = sketch_on(doc, plane=lcs["datum"]["label"], purpose="OnLcs")
    assert on_lcs.MapMode == "ObjectXY" and on_lcs.Placement.Base.z == pytest.approx(30)

    line = features.datum("line", offset=[10, 0, 0], purpose="RingAxis", document=doc.Name).to_dict()
    axis = line["datum"]["label"]
    ring = sketch_on(doc, plane="XZ", purpose="Ring")
    profile(doc, ring, "circle", diameter=6, center=[20, 10])  # 10 mm beside the line, r = 3
    torus = 2 * math.pi**2 * 10 * 3**2
    result = features.revolve(ring.Name, axis=axis, purpose="Ring", document=doc.Name).to_dict()
    assert result["volume"] == pytest.approx(torus, rel=0.01)

    wire = sketch_on(doc, plane="XZ", purpose="Wire")
    profile(doc, wire, "circle", diameter=2, center=[18, 12])  # coil of radius 8 fused into the ring
    coil = features.helix(wire.Name, pitch=4, turns=2, axis=axis, purpose="Coil", document=doc.Name).to_dict()
    assert torus < coil["volume"] < torus + math.pi * 2 * math.pi * 8 * 2

    pattern = features.pattern([coil["feature"]["name"]], "polar", axis=axis, count=2, document=doc.Name)
    assert doc.getObject(pattern.to_dict()["feature"]["name"]).isValid()
    with pytest.raises(CoreError, match="datum line"):
        features.revolve(ring.Name, axis="Sketch_Ring", document=doc.Name)


def _taper_volume(side: float, height: float, degrees: float) -> float:
    import math

    growth = 2 * math.tan(math.radians(degrees))  # the square's side grows by this per mm of height
    return ((side + growth * height) ** 3 - side**3) / (3 * growth)


def test_pad_taper_and_up_to_first(doc: Any, part: Any) -> None:
    import math

    base = sketch_on(doc)
    profile(doc, base, "rectangle", width=20, height=20)
    result = features.pad(base.Name, length=10, taper=10, purpose="Base", document=doc.Name).to_dict()
    assert result["volume"] == pytest.approx(_taper_volume(20, 10, 10), rel=0.01)

    plane = features.datum_plane(offset=30, purpose="Above", document=doc.Name).to_dict()
    boss = sketch_on(doc, plane=plane["plane"]["label"], purpose="Boss")
    profile(doc, boss, "circle", diameter=10)
    result = features.pad(
        boss.Name, mode="up_to_first", reversed=True, purpose="Boss", document=doc.Name
    ).to_dict()  # down from z = 30 until it meets the pad top at z = 10
    assert result["volume"] == pytest.approx(_taper_volume(20, 10, 10) + math.pi * 25 * 20, rel=0.01)


def test_pocket_up_to_first_and_taper(doc: Any, part: Any) -> None:
    import math

    _box(doc)  # 60 x 40 x 20
    slot = sketch_on(doc, purpose="Slot")
    profile(doc, slot, "rectangle", width=4, height=4)
    result = features.pocket(slot.Name, mode="up_to_first", purpose="Slot", document=doc.Name).to_dict()
    assert result["volume"] == pytest.approx(48000 - 4 * 4 * 20, rel=0.01)
    assert doc.getObject(result["feature"]["name"]).Type == "UpToFirst"

    dimple = sketch_on(doc, purpose="Dimple", offset=20)
    profile(doc, dimple, "circle", diameter=10, center=[20, 10])
    before = part.Tip.Shape.Volume
    result = features.pocket(dimple.Name, depth=5, taper=10, purpose="Dimple", document=doc.Name).to_dict()
    feature = doc.getObject(result["feature"]["name"])
    assert feature.TaperAngle.Value == pytest.approx(10)
    assert 0 < before - result["volume"] < math.pi * 25 * 5 * 1.5


def test_hole_model_thread_cuts_real_thread_geometry(doc: Any, part: Any) -> None:
    _box(doc)
    tapped = sketch_on(doc, purpose="Tapped", offset=20)
    profile(doc, tapped, "circle", diameter=5)
    cosmetic = features.hole(tapped.Name, size="M6", threaded=True, document=doc.Name).to_dict()
    documents.undo(document=doc.Name)

    modelled = features.hole(
        tapped.Name, size="M6", threaded=True, model_thread=True, purpose="Tapped", document=doc.Name
    ).to_dict()

    assert modelled["volume"] < cosmetic["volume"] and part.Tip.Shape.isValid()
    assert modelled["created"][0]["label"] == "Hole_Tapped" and len(part.Tip.Shape.Faces) > 20
    with pytest.raises(CoreError, match="threaded=true"):
        features.hole(tapped.Name, size="M6", model_thread=True, document=doc.Name)
