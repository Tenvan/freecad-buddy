"""External geometry (``x<N>``): layout sketches drive dependent sketches in the same body."""

from typing import Any

import pytest

from buddy_core import body, features
from buddy_core.errors import VALIDATION, CoreError
from buddy_core.sketch import assist, lowlevel, model

from .conftest import profile, set_params, sketch_on


def geometry(doc: Any, sketch: Any, *items: dict[str, Any]) -> dict[str, Any]:
    return lowlevel.add_geometry(sketch.Name, list(items), doc.Name).to_dict()


def constraints(doc: Any, sketch: Any, *items: dict[str, Any]) -> dict[str, Any]:
    return lowlevel.add_constraints(sketch.Name, list(items), doc.Name).to_dict()


def external(source: Any, element: str, **extra: Any) -> dict[str, Any]:
    return {"type": "external", "source": source.Label, "element": element, **extra}


def layout(doc: Any) -> Any:
    """Construction line of length Mount_Diag, symmetric to the origin, hole circles at its ends."""
    set_params(doc, Mount_Diag=70, Hole_D=3.4)
    sketch = sketch_on(doc, purpose="Layout")
    geometry(
        doc,
        sketch,
        {"type": "line", "start": [-35, 0], "end": [35, 0], "construction": True},
        {"type": "circle", "center": [35, 0], "radius": 1.7},
        {"type": "circle", "center": [-35, 0], "radius": 1.7},
    )
    report = constraints(
        doc,
        sketch,
        {"type": "symmetric", "a": "g0.start", "b": "g0.end", "about": "origin"},
        {"type": "horizontal", "a": "g0"},
        {"type": "distance", "a": "g0", "value": "Mount_Diag", "name": "Mount_Diag"},
        {"type": "coincident", "a": "g1.center", "b": "g0.end"},
        {"type": "coincident", "a": "g2.center", "b": "g0.start"},
        {"type": "diameter", "a": "g1", "value": "Hole_D", "name": "Hole_D"},
        {"type": "equal", "a": "g1", "b": "g2"},
    )
    assert report["sketch"]["dof"] == 0, report["sketch"]
    return sketch


def undo_names(doc: Any) -> list[str]:
    return list(doc.UndoNames)


def test_external_circle_center_drives_dependent_sketch(doc: Any, part: Any) -> None:
    source = layout(doc)
    target = sketch_on(doc, purpose="ScrewHead")

    added = geometry(doc, target, external(source, "g1"))
    assert added["geometry"] == ["x0"]

    geometry(doc, target, {"type": "circle", "center": [30, 2], "radius": 3})
    report = constraints(
        doc,
        target,
        {"type": "coincident", "a": "g0.center", "b": "x0.center"},
        {"type": "diameter", "a": "g0", "value": 6.5, "name": "Head_D"},
    )["sketch"]
    assert report["dof"] == 0
    assert report["external"] == [
        {"ref": "x0", "source": "Sketch_Layout", "element": "g1", "defining": False}
    ]
    assert target.Geometry[0].Location.distanceToPoint(source.Geometry[1].Location) < 1e-6

    set_params(doc, Mount_Diag=80)
    doc.recompute()
    assert source.isValid() and target.isValid()
    assert abs(target.Geometry[0].Location.x - 40) < 1e-6


def test_position_suffix_and_defining_edges_build_a_profile(doc: Any, part: Any) -> None:
    outline = sketch_on(doc, purpose="Outline")
    profile(doc, outline, "rectangle", width=40, height=20)
    target = sketch_on(doc, purpose="Copy")

    corner = geometry(doc, target, external(outline, "g0.start"))
    assert corner["geometry"] == ["x0.start"]
    edges = geometry(doc, target, *(external(outline, f"g{i}", defining=True) for i in range(1, 4)))
    assert edges["geometry"] == ["x1", "x2", "x3"]
    report = model.analyze_sketch(target.Name, doc.Name)
    assert [e["defining"] for e in report["external"]] == [False, True, True, True]
    assert report["closed_wires"] == 0  # three defining edges do not close the profile


def test_defining_outline_is_padded(doc: Any, part: Any) -> None:
    outline = sketch_on(doc, purpose="Outline")
    profile(doc, outline, "rectangle", width=40, height=20)
    target = sketch_on(doc, purpose="Copy")
    geometry(doc, target, *(external(outline, f"g{i}", defining=True) for i in range(4)))

    result = features.pad(target.Name, length=5, document=doc.Name).to_dict()

    assert abs(result["volume"] - 40 * 20 * 5) < 1e-6


def test_construction_geometry_cannot_be_referenced(doc: Any, part: Any) -> None:
    source = layout(doc)
    target = sketch_on(doc, purpose="Target")
    before = undo_names(doc)

    with pytest.raises(CoreError) as info:
        geometry(doc, target, external(source, "g0"))

    assert info.value.name == VALIDATION
    assert "construction geometry" in info.value.message
    assert target.ExternalGeometry == [] and undo_names(doc) == before


@pytest.mark.parametrize(
    ("case", "fragment"),
    [
        ("self", "cannot reference itself"),
        ("later", "dependency cycle"),
        ("unknown_source", "not found"),
        ("unknown_element", "does not exist"),
        ("other_body", "shape_binder"),
        ("solid", "topological naming"),
        ("face", "Faces cannot be external"),
    ],
)
def test_invalid_external_references_change_nothing(doc: Any, part: Any, case: str, fragment: str) -> None:
    source = layout(doc)
    target = sketch_on(doc, purpose="Target")
    pad_sketch = sketch_on(doc, purpose="Block")
    profile(doc, pad_sketch, "rectangle", width=90, height=20)
    features.pad(pad_sketch.Name, length=5, document=doc.Name)
    pad = doc.getObjectsByLabel("Pad_Block")[0]
    later = sketch_on(doc, purpose="Later")
    profile(doc, later, "circle", diameter=4)
    body.create_body("Other", document=doc.Name)
    foreign = sketch_on(doc, purpose="Foreign", body="Other")
    profile(doc, foreign, "circle", diameter=4)
    items = {
        "self": external(target, "g0"),
        "later": external(later, "g0"),
        "unknown_source": {"type": "external", "source": "Nope", "element": "g0"},
        "unknown_element": external(source, "g42"),
        "other_body": external(foreign, "g0"),
        "solid": external(pad, "Edge1"),
        "face": external(pad, "Face1", allow_face_reference=True),
    }
    # 'Target' comes before 'Later' (cycle case); solid sources need a sketch after the pad
    subject = sketch_on(doc, purpose="AfterPad", body="Part") if case in ("solid", "face") else target
    before = undo_names(doc)

    with pytest.raises(CoreError) as info:
        geometry(doc, subject, items[case])

    assert info.value.name == VALIDATION
    assert fragment in info.value.message
    assert subject.ExternalGeometry == [] and undo_names(doc) == before


def test_solid_reference_is_opt_in_and_warned(doc: Any, part: Any) -> None:
    block = sketch_on(doc, purpose="Block")
    profile(doc, block, "rectangle", width=40, height=20)
    features.pad(block.Name, length=5, document=doc.Name)
    pad = doc.getObjectsByLabel("Pad_Block")[0]
    target = sketch_on(doc, purpose="OnTop", offset=5)

    result = geometry(doc, target, external(pad, "edges:top", allow_face_reference=True))

    assert result["geometry"] == ["x0", "x1", "x2", "x3"]
    assert any("jump" in w for w in result["warnings"])
    lint = model.analyze_sketch(target.Name, doc.Name)["lint"]
    assert {i["severity"] for i in lint if "ref" in i} == {"warning"}


def test_sketch_sources_lint_as_info_and_duplicates_are_reused(doc: Any, part: Any) -> None:
    source = layout(doc)
    target = sketch_on(doc, purpose="Target")

    first = geometry(doc, target, external(source, "g1"))
    again = geometry(doc, target, external(source, "g1.center"))

    assert first["geometry"] == ["x0"] and again["geometry"] == ["x0.center"]
    lint = model.analyze_sketch(target.Name, doc.Name)["lint"]
    assert [i["severity"] for i in lint if i.get("ref") == "x0"] == ["info"]


def test_unknown_external_ref_in_constraint_is_rejected(doc: Any, part: Any) -> None:
    source = layout(doc)
    target = sketch_on(doc, purpose="Target")
    geometry(doc, target, external(source, "g1"), {"type": "circle", "center": [0, 0], "radius": 1})
    count = target.ConstraintCount

    with pytest.raises(CoreError) as info:
        constraints(doc, target, {"type": "coincident", "a": "g0.center", "b": "x3.center"})

    assert info.value.name == VALIDATION and "x3" in info.value.message
    assert target.ConstraintCount == count


def test_fully_constrain_keeps_external_references(doc: Any, part: Any) -> None:
    source = layout(doc)
    target = sketch_on(doc, purpose="Target")
    geometry(doc, target, external(source, "g1"), {"type": "line", "start": [35, 0], "end": [50, 10]})
    constraints(doc, target, {"type": "coincident", "a": "g0.start", "b": "x0.center"})

    applied = assist.fully_constrain_sketch(target.Name, apply=True, document=doc.Name).to_dict()

    assert applied["sketch"]["dof"] == 0
    assert applied["sketch"]["external"][0]["ref"] == "x0"


def test_deleted_source_is_reported(doc: Any, part: Any) -> None:
    source = layout(doc)
    target = sketch_on(doc, purpose="Target")
    geometry(doc, target, external(source, "g1"), {"type": "circle", "center": [30, 0], "radius": 1})
    constraints(doc, target, {"type": "coincident", "a": "g0.center", "b": "x0.center"})

    doc.removeObject(source.Name)
    doc.recompute()

    lint = model.analyze_sketch(target.Name, doc.Name)["lint"]
    assert any(i["severity"] == "error" and i.get("ref") == "x0" for i in lint)
