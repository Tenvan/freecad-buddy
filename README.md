# FreeCAD Buddy

MCP-Server mit Terminal-Oberfläche für FreeCAD, über den ein Agent 3D-Druck-Projekte in FreeCAD **PartDesign mit voll bestimmten Skizzen** aufbaut – so, dass der Mensch jederzeit in der GUI weiterarbeiten kann.

> Status: im Aufbau (Sprint [`freecad-buddy-aufbau`](TODOs/2-sprints-aktiv/freecad-buddy-aufbau/00-index.md)).

## Aufbau

| Pfad | Inhalt |
|---|---|
| `addon/FreeCADBuddy/` | FreeCAD-Addon: `buddy_core` (Modellierungslogik), später `buddy_bridge` (Transport) |
| `src/buddy_server/` | TUI-Server `freecad-buddy` (manuell gestartet, MCP über Streamable HTTP, importiert nie FreeCAD) |
| `tests/core/` | Tests, die in FreeCADs Python laufen |
| `tests/tools/` | Tests der Hilfsskripte (Projekt-Python) |
| `tools/` | Entwickler-Hilfsskripte (FreeCAD-Lokalisierung, Core-Testrunner) |
| `docs/architecture.md` | Architektur und Modellierungsregeln |

## Entwicklung

Voraussetzungen: [uv](https://docs.astral.sh/uv/), FreeCAD ≥ 26.3 (weekly). Die Installation wird automatisch unter `%LOCALAPPDATA%\Programs\FreeCAD*` gefunden oder über `FREECAD_HOME` gesetzt.

```bash
uv sync
```

```bash
uv run poe check
```

Einzelne Tasks: `uv run poe lint`, `uv run poe typecheck`, `uv run poe test-tools`, `uv run poe test-core`.

## Lizenz

MIT, siehe [LICENSE](LICENSE).
