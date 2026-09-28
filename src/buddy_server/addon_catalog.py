"""Official FreeCAD addon catalog: parse, check compatibility, search. Stdlib only, no FreeCAD import.

Formats (FreeCAD 1.1+ Addon Manager, verified 2026-09-28 against addons.freecad.org):

* ``addon_catalog_cache.json``: ``{addon_id: [entry, …]}``, one entry per branch with ``repository``,
  ``git_ref``, ``zip_url``, ``curated``, ``sparse_cache``, ``last_update_time``,
  ``freecad_min``/``freecad_max`` (``{"version_as_list": [1, 0, 99, ""]}`` or null) and ``metadata``
  (``package_xml`` text, ``requirements_txt``, ``metadata_txt``) or null.
* ``macro_cache.json``: ``{macro_name: {name, comment, desc, author, license, version, url, …}}``.
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ADDON_CACHE = "addon_catalog_cache.json"
MACRO_CACHE = "macro_cache.json"
_NS = "{https://wiki.freecad.org/Package_Metadata}"
_MAX_XML_CHARS = 200_000
_CONTENT_KINDS = {"workbench": "workbench", "macro": "macro", "preferencepack": "preference_pack"}

Version = tuple[int, int, int]


@dataclass
class AddonEntry:
    id: str
    kind: str  # workbench | macro | preference_pack | other
    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    license: str = ""
    maintainer: str = ""
    repository: str = ""
    branch: str = ""
    branches: list[str] = field(default_factory=list)
    zip_url: str = ""
    last_update: str = ""
    version: str = ""
    freecad_min: Version | None = None
    freecad_max: Version | None = None
    addon_dependencies: list[str] = field(default_factory=list)
    python_dependencies: list[str] = field(default_factory=list)
    curated: bool = True
    sparse: bool = False
    readme_url: str = ""
    filename: str = ""
    """Macros: file name in the macro directory (installed-check)."""

    def compatible_with(self, version: Version) -> bool:
        return (self.freecad_min is None or version >= self.freecad_min) and (
            self.freecad_max is None or version <= self.freecad_max
        )

    def summary(self, version: Version | None = None) -> dict[str, Any]:
        data = {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "description": _shorten(self.description, 200),
            "tags": self.tags,
            "license": self.license,
            "repository": self.repository,
            "python_dependencies": bool(self.python_dependencies),
        }
        if version is not None:
            data["compatible"] = self.compatible_with(version)
        return data

    def details(self, version: Version | None = None) -> dict[str, Any]:
        data = asdict(self)
        data["freecad_min"] = _version_text(self.freecad_min)
        data["freecad_max"] = _version_text(self.freecad_max)
        if version is not None:
            data["compatible"] = self.compatible_with(version)
        return data


def _shorten(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _version_text(version: Version | None) -> str | None:
    return ".".join(str(part) for part in version) if version else None


def parse_version(raw: Any) -> Version | None:
    """``{"version_as_list": [0, 20, 1, ""]}``, ``"0.21"`` or ``"1.0.2"`` → ``(0, 20, 1)``."""
    if isinstance(raw, Mapping):
        raw = raw.get("version_as_list")
    if isinstance(raw, list | tuple):
        numbers = [int(part) for part in raw[:3] if isinstance(part, int)]
    elif isinstance(raw, str) and raw.strip():
        numbers = [int(part) for part in re.findall(r"\d+", raw)[:3]]
    else:
        return None
    if not numbers:
        return None
    numbers += [0] * (3 - len(numbers))
    return numbers[0], numbers[1], numbers[2]


def _text(node: ET.Element | None, tag: str) -> str:
    child = node.find(_NS + tag) if node is not None else None
    return (child.text or "").strip() if child is not None else ""


def _package(xml_text: str) -> dict[str, Any]:
    """The fields of a ``package.xml`` we need (tolerant: broken XML yields an empty dict).

    The catalog is third-party data and ``defusedxml`` is not available in FreeCAD's Python: package
    metadata never needs a DTD, so any DOCTYPE/ENTITY declaration (XXE, billion laughs) is rejected.
    """
    if len(xml_text) > _MAX_XML_CHARS or "<!DOCTYPE" in xml_text.upper() or "<!ENTITY" in xml_text.upper():
        return {}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return {}
    kinds: list[str] = []
    tags = [tag.text.strip() for tag in root.findall(_NS + "tag") if tag.text]
    depends = [
        dep.text.strip() for dep in root.findall(_NS + "depend") if dep.text and dep.get("type") != "python"
    ]
    python = [
        dep.text.strip() for dep in root.findall(_NS + "depend") if dep.text and dep.get("type") == "python"
    ]
    fc_min, fc_max = _text(root, "freecadmin"), _text(root, "freecadmax")
    content = root.find(_NS + "content")
    for child in list(content) if content is not None else []:
        kind = _CONTENT_KINDS.get(child.tag.removeprefix(_NS))
        if kind:
            kinds.append(kind)
        tags += [tag.text.strip() for tag in child.findall(_NS + "tag") if tag.text]
        fc_min = fc_min or _text(child, "freecadmin")
        fc_max = fc_max or _text(child, "freecadmax")
    urls = {url.get("type"): (url.text or "").strip() for url in root.findall(_NS + "url")}
    return {
        "name": _text(root, "name"),
        "description": _text(root, "description"),
        "version": _text(root, "version"),
        "maintainer": _text(root, "maintainer"),
        "license": _text(root, "license"),
        "tags": sorted(set(tags), key=str.lower),
        "kinds": kinds,
        "freecad_min": fc_min,
        "freecad_max": fc_max,
        "depends": depends,
        "python": python,
        "readme": urls.get("readme", ""),
    }


def _requirements(text: str) -> list[str]:
    lines = (line.split("#", 1)[0].strip() for line in text.splitlines())
    return [line for line in lines if line]


def parse_addon_catalog(data: Mapping[str, Any]) -> list[AddonEntry]:
    """One entry per addon id; the first branch is the primary one (like the Addon Manager)."""
    entries: list[AddonEntry] = []
    for addon_id, branches in data.items():
        if not isinstance(branches, list) or not branches:
            continue
        primary = branches[0]
        metadata = primary.get("metadata") or {}
        package = _package(metadata.get("package_xml", "")) if metadata.get("package_xml") else {}
        kinds = package.get("kinds", [])
        python = sorted(set(package.get("python", []) + _requirements(metadata.get("requirements_txt", ""))))
        entries.append(
            AddonEntry(
                id=addon_id,
                kind=kinds[0] if kinds else ("workbench" if not package else "other"),
                name=package.get("name") or addon_id,
                description=package.get("description", ""),
                tags=package.get("tags", []),
                license=package.get("license", ""),
                maintainer=package.get("maintainer", ""),
                repository=primary.get("repository") or "",
                branch=primary.get("branch_display_name") or primary.get("git_ref") or "",
                branches=[b.get("branch_display_name") or b.get("git_ref") or "" for b in branches],
                zip_url=primary.get("zip_url") or "",
                last_update=primary.get("last_update_time") or "",
                version=package.get("version", ""),
                freecad_min=parse_version(primary.get("freecad_min"))
                or parse_version(package.get("freecad_min")),
                freecad_max=parse_version(primary.get("freecad_max"))
                or parse_version(package.get("freecad_max")),
                addon_dependencies=package.get("depends", []),
                python_dependencies=python,
                curated=bool(primary.get("curated", True)),
                sparse=bool(primary.get("sparse_cache", False)),
                readme_url=package.get("readme", ""),
            )
        )
    return entries


def parse_macro_catalog(data: Mapping[str, Any]) -> list[AddonEntry]:
    entries = []
    for name, macro in data.items():
        if not isinstance(macro, Mapping):
            continue
        entries.append(
            AddonEntry(
                id=name,
                kind="macro",
                name=str(macro.get("name") or name),
                description=str(macro.get("comment") or macro.get("desc") or ""),
                license=str(macro.get("license") or ""),
                maintainer=str(macro.get("author") or ""),
                repository=str(macro.get("url") or macro.get("wiki") or ""),
                version=str(macro.get("version") or ""),
                last_update=str(macro.get("date") or ""),
                filename=_macro_filename(name, macro),
            )
        )
    return entries


def _macro_filename(name: str, macro: Mapping[str, Any]) -> str:
    for key in ("src_filename", "filename_from_url"):
        value = str(macro.get(key) or "")
        if value:
            return value.replace("\\", "/").rsplit("/", 1)[-1]
    return name.replace(" ", "_") + ".FCMacro"


def load_cache(directory: Path) -> list[AddonEntry]:
    """Entries from the unpacked cache files in ``directory`` (missing files are skipped)."""
    entries: list[AddonEntry] = []
    for filename, parser in ((ADDON_CACHE, parse_addon_catalog), (MACRO_CACHE, parse_macro_catalog)):
        path = directory / filename
        if path.is_file():
            entries += parser(json.loads(path.read_text(encoding="utf-8")))
    return entries


def verify_sha256(data: bytes, expected: str) -> bool:
    """``expected`` is the content of the ``.sha256`` file (``"<hex>"`` or ``"<hex> *name"``)."""
    token = expected.strip().split()[0].lower() if expected.strip() else ""
    return bool(token) and hashlib.sha256(data).hexdigest() == token


def _terms(query: str) -> list[str]:
    return [term for term in re.split(r"[\s,;]+", query.lower()) if term]


def _score(entry: AddonEntry, terms: Iterable[str]) -> int:
    ident, name = entry.id.lower(), entry.name.lower()
    tags = [tag.lower() for tag in entry.tags]
    text = entry.description.lower()
    total = 0
    for term in terms:
        if term in (ident, name):
            points = 100
        elif term in ident or term in name:
            points = 50
        elif any(term == tag for tag in tags):
            points = 40
        elif any(term in tag for tag in tags):
            points = 25
        elif re.search(rf"\b{re.escape(term)}", text):
            points = 15
        elif term in text:
            points = 5
        else:
            return 0  # every term must match somewhere
        total += points
    return total


def search(
    entries: Iterable[AddonEntry],
    query: str,
    kind: str | None = None,
    limit: int = 10,
) -> list[tuple[AddonEntry, int]]:
    """Ranked matches: name > tag > description; all terms must match; curated before community."""
    terms = _terms(query)
    if not terms:
        return []
    scored = [
        (entry, score)
        for entry in entries
        if (kind is None or entry.kind == kind) and (score := _score(entry, terms)) > 0
    ]
    scored.sort(key=lambda item: (-item[1], not item[0].curated, item[0].name.lower()))
    return scored[:limit]
