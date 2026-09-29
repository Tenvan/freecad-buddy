"""step.parts catalogue and OrcaSlicer CLI on the server side - without network and without OrcaSlicer."""

import asyncio
import io
import json
import zipfile
from pathlib import Path

import httpx2
import pytest

from buddy_server import parts_catalog, slicer
from buddy_server.addon_service import CatalogError
from buddy_server.parts_catalog import PartsCatalog

PARTS = [
    {"id": "raspberry_pi_5", "name": "Raspberry Pi 5", "description": "", "category": "electronics",
     "family": "sbc", "tags": ["board"], "aliases": ["rpi5"], "attributes": {}},
    {"id": "bearing_608", "name": "608 ball bearing", "description": "skateboard bearing",
     "category": "bearing", "family": "ball-bearing", "tags": ["metric"], "aliases": [], "attributes": {}},
]  # fmt: skip
STEP = b"ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;\n"


class FakeFetch:
    def __init__(self) -> None:
        self.online = True
        self.calls: list[str] = []
        self.files = {parts_catalog.CATALOG_URL: json.dumps(PARTS).encode()}
        self.files[parts_catalog.STEP_URL.format(id="bearing_608")] = STEP
        self.files[parts_catalog.STEP_URL.format(id="raspberry_pi_5")] = b"version https://git-lfs..."

    async def __call__(self, url: str, timeout: float) -> bytes:
        self.calls.append(url)
        if not self.online:
            raise httpx2.ConnectError("offline")
        return self.files[url]


def test_search_matches_all_terms_and_category(tmp_path: Path) -> None:
    catalog = PartsCatalog(tmp_path, FakeFetch())
    assert [p["id"] for p in asyncio.run(catalog.search("rpi5"))["results"]] == ["raspberry_pi_5"]
    assert asyncio.run(catalog.search("608 metric"))["count"] == 1
    assert asyncio.run(catalog.search("bearing", category="electronics"))["count"] == 0


def test_catalogue_is_cached_and_works_offline(tmp_path: Path) -> None:
    fetch = FakeFetch()
    asyncio.run(PartsCatalog(tmp_path, fetch).parts())
    fetch.online = False
    stale = PartsCatalog(tmp_path, fetch, max_age=0)  # due for refresh, but offline: the cache stays
    assert len(asyncio.run(stale.parts())) == 2
    with pytest.raises(CatalogError):
        asyncio.run(PartsCatalog(tmp_path / "empty", fetch).parts())


def test_step_file_is_downloaded_once_and_validated(tmp_path: Path) -> None:
    fetch = FakeFetch()
    catalog = PartsCatalog(tmp_path, fetch)
    path = asyncio.run(catalog.step_file("bearing_608"))
    assert path.read_bytes() == STEP
    asyncio.run(catalog.step_file("bearing_608"))
    assert fetch.calls.count(parts_catalog.STEP_URL.format(id="bearing_608")) == 1
    with pytest.raises(CatalogError, match="no STEP"):  # an LFS pointer instead of the file
        asyncio.run(catalog.step_file("raspberry_pi_5"))
    with pytest.raises(CatalogError, match="Invalid"):
        asyncio.run(catalog.step_file("../../evil"))


def test_find_orca_prefers_the_explicit_path(tmp_path: Path) -> None:
    exe = tmp_path / "orca-slicer.exe"
    exe.write_bytes(b"")
    assert slicer.find_orca({"FREECAD_BUDDY_ORCASLICER": str(exe)}) == exe
    assert slicer.find_orca({"FREECAD_BUDDY_ORCASLICER": str(tmp_path / "missing.exe")}) is None
    program_files = tmp_path / "pf"
    (program_files / "OrcaSlicer").mkdir(parents=True)
    (program_files / "OrcaSlicer" / "orca-slicer.exe").write_bytes(b"")
    assert slicer.find_orca({"ProgramFiles": str(program_files), "PATH": ""}) is not None


def test_command_loads_presets_only_when_configured(tmp_path: Path) -> None:
    model, out = tmp_path / "Box.3mf", tmp_path / "Box.gcode.3mf"
    plain = slicer.command(Path("orca"), model, out, {})
    assert "--load-settings" not in plain and plain[-1] == str(model)
    env = {"FREECAD_BUDDY_ORCA_SETTINGS": "m.json;p.json", "FREECAD_BUDDY_ORCA_FILAMENT": "f.json"}
    full = slicer.command(Path("orca"), model, out, env)
    assert full[full.index("--load-settings") + 1] == "m.json;p.json"
    assert full[full.index("--export-3mf") + 1] == "Box.gcode.3mf"


def _sliced(tmp_path: Path, members: dict[str, str]) -> Path:
    path = tmp_path / "Box.gcode.3mf"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, text in members.items():
            archive.writestr(name, text)
    path.write_bytes(buffer.getvalue())
    return path


def test_read_result_from_slice_info(tmp_path: Path) -> None:
    info = """<?xml version="1.0" encoding="UTF-8"?><config><plate>
      <metadata key="index" value="1"/><metadata key="prediction" value="8040"/>
      <metadata key="weight" value="38.12"/>
      <filament id="1" type="PLA" used_m="12.5" used_g="38.12"/>
      <warning msg="Floating regions" level="1"/></plate></config>"""
    result = slicer.read_result(_sliced(tmp_path, {"Metadata/slice_info.config": info}))
    assert result["print_time_s"] == 8040 and result["print_time"] == "2 h 14 min"
    assert result["filament_g"] == 38.12 and result["filament_m"] == 12.5
    assert result["slicer_warnings"] == ["Floating regions"]


def test_read_result_falls_back_to_gcode_comments(tmp_path: Path) -> None:
    gcode = "; HEADER\n; estimated printing time (normal mode) = 1h 2m 3s\n; total filament weight [g] : 4.5\nG1 X0\n"
    result = slicer.read_result(_sliced(tmp_path, {"Metadata/plate_1.gcode": gcode}))
    assert result["print_time_s"] == 3723 and result["filament_g"] == 4.5
