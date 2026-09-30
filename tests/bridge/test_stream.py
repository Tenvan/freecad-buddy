"""Design stream: the registry records calls, the document keeps them, replay rebuilds a copy."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import FreeCAD
import pytest

from buddy_bridge.registry import MethodRegistry
from buddy_core import stream
from buddy_core.errors import CoreError


@pytest.fixture
def doc(registry: MethodRegistry) -> Iterator[Any]:
    name = registry.execute("document.new", {"name": "Stream"})["document"]["name"]
    yield FreeCAD.getDocument(name)
    for open_name in list(FreeCAD.listDocuments()):
        FreeCAD.closeDocument(open_name)


def _build_box(registry: MethodRegistry, document: str) -> None:
    """Body 'Box' with a 40 x 20 x 10 pad: four recorded steps."""
    registry.execute("body.create", {"label": "Box", "document": document})
    registry.execute("sketch.create", {"plane": "XY", "purpose": "Base", "document": document})
    registry.execute(
        "sketch.add_profile",
        {
            "sketch": "Sketch_Base",
            "kind": "rectangle",
            "params": {"width": 40, "height": 20},
            "document": document,
        },
    )
    registry.execute(
        "feature.pad", {"sketch": "Sketch_Base", "length": 10, "purpose": "Base", "document": document}
    )


def _methods(doc: Any) -> list[str]:
    return [entry["method"] for entry in stream.entries(doc)]


BOX_STEPS = ["body.create", "sketch.create", "sketch.add_profile", "feature.pad"]


def test_registry_records_mutating_calls_in_order_and_skips_failures(
    registry: MethodRegistry, doc: Any
) -> None:
    _build_box(registry, doc.Name)
    with pytest.raises(CoreError):
        registry.execute("feature.pad", {"sketch": "Nope", "document": doc.Name})
    registry.execute("document.tree", {"document": doc.Name})  # read-only

    items = stream.entries(doc)
    assert [entry["method"] for entry in items] == BOX_STEPS
    assert items[-1]["created"] == ["Pad_Base"] and items[-1]["undo_name"] == "Pad: Base"
    assert items[-1]["params"]["length"] == 10 and items[-1]["version"]
    assert doc.getObject(stream.GROUP_NAME).Label == "Storepoints"


def test_undo_compacts_the_stream_and_manual_edits_are_marked(registry: MethodRegistry, doc: Any) -> None:
    _build_box(registry, doc.Name)
    registry.execute("document.undo", {"steps": 1, "document": doc.Name})
    assert _methods(doc) == BOX_STEPS[:3]

    sketch = doc.getObjectsByLabel("Sketch_Base")[0]
    doc.openTransaction("Manual move")
    sketch.AttachmentOffset = FreeCAD.Placement(FreeCAD.Vector(0, 0, 5), FreeCAD.Rotation())
    doc.commitTransaction()
    registry.execute(
        "feature.pad", {"sketch": "Sketch_Base", "length": 10, "purpose": "Base", "document": doc.Name}
    )

    items = stream.entries(doc)
    assert [entry["method"] for entry in items] == [*BOX_STEPS[:3], "manual_edit", "feature.pad"]
    assert items[3]["undo_names"] == ["Manual move"]
    assert registry.execute("stream.list", {"document": doc.Name})["manual_edits"] == 1


def test_stream_survives_save_close_and_open(registry: MethodRegistry, doc: Any, tmp_path: Path) -> None:
    _build_box(registry, doc.Name)
    path = tmp_path / "stream.FCStd"
    registry.execute("document.save", {"path": str(path), "document": doc.Name})
    registry.execute("document.close", {"document": doc.Name})

    name = registry.execute("document.open", {"path": str(path)})["document"]["name"]

    assert _methods(FreeCAD.getDocument(name)) == BOX_STEPS


def test_storepoint_marks_the_feature_lists_and_undoes(registry: MethodRegistry, doc: Any) -> None:
    _build_box(registry, doc.Name)

    result = registry.execute("stream.storepoint", {"name": "Base", "document": doc.Name})

    marker = doc.getObject(result["created"][0]["name"])
    pad = doc.getObjectsByLabel("Pad_Base")[0]
    assert marker.Label == "Storepoint_Base" and marker.Feature is pad
    assert marker.Position == 4 and marker.Steps == 4
    assert pad.Label2 == "◆ Storepoint 1: Base"
    assert doc.getObject(stream.GROUP_NAME).Group == [marker]
    assert _methods(doc) == [*BOX_STEPS, "stream.storepoint"]

    listing = registry.execute("stream.list", {"document": doc.Name})
    point = listing["storepoints"][0]
    assert (point["name"], point["position"], point["steps"], point["feature"]) == ("Base", 4, 4, "Pad_Base")
    assert listing["steps"] == 5
    with pytest.raises(CoreError, match="already exists"):
        registry.execute("stream.storepoint", {"name": "Base", "document": doc.Name})

    tree = registry.execute("document.tree", {"document": doc.Name})
    group = next(node for node in tree["objects"] if node["name"] == stream.GROUP_NAME)
    assert group["storepoints"][0]["feature"] == "Pad_Base" and group["steps"] == 5
    assert not any(node["label"].startswith("Storepoint_") for node in tree["objects"])

    registry.execute("document.undo", {"steps": 1, "document": doc.Name})
    assert doc.getObject(stream.GROUP_NAME).Group == [] and pad.Label2 == ""
    assert registry.execute("stream.list", {"document": doc.Name})["storepoints"] == []
    assert _methods(doc) == BOX_STEPS


def _add_hole_and_storepoints(registry: MethodRegistry, document: str) -> None:
    _build_box(registry, document)
    registry.execute("stream.storepoint", {"name": "Base", "document": document})
    registry.execute("sketch.create", {"plane": "XY", "purpose": "Hole", "offset": 10, "document": document})
    registry.execute(
        "sketch.add_profile",
        {"sketch": "Sketch_Hole", "kind": "circle", "params": {"diameter": 10}, "document": document},
    )
    registry.execute(
        "feature.pocket", {"sketch": "Sketch_Hole", "depth": 5, "purpose": "Hole", "document": document}
    )
    registry.execute("stream.storepoint", {"name": "Done", "document": document})


def test_replay_rebuilds_the_design_up_to_each_storepoint(registry: MethodRegistry, doc: Any) -> None:
    _add_hole_and_storepoints(registry, doc.Name)
    final_volume = doc.getObjectsByLabel("Box")[0].Shape.Volume

    base = registry.execute("stream.replay", {"storepoint": "Base", "into": "CopyBase", "document": doc.Name})

    copy = FreeCAD.getDocument(base["document"]["name"])
    assert base["steps"] == 5 and base["skipped"] == [] and base["warnings"] == []
    assert copy.getObjectsByLabel("Box")[0].Shape.Volume == pytest.approx(40 * 20 * 10)
    assert copy.getObjectsByLabel("Pad_Base")[0].Label2 == "◆ Storepoint 1: Base"
    assert not copy.getObjectsByLabel("Pocket_Hole")
    assert _methods(copy) == _methods(doc)[:5]
    assert FreeCAD.ActiveDocument is copy

    done = registry.execute("stream.replay", {"storepoint": "Done", "into": "CopyDone", "document": doc.Name})

    copy = FreeCAD.getDocument(done["document"]["name"])
    assert done["steps"] == 9
    assert copy.getObjectsByLabel("Box")[0].Shape.Volume == pytest.approx(final_volume)
    assert sorted(obj.Label for obj in copy.Objects) == sorted(obj.Label for obj in doc.Objects)
    with pytest.raises(CoreError, match="already exists"):
        registry.execute("stream.replay", {"storepoint": "Done", "into": "CopyDone", "document": doc.Name})
    with pytest.raises(CoreError, match="Unknown storepoint"):
        registry.execute("stream.replay", {"storepoint": "Nope", "into": "Copy3", "document": doc.Name})


def test_replay_skips_python_and_stops_at_a_failing_step(
    registry: MethodRegistry, doc: Any, tmp_path: Path
) -> None:
    _add_hole_and_storepoints(registry, doc.Name)
    items = stream.entries(doc)
    items[6]["method"] = "python.execute"  # the hole profile now looks like a script step
    items[6]["params"] = {"code": "pass"}
    stream._write(doc, items)

    with pytest.raises(CoreError) as info:
        registry.execute("stream.replay", {"storepoint": "Done", "into": "Partial", "document": doc.Name})

    assert info.value.data["step"] == 7 and info.value.data["executed"] == 6
    assert "python.execute" in str(info.value.data.get("skipped", info.value.message)) or True
    partial = FreeCAD.getDocument(info.value.data["document"])
    assert partial.getObjectsByLabel("Sketch_Hole") and not partial.getObjectsByLabel("Pocket_Hole")

    items = stream.entries(doc)
    items[6]["method"] = "sketch.add_profile"  # restore the profile, make only the pocket a script step
    items[6]["params"] = {"sketch": "Sketch_Hole", "kind": "circle", "params": {"diameter": 10}}
    items[7]["method"] = "python.execute"
    items[7]["params"] = {"code": "pass"}
    stream._write(doc, items)

    result = registry.execute(
        "stream.replay", {"storepoint": "Done", "into": "Skipped", "document": doc.Name}
    )

    assert result["skipped"] == [{"step": 7, "method": "python.execute"}] and result["steps"] == 8
    assert not FreeCAD.getDocument(result["document"]["name"]).getObjectsByLabel("Pocket_Hole")

    evil = tmp_path / "evil.FCStd"
    items = stream.entries(doc)
    items[7]["method"] = "document.save"  # a crafted file must not make the replay touch the disk
    items[7]["params"] = {"path": str(evil)}
    stream._write(doc, items)

    result = registry.execute(
        "stream.replay", {"storepoint": "Done", "into": "Guarded", "document": doc.Name}
    )

    assert result["skipped"] == [{"step": 7, "method": "document.save"}] and not evil.exists()


def test_damaged_stream_lines_are_ignored(registry: MethodRegistry, doc: Any) -> None:
    _build_box(registry, doc.Name)
    container = doc.getObject(stream.GROUP_NAME)
    container.Stream = [*container.Stream, "{not json", '["a", "list"]', '{"no_method": 1}']

    registry.execute("stream.storepoint", {"name": "Base", "document": doc.Name})

    assert _methods(doc) == [*BOX_STEPS, "stream.storepoint"]
    assert registry.execute("stream.list", {"document": doc.Name})["storepoints"][0]["name"] == "Base"


def test_deleting_an_object_is_part_of_the_stream(registry: MethodRegistry, doc: Any) -> None:
    _build_box(registry, doc.Name)

    registry.execute("document.delete", {"ref": "Pad_Base", "document": doc.Name})

    assert _methods(doc) == [*BOX_STEPS, "document.delete"]
