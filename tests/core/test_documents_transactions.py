from typing import Any

import pytest

from buddy_core import body, documents, naming
from buddy_core import parameters as params
from buddy_core.errors import BUSY_USER_TRANSACTION, RECOMPUTE_FAILED, VALIDATION, CoreError
from buddy_core.transaction import transaction

from .conftest import set_params, sketch_on


def test_each_tool_call_is_one_named_undo_step(doc: Any) -> None:
    before = doc.UndoCount

    body.create_body("Box", document=doc.Name)
    set_params(doc, Box_Width=60)

    assert doc.UndoCount == before + 2
    assert doc.UndoNames[0].startswith("Set parameters")
    assert doc.UndoNames[1] == "Create body: Box"


def test_failing_block_rolls_back_everything(doc: Any) -> None:
    objects_before, undo_before = len(doc.Objects), doc.UndoCount

    with pytest.raises(RuntimeError), transaction(doc, "kaputt"):
        doc.addObject("PartDesign::Body", "Body")
        raise RuntimeError("boom")

    assert len(doc.Objects) == objects_before
    assert doc.UndoCount == undo_before


def test_recompute_failure_is_reported_and_rolled_back(doc: Any, part: Any) -> None:
    sketch = sketch_on(doc)  # empty sketch -> pad cannot work
    objects_before = len(doc.Objects)

    with pytest.raises(CoreError) as info, transaction(doc, "Pad ohne Profil"):
        pad = part.newObject("PartDesign::Pad", "Pad")
        pad.Profile = sketch

    assert info.value.name == RECOMPUTE_FAILED
    assert info.value.data["state"] == "rolled_back"
    assert len(doc.Objects) == objects_before


def test_open_user_transaction_blocks_without_changes(doc: Any) -> None:
    doc.openTransaction("Nutzer arbeitet")  # FreeCAD opens transactions lazily ...
    doc.addObject("App::FeaturePython", "UserChange")  # ... the first change makes it pending
    try:
        with pytest.raises(CoreError) as info:
            body.create_body("Box", document=doc.Name)
    finally:
        doc.abortTransaction()

    assert info.value.name == BUSY_USER_TRANSACTION
    assert not [o for o in doc.Objects if o.TypeId == "PartDesign::Body"]
    assert not doc.getObject("UserChange")  # the user's own transaction was untouched until abort


def test_parameters_are_typed_and_listed(doc: Any) -> None:
    params.set_parameters(
        doc,
        {
            "Box_Width": 60,
            "Wall": {"value": 2, "description": "Wand"},
            "Ribs": {"value": 4, "type": "integer"},
        },
    )

    listed = {p["name"]: p for p in params.list_parameters(doc)}
    assert listed["Box_Width"]["type"] == "length" and listed["Box_Width"]["value"] == 60
    assert listed["Wall"]["description"] == "Wand"
    assert listed["Ribs"]["type"] == "integer" and listed["Ribs"]["value"] == 4
    assert listed["Box_Width"]["expression"] == "<<Parameters>>.Box_Width"


@pytest.mark.parametrize("bad", [{"1abc": 1}, {"ok": "text"}, {"x": {"value": 1, "type": "weird"}}])
def test_invalid_parameters_are_rejected(doc: Any, bad: dict[str, Any]) -> None:
    with pytest.raises(CoreError) as info:
        params.set_parameters(doc, bad)

    assert info.value.name == VALIDATION


def test_parameter_type_cannot_change(doc: Any) -> None:
    set_params(doc, Holes=3)
    with pytest.raises(CoreError):
        params.set_parameters(doc, {"Holes": {"value": 3, "type": "integer"}})


def test_model_tree_and_label_lint(doc: Any, part: Any) -> None:
    sketch_on(doc)
    raw = part.newObject("Sketcher::SketchObject", "Sketch")
    raw.Label = "Sketch001"

    tree = documents.model_tree(doc.Name)

    body_node = next(n for n in tree["objects"] if n["label"] == "Part")
    assert [f["label"] for f in body_node["features"]] == ["Sketch_Base", "Sketch001"]
    assert [issue["label"] for issue in tree["label_issues"]] == ["Sketch001"]
    # origin axes, planes and (since 26.3) the origin point never appear as top-level objects
    origin_features = {f.Name for f in part.Origin.OriginFeatures}
    assert not origin_features & {n["name"] for n in tree["objects"]}
    assert all(n["type"] in ("PartDesign::Body", "App::VarSet") for n in tree["objects"])


def test_undo_and_delete(doc: Any, part: Any) -> None:
    sketch = sketch_on(doc)
    documents.delete_object(sketch.Label, doc.Name)
    assert not doc.getObjectsByLabel("Sketch_Base")

    documents.undo(doc.Name)
    assert doc.getObjectsByLabel("Sketch_Base")


def test_resolve_object_by_label_and_not_found(doc: Any, part: Any) -> None:
    assert documents.resolve_object(doc, "Part") is part
    with pytest.raises(CoreError) as info:
        documents.resolve_object(doc, "Nope")
    assert info.value.name == "not_found"


def test_sanitize_and_unique_labels(doc: Any) -> None:
    assert naming.sanitize("Größe der Box") == "GroesseDerBox"
    assert naming.make_label(doc, "Pad", "base plate") == "Pad_BasePlate"
