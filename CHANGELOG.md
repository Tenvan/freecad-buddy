# Changelog

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
