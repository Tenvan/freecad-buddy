from pathlib import Path
from typing import Any

import FreeCAD
import pytest

from buddy_core import body, documents
from buddy_core.errors import VALIDATION, CoreError


def _new(name: str = "Lifecycle") -> Any:
    return FreeCAD.getDocument(documents.new_document(name).data["document"]["name"])


def test_closing_an_untouched_document_needs_no_decision() -> None:
    doc = _new()
    name = doc.Name

    result = documents.close_document(name).to_dict()

    assert result["closed"]["name"] == name
    assert result["discarded_changes"] is False
    assert name not in FreeCAD.listDocuments()


def test_unsaved_changes_are_refused_then_discarded() -> None:
    doc = _new()
    name = doc.Name
    body.create_body("Box", document=name)

    with pytest.raises(CoreError) as info:
        documents.close_document(name)
    assert info.value.name == VALIDATION
    assert name in FreeCAD.listDocuments()

    result = documents.close_document(name, unsaved="discard").to_dict()
    assert result["discarded_changes"] is True
    assert name not in FreeCAD.listDocuments()


def test_close_with_save_writes_the_file_first(tmp_path: Path) -> None:
    doc = _new()
    body.create_body("Box", document=doc.Name)
    target = tmp_path / "saved.FCStd"

    result = documents.close_document(doc.Name, unsaved="save", path=str(target)).to_dict()

    assert target.is_file()
    assert result["closed"]["file"] == str(target)


def test_saving_clears_the_unsaved_state(tmp_path: Path) -> None:
    doc = _new()
    body.create_body("Box", document=doc.Name)
    documents.save_document(doc.Name, str(tmp_path / "clean.FCStd"))

    assert documents.has_unsaved_changes(doc) is False
    documents.close_document(doc.Name)  # no decision needed after saving


def test_revert_restores_the_saved_state(tmp_path: Path) -> None:
    doc = _new()
    body.create_body("Box", document=doc.Name)
    file = tmp_path / "revert.FCStd"
    documents.save_document(doc.Name, str(file))
    body.create_body("Lid", document=doc.Name)

    result = documents.revert_document(doc.Name).to_dict()

    reverted = FreeCAD.getDocument(result["document"]["name"])
    try:
        assert result["discarded_changes"] is True
        assert [o.Label for o in reverted.Objects if o.TypeId == "PartDesign::Body"] == ["Box"]
        assert documents.has_unsaved_changes(reverted) is False
    finally:
        FreeCAD.closeDocument(reverted.Name)


def test_revert_needs_a_saved_file() -> None:
    doc = _new()
    try:
        with pytest.raises(CoreError) as info:
            documents.revert_document(doc.Name)
        assert info.value.name == VALIDATION
    finally:
        FreeCAD.closeDocument(doc.Name)


def test_unknown_unsaved_mode_is_rejected() -> None:
    doc = _new()
    try:
        with pytest.raises(CoreError):
            documents.close_document(doc.Name, unsaved="later")
    finally:
        FreeCAD.closeDocument(doc.Name)
