"""AC-06/AC-07 (catalog part): parsing, compatibility and search on a slice of the real catalog."""

import hashlib
import json
from pathlib import Path

import pytest

from buddy_server import addon_catalog as catalog

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "addon_catalog"


@pytest.fixture(scope="module")
def entries() -> list[catalog.AddonEntry]:
    return catalog.load_cache(FIXTURE)


def _by_id(entries: list[catalog.AddonEntry], addon_id: str) -> catalog.AddonEntry:
    return next(e for e in entries if e.id == addon_id)


def test_real_catalog_entries_are_parsed(entries: list[catalog.AddonEntry]) -> None:
    lattice = _by_id(entries, "lattice2")
    assert lattice.kind == "workbench" and "array" in lattice.tags
    assert lattice.license == "LGPL-2.0-or-later" and lattice.repository.startswith("https://github.com/")
    assert _by_id(entries, "FCHoneycombMaker").kind == "macro"
    assert _by_id(entries, "BillOfMaterials").branches[:2] == ["main", "Develop"]
    assert _by_id(entries, "parts_library").sparse is True
    bare = _by_id(entries, "3D_Printing_Tools")  # no metadata in the catalog
    assert bare.name == "3D_Printing_Tools" and bare.description == ""


def test_compatibility_and_python_dependencies(entries: list[catalog.AddonEntry]) -> None:
    btl = _by_id(entries, "btl")
    assert btl.freecad_max == (1, 0, 99)
    assert not btl.compatible_with((26, 3, 0)) and btl.compatible_with((1, 0, 0))
    assert btl.python_dependencies  # requirements.txt is not empty
    assert _by_id(entries, "lattice2").compatible_with((26, 3, 0))


def test_search_ranks_name_over_tags_over_description(entries: list[catalog.AddonEntry]) -> None:
    hits = [entry.id for entry, _ in catalog.search(entries, "grid")]
    assert set(hits[:3]) == {"CarteGrid", "FreeGrid", "Gridfinity"}  # name matches first
    assert next(e.id for e, _ in catalog.search(entries, "array", kind="workbench")) == "lattice2"  # tag
    assert [e.id for e, _ in catalog.search(entries, "honeycomb", kind="macro")] == ["FCHoneycombMaker"]
    assert catalog.search(entries, "grid nonsense-term") == []  # every term must match
    assert catalog.search(entries, "   ") == []


def test_versions_and_checksums() -> None:
    assert catalog.parse_version({"version_as_list": [0, 20, 1, ""]}) == (0, 20, 1)
    assert catalog.parse_version("0.21") == (0, 21, 0)
    assert catalog.parse_version(None) is None
    data = b"catalog"
    digest = hashlib.sha256(data).hexdigest()
    assert catalog.verify_sha256(data, f"{digest} *addon_catalog_cache.zip\n")
    assert not catalog.verify_sha256(data, "0" * 64)
    assert not catalog.verify_sha256(data, "")


def test_hostile_package_xml_is_ignored() -> None:
    bomb = '<?xml version="1.0"?><!DOCTYPE lolz [<!ENTITY lol "lol">]><package><name>&lol;</name></package>'
    data = {"Evil": [{"repository": "https://example.invalid/evil", "metadata": {"package_xml": bomb}}]}
    (entry,) = catalog.parse_addon_catalog(data)
    assert entry.name == "Evil" and entry.description == ""


def test_summary_and_details_are_json_safe(entries: list[catalog.AddonEntry]) -> None:
    lattice = _by_id(entries, "lattice2")
    json.dumps(lattice.summary((26, 3, 0)))
    details = lattice.details((26, 3, 0))
    assert details["compatible"] is True and json.dumps(details)
