# FreeCAD Buddy – Agenten-Kontext

MCP-Server (TUI) + FreeCAD-Addon für PartDesign/Sketcher-3D-Druckteile. Details: [README.md](README.md), [docs/architecture.md](docs/architecture.md), [TODOs/README.md](TODOs/README.md).

## Commands

```bash
uv sync
uv run poe check                      # lint + pyright + alle Tests – Pflicht vor jedem Commit
uv run poe test-tools                 # Projekt-venv inkl. E2E gegen Headless-Bridge
uv run poe test-core                  # Core-/Bridge-Tests in FreeCADs python.exe (headless)
uv run ruff check --select C901 .     # Komplexität ≤ 10, Baseline darf nicht wachsen
uv run python tools/gen_tool_docs.py  # nach jeder Tool-Änderung (test_tool_docs prüft Aktualität)
```

## Schichten (harte Grenzen)

| Paket | Läuft in | Darf nicht |
|---|---|---|
| `src/buddy_server` | Projekt-venv | FreeCAD importieren, Modellierungslogik enthalten |
| `addon/FreeCADBuddy/buddy_bridge` | FreeCAD-Prozess | Nicht-Stdlib-Pakete nutzen, Modellierungslogik enthalten |
| `addon/FreeCADBuddy/buddy_core` | FreeCAD-Python | MCP/Netzwerk nutzen, GUI voraussetzen |

- `tests/tools/test_addon_imports.py`: im Addon nur Stdlib, FreeCAD-Module und `PySide` (nie `PySide6`/`PySide2`). Addon-Manager-Module nur in `buddy_core/addons/install.py`, `FastenersCmd` nur in `buddy_core/assembly.py`.
- `tests/tools/test_tool_contract.py`: Server-Tools rufen nur registrierte Bridge-Methoden auf.

## Regeln mit Gotcha-Potenzial

- Sprache: alles an MCP-Clients englisch (Instructions, Tool-Beschreibungen, Ergebnisse, Fehler, Undo-Namen); FreeCAD-UI, Dialoge, TUI deutsch. UI-Texte außerhalb der UI-Module mit `# ui-de` markieren (`tests/server/test_language.py`).
- ≤ 100 öffentliche Tools; zusammenlegen nur, wenn fachlich sinnvoll. Tool-Gruppe = registrierendes Modul in `src/buddy_server/tools/`.
- Jede Mutation in `buddy_core.transaction.transaction(doc, "<Aktion>: <Zweck>")` = genau ein Undo-Schritt, Rollback bei Fehler; innere Aufrufe hängen sich an die äußere Transaktion.
- FreeCAD-Zugriffe nur im Qt-Hauptthread (Bridge-Dispatch), nie aus dem Socket-Thread.
- Neue Bridge-Methode: in `buddy_bridge/registry.py` (`NOT_RECORDED`) und `buddy_bridge/replay.py` (`REPLAYABLE`/`NEVER_REPLAYED`) einordnen.
- API-Drift: neue FreeCAD-Typen in `buddy_core.compat.REQUIRED_TYPES`; fehlende Features → Fehler `1007 unsupported`, keine rohe Exception.
- FreeCADs Python startet ohne `PYTHONHOME`/`PYTHONPATH`/`VIRTUAL_ENV` (`tools/freecad_env.py`), sonst lädt es die Stdlib des uv-Pythons.

## Arbeitsweise (Details: TODOs/README.md)

- Eine Session = ein Session-Paket, endet mit grünem `uv run poe check` + Commit; Session-Log-Zeile `Komplexität:`.
- Dateien > 400 Zeilen wachsen nicht weiter; keine neue Dependency außerhalb eines `infra`-Sprints.
- Eine Domäne je Sprint; Befunde außerhalb des Umfangs als `E-NN` in den Eingang des Backlog-Index, nicht nebenbei fixen.
- Sprint-Abschluss erst nach Review-Gate (`97-review.md`) und Ralfs Bestätigung im Chat.
- GUI-Abnahme ([docs/acceptance.md](docs/acceptance.md)) nur nach Freigabe; `execute_python` danach wieder ausschalten.
