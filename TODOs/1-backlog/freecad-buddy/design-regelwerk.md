# Design-Regelwerk für den MCP-Server und Design-Tool-Regel

> Erstellt: 2026-09-28 │ Status: 🔵 Eingeplant → Sprint [`freecad-buddy-design-regelwerk`](../../2-sprints-aktiv/freecad-buddy-design-regelwerk/00-index.md) │ Priorität: hoch │ Architektur-Impact: server

## Spezifikation

> Spec-Stand: 1 │ Spec-Status: Freigegeben │ Freigabe: durch Ralf im Chat, 2026-09-28 (über den Sprint-Index)

Vollständige Spezifikation, Kriterien und Aufgaben stehen im Sprint-Index (AC-01 bis AC-05). Dieses Ticket hält nur den Auftrag fest.

## Ausgangslage

Die MCP-Instructions bestehen heute aus sechs Kurzregeln (`src/buddy_server/prompts.py`). Ein belastbares Regelwerk für FreeCAD-Konstruktion und FDM-Druck fehlt. Beim Sieb der Testplatte hat sich gezeigt: Ohne Regel baut der Agent komplexe Wiederholungsaufgaben ad hoc aus Einzelschritten nach und läuft dabei in PartDesign-Grenzen (Muster auf Muster).

## Auftrag (Ralf, 2026-09-28)

- Instructions für den MCP-Server mit Design-Regelwerk für FreeCAD (MCP unterstützt Server-Instructions).
- In den Instructions generell festlegen, dass wiederkehrende komplexe Aufgaben (wie das Grid) als Design-Tool umgesetzt werden.

## Vorentscheidungen (Ralf, 2026-09-28)

- Kompakte Instructions plus vollständiges Regelwerk über das Tool `get_design_rules(topic)` und als MCP-Resource, alles aus einer Quelle.
- Design-Tool-Regel mit Vorschlagsliste: Der Agent nutzt vorhandene Design-Tools, sonst schlägt er per `propose_design_tool` ein neues vor. Umgesetzt werden Vorschläge als Buddy-Tools im Code. Erstes Beispiel: `hole_grid`.
