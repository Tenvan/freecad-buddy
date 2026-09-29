# Changelog

## 0.2.0 — 2026-09-29

Aus den Sprints `freecad-buddy-referenzen` und `freecad-buddy-design-regelwerk`.

### Breaking

- `new_document`, `open_document`, `save_document`, `close_document` und `revert_document` sind ersetzt durch `document(action=new|open|save|close|revert)`.
- Alle MCP-Ausgaben sind englisch: Instructions, Regelwerk, Prompts, Tool-Beschreibungen, Ergebnisse, Hinweise (`Hint:` statt `Hinweis:`), Fehler und Undo-Namen. FreeCAD-Oberfläche, Bestätigungsdialog, Konsole und TUI bleiben deutsch.

### Neu

- Design-Regelwerk mit zehn Themen über `get_design_rules`, die Resource `buddy://design-rules/{topic}` und den Prompt `human_modeling_guide`; Druckwerte folgen dem Druckerprofil. Kompakte Server-Instructions mit Kernregeln, Ansichtsregel und Design-Tool-Regel.
- Design-Tool `fill_pattern`: Sieb-, Loch-, Lüftungs- und Wabenraster in einem Aufruf und einem Undo-Schritt, runde oder Sechseck-Zellen, Layout rechteckig oder versetzt, Anzahl fest oder aus der Feldgröße (auch über Parameter), rein nativ ohne Addon.
- `propose_design_tool` und `list_design_tool_proposals`: Vorschläge für fehlende Design-Tools, zusammengeführt und gezählt, Meldung in der TUI.
- Addons: `search_addons` und `get_addon` durchsuchen den offiziellen Katalog mit Kompatibilität, Installationsstatus, Lizenz und README-Auszug (offline aus dem Cache). `install_addon` installiert Addons und Makros über FreeCADs Addon Manager nach Bestätigung im FreeCAD-Dialog; server- und FreeCAD-seitig freizuschalten, serverseitig standardmäßig an.
- Referenzen: externe Geometrie in Skizzen (`add_geometry` Typ `external`, Referenzen `x<N>`), `shape_binder` für Bezüge über Body-Grenzen, parametrische Senkungen an `hole`.
- Zahnräder, Normteile und Slicer: `add_gear` (freecad.gears als Feature im Body), `search_parts`/`insert_part` (STEP-Referenzteile aus step.parts), `export_body` schickt stl/3mf durch einen installierten OrcaSlicer.
- Weitere Tools: `sweep` (Profil entlang eines Pfads, Profil `u_path`), `thread` (echte metrische Außengewinde), `set_material`, Assembly4-Baugruppen (`create_assembly`, `add_to_assembly`, `add_fastener`, `explode_assembly`, `apply_configuration`), `set_view`.
- `add_profile polygon` mit `orientation` `flat` oder `pointy`.
- Ansicht: Nach dem ersten `pad`/`revolve` eines Bodys springt FreeCAD auf iso und zeigt das ganze Bauteil.
- Tool-Katalog nach Arbeitsphasen gruppiert, jede Tool-Beschreibung mit Kategorie-Präfix (`[Sketch]`, `[Design tools]`, …).
- TUI: Tool-Aufrufe als farbiger Chat mit Anfrage und Antwort, Detailansicht per Enter, Umschaltung auf die Liste mit `v`, maskierte Geheimnisse, verstellbares Meldungsfenster; `--log-file` schreibt die Aufrufe als JSONL mit.
- Workbench: Schalter für Autostart, Python und Addon-Installation als Button-Paare; Body und Features mit dickeren Kanten und größeren Punkten für die Auswahl.
- Referenzmodelle `referenzmodell` (Stufen 1–5) und `luefterrahmen` als Vergleichs-Samples mit Prüfskript.

### Behoben

- Zahlen in Maßausdrücken verlieren keine Nachkommastellen mehr (bisher 6 signifikante Stellen).
- Muster setzen den Body-Tip; Raster liegen wie bei FreeCADs MultiTransform im Body, nur das Muster ist sichtbar.
- Der Modellbaum zeigt den Ursprungspunkt von FreeCAD 26.3 nicht mehr als eigenes Objekt.
- `q` beendet die TUI zuverlässig; Chat-Blasen ohne schwarzen Hintergrund.

### Entwicklung

- Verschachtelbare Transaktionen für Design-Tools.
- Sprachtest `tests/server/test_language.py` für englische MCP-Ausgaben; Tool-Budget-Test ≤ 100.

## 0.1.0 — 2026-09-27

Erste Version aus Sprint `freecad-buddy-aufbau`.

### Neu

- FreeCAD-Addon „FreeCAD Buddy“ mit Bridge (JSON-RPC über `127.0.0.1`, Token, Ausführung im Qt-Hauptthread per Signal, Autostart, Workbench-Befehle).
- TUI-Server `freecad-buddy` (Textual) mit MCP über Streamable HTTP, Bearer-Token, DNS-Rebinding-Schutz, Headless-Modus.
- 32 MCP-Tools (+ `execute_python` opt-in) für Dokumente, Parameter, Bodies, Skizzen, PartDesign-Features, Selektoren, Screenshots und 3D-Druck; MCP-Prompts `design_part` und `human_modeling_guide`.
- Sketch-Engine: vollständig bestimmte Intent-Profile, Low-Level-Geometrie/Constraints, Analyse mit Lint, Fully-Constrain-Assistent ohne Block-Constraints.
- Parameter im VarSet `Parameters`; Maße als Zahl, Parametername oder Ausdruck über Parameter.
- Semantische Selektoren mit Re-Resolve nach Parameteränderungen; Fehlerkatalog mit Hinweisen.
- Druckerprofil, Druckbarkeitsprüfung und Export (STL/3MF/STEP) mit Reimport-Kontrolle.
- Referenzprojekte Box mit Deckel, Wandhalter und Drehknopf.
- `pattern` mit `kind="grid"` für 2D-Raster (MultiTransform); Muster auf Muster wird mit Hinweis abgelehnt.
- TUI mit übereinander angeordneten Bereichen für Tool-Aufrufe und Meldungen.

### Entwicklung

- `uv run poe check`: ruff, pyright, Tests im Projekt-Python (inkl. End-to-End über MCP gegen Headless-FreeCAD) und in FreeCADs Python.
- Kompatibilitätsprüfung benötigter FreeCAD-Objekttypen gegen den laufenden Build (API-Drift der Weekly-Builds).
