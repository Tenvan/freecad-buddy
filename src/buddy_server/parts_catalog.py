"""step.parts catalogue: open STEP models (fasteners, electronics, motion parts, ...) straight from GitHub.

The catalogue is one static ``catalog/parts.json`` in the earthtojake/step.parts repository, the STEP
files live there via Git LFS (same source as the stepParts addon, api_client.py). So Buddy needs no
addon: it caches the catalogue daily, searches it locally and downloads single STEP files on demand.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

import httpx2

from buddy_server.addon_service import CatalogError, Fetch, http_fetch

CATALOG_URL = "https://raw.githubusercontent.com/earthtojake/step.parts/main/catalog/parts.json"
STEP_URL = "https://media.githubusercontent.com/media/earthtojake/step.parts/main/catalog/step/{id}.step"
MAX_AGE_SECONDS = 24 * 3600
_ID = re.compile(r"^[A-Za-z0-9_.-]+$")


class PartsCatalog:
    def __init__(self, cache_dir: Path, fetch: Fetch = http_fetch, max_age: float = MAX_AGE_SECONDS) -> None:
        self.cache_dir = cache_dir
        self.fetch = fetch
        self.max_age = max_age
        self._parts: list[dict[str, Any]] | None = None

    @property
    def _catalog_path(self) -> Path:
        return self.cache_dir / "parts.json"

    async def parts(self, refresh: bool = False) -> list[dict[str, Any]]:
        path = self._catalog_path
        stale = not path.is_file() or time.time() - path.stat().st_mtime > self.max_age
        if refresh or stale:
            try:
                data = await self.fetch(CATALOG_URL, 120)
                json.loads(data)  # must be valid before it replaces the cache
            except (httpx2.HTTPError, OSError, ValueError) as error:
                if not path.is_file():
                    raise CatalogError("catalog_unavailable", f"{CATALOG_URL}: {error}") from None
            else:
                self.cache_dir.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                self._parts = None
        parts = self._parts
        if parts is None:
            parts = self._parts = json.loads(path.read_text(encoding="utf-8"))
        return parts

    async def search(self, query: str, category: str | None = None, limit: int = 10) -> dict[str, Any]:
        """Every search term must occur in name, id, description, aliases or tags."""
        terms = query.lower().split()
        hits = []
        for part in await self.parts():
            if category and part.get("category") != category:
                continue
            hay = " ".join(
                [part.get("id", ""), part.get("name", ""), part.get("description", ""),
                 *(part.get("aliases") or []), *(part.get("tags") or [])]
            ).lower()  # fmt: skip
            if all(term in hay for term in terms):
                hits.append(part)
        return {
            "count": len(hits),
            "results": [
                {key: part[key] for key in ("id", "name", "category", "family", "attributes") if key in part}
                for part in hits[:limit]
            ],
        }

    async def find(self, part_id: str) -> dict[str, Any] | None:
        return next((p for p in await self.parts() if p.get("id") == part_id), None)

    async def step_file(self, part_id: str) -> Path:
        """Local copy of the part's STEP file (downloaded once)."""
        if not _ID.match(part_id):
            raise CatalogError("invalid_id", f"Invalid part id '{part_id}'")
        target = self.cache_dir / "step" / f"{part_id}.step"
        if target.is_file():
            return target
        url = STEP_URL.format(id=part_id)
        try:
            data = await self.fetch(url, 120)
        except (httpx2.HTTPError, OSError) as error:
            raise CatalogError("catalog_unavailable", f"{url}: {error}") from None
        if not data.lstrip().startswith(b"ISO-10303-21"):
            raise CatalogError("catalog_unavailable", f"{url} is no STEP file")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target
