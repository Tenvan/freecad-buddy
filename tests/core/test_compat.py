import FreeCAD

from buddy_core import compat


def test_freecad_info_reports_running_build() -> None:
    info = compat.freecad_info()

    assert info.version == ".".join(FreeCAD.Version()[:3])
    assert info.python.startswith("3.")
    assert info.gui_up is False  # core tests run headless


def test_version_tuple_is_numeric() -> None:
    assert compat.version_tuple() >= (1, 0, 0)


def test_all_required_types_are_available() -> None:
    assert compat.missing_types() == []


def test_unknown_type_is_reported() -> None:
    assert compat.missing_types(("PartDesign::Pad", "PartDesign::DoesNotExist")) == [
        "PartDesign::DoesNotExist"
    ]


def test_type_probe_leaves_no_document_behind() -> None:
    before = set(FreeCAD.listDocuments())
    compat.missing_types()

    assert set(FreeCAD.listDocuments()) == before
