# FreeCAD Buddy

MCP-Server mit Terminal-Oberfläche für FreeCAD: Ein Agent (z. B. Claude Code) konstruiert 3D-Druck-Bauteile in **PartDesign mit vollständig bestimmten, parametrischen Skizzen** – so, wie ein erfahrener Mensch es tun würde. Du kannst jederzeit in der FreeCAD-GUI weiterarbeiten, Maße im VarSet `Parameters` ändern und das Modell wächst mit.

## Was es besser macht

| Thema | FreeCAD Buddy |
|---|---|
| Werkzeuge | 51 Intent-Level-Tools in 11 Gruppen statt einer API-Kopie; `execute_python` nur per Opt-in |
| Design-Tools | Wiederkehrende Aufgaben in einem Aufruf: `fill_pattern` für Sieb-, Loch-, Lüftungs- und Wabenraster (runde oder Sechseck-Zellen), parametrisch und ohne Addon; fehlende Tools schlägt der Agent mit `propose_design_tool` vor |
| Addons | `search_addons`/`get_addon` durchsuchen den offiziellen FreeCAD-Katalog (offline aus dem Cache); `install_addon` installiert nach Bestätigung im FreeCAD-Dialog |
| Agentenführung | Design-Regelwerk nach Themen mit Werten aus dem Druckerprofil; alle MCP-Ausgaben englisch, FreeCAD-Oberfläche und TUI deutsch |
| Skizzen | Profile (Rechteck, abgerundetes Rechteck, Langloch, Kreis, Polygon, Lochbild, Polyline) sind vollständig bestimmt: Symmetrie zum Ursprung, `Equal`, benannte Maße, keine Block-Constraints |
| Parameter | Maße als Zahl, Parametername oder Ausdruck (`"Box_Width - 2*Wall"`) – gebunden per FreeCAD-Expression |
| Robustheit | Kanten/Flächen über semantische Selektoren (`edges:vertical`, `face:top`, `edges:parallel=X,y=Thickness`); nach Parameteränderungen neu aufgelöst |
| Sicherheit im Modell | Jeder Tool-Aufruf ist genau ein benannter Undo-Schritt; Fehler rollen zurück; offene Nutzer-Bearbeitung wird respektiert |
| 3D-Druck | Druckerprofil, Druckbarkeitsprüfung (Solid, Bauraum, Überhang, Wandstärke, Details), Export STL/3MF/STEP aufs Druckbett mit Reimport-Kontrolle |
| Übersicht | TUI zeigt Bridge-Status, MCP-Sessions und jeden Tool-Aufruf als farbigen Chat aus Anfrage und Antwort |

## Aufbau

```text
Claude Code ──HTTP (MCP, Bearer-Token)──► freecad-buddy (TUI) ──TCP 127.0.0.1 (JSON-RPC, Token)──► Bridge in FreeCAD ──► buddy_core ──► PartDesign/Sketcher
```

| Pfad | Inhalt |
|---|---|
| `addon/FreeCADBuddy/` | FreeCAD-Addon: `buddy_core` (Modellierungslogik), `buddy_bridge` (Transport, nur Stdlib), Workbench „FreeCAD Buddy“ |
| `src/buddy_server/` | TUI-Server `freecad-buddy` (MCP über Streamable HTTP, importiert nie FreeCAD) |
| `examples/reference_projects.py` | Referenzprojekte: Box mit Deckel, Wandhalter, Drehknopf |
| `examples/samples/` | Vergleichs-Samples für LLMs/Thinking-Stufen: Prompt, Soll-Werte, Screenshot, deterministische Prüfung; mitwachsend in Stufen: `referenzmodell.md` (Deckel, Kasten, Baugruppe) und `luefterrahmen.md` (Layout-Skizze, externe Geometrie) |
| `docs/architecture.md` | Architektur und Modellierungsregeln |
| `docs/tools.md` | Tool-Katalog (generiert) |
| `docs/acceptance.md` | Checkliste für die Abnahme in der GUI |

## Installation

Voraussetzungen: Windows, [uv](https://docs.astral.sh/uv/), FreeCAD ≥ 26.3 (weekly). FreeCAD wird unter `%LOCALAPPDATA%\Programs\FreeCAD*` gefunden oder über `FREECAD_HOME` gesetzt.

```bash
uv sync
```

Addon per Junction in FreeCADs Mod-Verzeichnis verlinken (reversibel mit `uv run poe uninstall-addon`):

```bash
uv run poe install-addon
```

## Starten

1. FreeCAD starten. Die Bridge startet automatisch (abschaltbar über Workbench „FreeCAD Buddy“ → „Autostart aus“); manuell über „Bridge starten“.
2. Server mit Oberfläche starten:

```bash
uv run freecad-buddy
```

3. Claude Code anbinden – entweder in der TUI `c` drücken (kopiert den `claude mcp add`-Befehl samt Token) oder das Token als Umgebungsvariable setzen und die mitgelieferte `.mcp.json` verwenden:

```bash
uv run freecad-buddy --print-claude-command
```

Die TUI zeigt jeden Tool-Aufruf als Chat: Die Anfrage-Blase enthält Tool, Client und Argumente, die Antwort-Blase das Ergebnis. Sie ist grün bei Erfolg, gelb bei Warnungen und rot bei Fehlern, jeweils mit Dauer. Lange Inhalte werden gekürzt, Screenshots erscheinen als Platzhalter, Tokens werden maskiert.

Tasten in der TUI:
- `Enter`: vollständige Anfrage und Antwort, darin kopiert `c`
- `v`: zwischen Chat und Einzeilen-Liste wechseln
- `r`: Bridge neu verbinden
- `c`: Claude-Befehl kopieren
- `p`: `execute_python` umschalten (mit Server-Neustart)
- `q`: beenden (ein zweites `q` beendet sofort)

Optionen: `--port` (Standard 8765), `--bridge-port` (Standard 9876), `--headless` (ohne TUI, Log auf stderr), `--allow-python`, `--no-allow-addon-install` (`install_addon` ist standardmäßig an), `--log-file <pfad>` (Tool-Aufrufe als JSONL, maskiert, rotiert ab 10 MB).

## Nutzung

- Design-Regelwerk: Die Server-Instructions enthalten die Kernregeln. Das vollständige Regelwerk nach Themen liefert `get_design_rules(topic)` mit den Werten des aktiven Druckerprofils. Dasselbe gibt es als MCP-Resource `buddy://design-rules/{topic}` und als Prompt `human_modeling_guide`. Quelle ist `src/buddy_server/design_rules.py`.
- MCP-Prompt `design_part` („Konstruiere eine Box 80×50×30 mit Deckel“) führt den Agenten durch den Workflow.
- Design-Tool-Vorschläge landen in `%APPDATA%\FreeCADBuddy\design-tool-proposals.json` und erscheinen in der TUI; `list_design_tool_proposals` listet sie nach Häufigkeit.
- Referenzprojekte gegen den laufenden Server bauen:

```bash
uv run python examples/reference_projects.py box bracket knob --out out
```

## Addons und externe Tools

Alle Punkte sind optional. Ein Tool, das ein fehlendes Addon braucht, meldet `[unsupported]` mit Installationshinweis. Buddy schlägt die Installation erst dann vor, wenn die Aufgabe das Addon wirklich braucht.

| Addon / Tool | Tools | Quelle | Hinweis |
|---|---|---|---|
| Fasteners Workbench | `add_fastener` | Addon Manager (`fasteners`) | Normteile (Schrauben, Muttern, Scheiben) |
| freecad.gears | `add_gear` | Addon Manager (`freecad.gears`) | Zahnräder als Feature im Body (Evolvente, Hohlrad, Zahnstange, Zykloide, Kegel, Schnecke, Zahnriemen) |
| Assembly4 | `create_assembly` & Co. | Addon Manager (`Assembly4`) | Buddy schreibt die Asm4-Konvention selbst. Das Addon brauchst du nur, um die Baugruppe in der GUI zu bearbeiten |
| step.parts | `search_parts`, `insert_part` | Katalog direkt von GitHub (MIT), kein Addon | Referenzteile als STEP (Boards, Lüfter, Motoren, Lager), Cache in `%APPDATA%\FreeCADBuddy\parts-catalog` |
| OrcaSlicer | `export_body` | [orcaslicer.com](https://www.orcaslicer.com) | Ist er installiert, schickt `export_body` stl/3mf automatisch durch den Slicer und liefert Druckzeit und Filament. Die Suchreihenfolge ist `FREECAD_BUDDY_ORCASLICER`, dann `PATH`, dann der Standard-Installationsordner. Eigene Presets setzt du mit `FREECAD_BUDDY_ORCA_SETTINGS="machine.json;process.json"` und `FREECAD_BUDDY_ORCA_FILAMENT=filament.json`, sonst gelten Orcas Standardwerte |

Ein Modell mit Addon-Objekten (Fasteners, Gears) lässt sich nur mit dem Addon neu berechnen. Deshalb führt das README des jeweiligen Projekts die verwendeten Addons im Abschnitt „Benötigte Addons“ auf.

## Entwicklung

```bash
uv run poe check
```

| Task | Inhalt |
|---|---|
| `poe lint` / `poe typecheck` | ruff, pyright |
| `poe test-tools` | Tests im Projekt-Python inkl. End-to-End über MCP gegen eine Headless-Bridge |
| `poe test-core` | Core- und Bridge-Tests in FreeCADs Python (headless) |
| `poe headless-bridge` | Bridge ohne GUI starten (Automatisierung) |
| `python tools/gen_tool_docs.py` | `docs/tools.md` neu erzeugen |

## Sicherheit

- Bridge und MCP-Endpunkt lauschen nur auf `127.0.0.1`; beide verlangen ein Token (`%APPDATA%\FreeCADBuddy\bridge-token`, `mcp-token`).
- Der MCP-Endpunkt prüft `Host`/`Origin` gegen DNS-Rebinding.
- `install_addon` braucht zwei Freischaltungen: Der Server bietet es standardmäßig an (aus mit `--no-allow-addon-install` oder `FREECAD_BUDDY_ALLOW_ADDON_INSTALL=0`), in FreeCAD schaltest du es mit „Addon-Installation erlauben“ frei (bzw. `FREECAD_BUDDY_ALLOW_ADDON_INSTALL=1` im FreeCAD-Prozess). Jede Installation bestätigst du zusätzlich in einem FreeCAD-Dialog (Standard „Abbrechen“). Addons mit Python-Paketen, Addon-Abhängigkeiten oder Git-Pflicht lehnt Buddy ab, dafür ist der Addon Manager zuständig.
- `execute_python` ist standardmäßig aus und braucht zwei Freischaltungen: `--allow-python` beim Server **und** in FreeCAD „Python erlauben“ (oder `FREECAD_BUDDY_ALLOW_PYTHON=1` für beide Prozesse).
- Exporte überschreiben vorhandene Dateien nur mit `overwrite=true`; die Dateiendung muss zum Format passen.

## Fehlerbehebung

| Symptom | Ursache / Lösung |
|---|---|
| `[bridge_unavailable]` | FreeCAD läuft nicht oder Bridge gestoppt → FreeCAD starten, „Bridge starten“ |
| `[busy_user_transaction]` | Du bearbeitest gerade (Skizze/Aufgabenbereich/Dialog offen) → Bearbeitung abschließen |
| `[timeout]` / `[gui_timeout]` | FreeCAD war zu lange beschäftigt; die Meldung sagt, ob etwas geändert wurde – vor einer Wiederholung `get_model_tree` prüfen |
| Port belegt | läuft `freecad-buddy` schon? `--port` bzw. Bridge-Port in FreeCAD (`Mod/FreeCADBuddy/Port`) ändern |
| `[sketch_invalid]` | widersprüchliche Constraints – Details stehen in der Fehlermeldung, das Modell wurde zurückgerollt |
| Screenshot `unsupported` | Screenshots gibt es nur mit laufender GUI, nicht im Headless-Modus |

## Lizenz

MIT, siehe [LICENSE](LICENSE).
