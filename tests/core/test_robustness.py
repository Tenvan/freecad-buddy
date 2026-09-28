"""AC-05/AC-07: parameter changes keep the model valid and dress-ups on the intended edges."""

from typing import Any

from buddy_core import documents, features, naming, select

from .conftest import profile, set_params, sketch_on


def _box_with_pocket(doc: Any) -> tuple[Any, Any]:
    set_params(doc, Box_Width=60, Box_Depth=40, Box_Height=20, Pocket_X=-10, Fillet_Radius=2)
    base = sketch_on(doc)
    profile(doc, base, "rectangle", width="Box_Width", height="Box_Depth")
    features.pad(base.Name, length="Box_Height", purpose="Base", document=doc.Name)
    cut = sketch_on(doc, purpose="Cut", offset="Box_Height")
    profile(doc, cut, "rectangle", width=10, height=10, center=["Pocket_X", 0])
    features.pocket(cut.Name, depth=5, purpose="Cut", document=doc.Name)
    fillet = features.fillet("edges:vertical", radius="Fillet_Radius", document=doc.Name).to_dict()
    return doc.getObject(fillet["feature"]["name"]), cut


def test_parameter_variants_recompute_cleanly(doc: Any, part: Any) -> None:
    fillet, _ = _box_with_pocket(doc)

    for width, height in ((80, 20), (50, 30), (60, 12)):
        set_params(doc, Box_Width=width, Box_Height=height)
        doc.recompute()
        assert fillet.isValid(), fillet.getStatusString()
        assert fillet.Shape.isValid()
        assert abs(fillet.Shape.BoundBox.XLength - width) < 1e-6
        assert abs(fillet.Shape.BoundBox.ZLength - height) < 1e-6


def test_fillet_stays_on_intended_edges_after_topology_shift(doc: Any, part: Any) -> None:
    fillet, _ = _box_with_pocket(doc)
    base_shape = fillet.Base[0].Shape
    expected = select.resolve(base_shape, "edges:vertical", single=False)

    set_params(doc, Pocket_X=15, Box_Width=90)
    doc.recompute()

    now = select.resolve(fillet.Base[0].Shape, "edges:vertical", single=False)
    assert sorted(fillet.Base[1]) == sorted(now)
    assert len(now) == len(expected)
    for name in fillet.Base[1]:
        edge = fillet.Base[0].Shape.getElement(name)
        assert abs(edge.BoundBox.ZMax - fillet.Base[0].Shape.BoundBox.ZMax) < 1e-6


def test_model_tree_has_readable_labels(doc: Any, part: Any) -> None:
    _box_with_pocket(doc)

    tree = documents.model_tree(doc.Name)

    assert tree["label_issues"] == []
    body_node = next(node for node in tree["objects"] if node["type"] == "PartDesign::Body")
    labels = [feature["label"] for feature in body_node["features"]]
    assert labels == ["Sketch_Base", "Pad_Base", "Sketch_Cut", "Pocket_Cut", "Fillet_Vertical"]
    assert all(not naming.is_default_label(label) for label in labels)
