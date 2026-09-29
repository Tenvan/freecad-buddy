"""AC-06/AC-07: catalog download, checksum, offline cache and the MCP tools – all without network."""

import asyncio
import hashlib
import io
import json
import shutil
import time
import zipfile
from pathlib import Path

import httpx2
import pytest

from buddy_server import addon_service
from buddy_server.addon_service import AddonCatalogService, CatalogError

from .conftest import make_settings, mcp_session, running_server, tool_caller

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "addon_catalog"


def _zip(member: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(member, (FIXTURE / member).read_text(encoding="utf-8"))
    return buffer.getvalue()


class FakeCatalogServer:
    """Serves the fixture as addons.freecad.org would; can go offline or send a wrong checksum."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        for member, name in addon_service.CACHES.items():
            data = _zip(member)
            self.files[addon_service.CATALOG_BASE + name] = data
            self.files[addon_service.CATALOG_BASE + name + ".sha256"] = (
                hashlib.sha256(data).hexdigest().encode()
            )
        self.offline = False
        self.requests: list[str] = []

    async def __call__(self, url: str, timeout: float) -> bytes:
        self.requests.append(url)
        if self.offline:
            raise httpx2.ConnectError("offline")
        if url not in self.files:
            raise httpx2.HTTPStatusError(
                "404", request=httpx2.Request("GET", url), response=httpx2.Response(404)
            )
        return self.files[url]


def test_download_verifies_and_caches(tmp_path: Path) -> None:
    server = FakeCatalogServer()
    service = AddonCatalogService(tmp_path, server)

    state = asyncio.run(service.ensure())
    assert state.source == "online" and len(server.requests) == 4
    assert {e.id for e in service.entries()} >= {"lattice2", "FCHoneycombMaker"}

    state = asyncio.run(service.ensure())  # fresh cache: no request at all
    assert state.source == "cache" and len(server.requests) == 4

    asyncio.run(service.ensure(refresh=True))  # unchanged checksums: only the .sha256 files are fetched
    assert server.requests[4:] == [u for u in server.files if u.endswith(".sha256")]


def test_offline_uses_cache_with_warning_and_fails_without_cache(tmp_path: Path) -> None:
    server = FakeCatalogServer()
    asyncio.run(AddonCatalogService(tmp_path / "a", server).ensure())
    server.offline = True

    state = asyncio.run(AddonCatalogService(tmp_path / "a", server, max_age=0).ensure())
    assert state.source == "cache" and "could not be updated" in state.warning

    with pytest.raises(CatalogError) as info:
        asyncio.run(AddonCatalogService(tmp_path / "b", server).ensure())
    assert info.value.code == "catalog_unavailable"


def test_wrong_checksum_is_rejected_and_the_cache_stays(tmp_path: Path) -> None:
    server = FakeCatalogServer()
    service = AddonCatalogService(tmp_path, server)
    asyncio.run(service.ensure())
    before = (tmp_path / "addon_catalog_cache.json").read_bytes()
    server.files[addon_service.CATALOG_BASE + "addon_catalog_cache.zip.sha256"] = b"0" * 64

    with pytest.raises(CatalogError) as info:
        asyncio.run(service.ensure(refresh=True))
    assert info.value.code == "catalog_checksum"
    assert (tmp_path / "addon_catalog_cache.json").read_bytes() == before


def test_readme_is_cleaned_and_shortened(tmp_path: Path) -> None:
    server = FakeCatalogServer()
    service = AddonCatalogService(tmp_path, server)
    asyncio.run(service.ensure())
    lattice = service.find("Lattice2")  # case-insensitive, by id or name
    assert lattice is not None
    url = next(u for u in addon_service._readme_urls(lattice) if "raw.githubusercontent.com" in u)
    server.files[url] = ("# Lattice2\n![badge](x.svg)\n<p>Arrays</p>\n\n\n\nText " + "x" * 5000).encode()

    text = asyncio.run(service.readme(lattice))
    assert text is not None and text.startswith("# Lattice2") and "badge" not in text and "<p>" not in text
    assert len(text) <= addon_service.README_CHARS


def _seed_cache(home: Path) -> None:
    target = home / "addon-catalog"
    target.mkdir(parents=True, exist_ok=True)
    for member in addon_service.CACHES:
        shutil.copy(FIXTURE / member, target / member)
    (target / "catalog-meta.json").write_text(json.dumps({"fetched_at": time.time()}), encoding="utf-8")


def test_search_and_details_over_mcp(bridge_home: tuple[Path, int]) -> None:
    home, bridge_port = bridge_home
    _seed_cache(home)
    settings = make_settings(home, bridge_port)

    async def scenario() -> None:
        async with running_server(settings), mcp_session(settings) as session:
            call = tool_caller(session)
            found = await call("search_addons", query="grid")
            assert found["catalog"]["source"] == "cache" and found["count"] >= 3
            first = found["results"][0]
            assert {"id", "kind", "compatible", "installed", "license"} <= set(first)
            assert first["compatible"] is True and first["installed"] is False

            macros = await call("search_addons", query="honeycomb", kind="macro")
            assert [r["id"] for r in macros["results"]] == ["FCHoneycombMaker"]

            btl = await call("get_addon", addon_id="btl", readme=False)
            assert btl["compatible"] is False and btl["python_dependencies"]
            assert btl["freecad_max"] == "1.0.99"

            missing = await session.call_tool("get_addon", {"addon_id": "does-not-exist", "readme": False})
            assert missing.is_error and "[not_found]" in missing.content[0].text  # type: ignore[union-attr]

    asyncio.run(scenario())
