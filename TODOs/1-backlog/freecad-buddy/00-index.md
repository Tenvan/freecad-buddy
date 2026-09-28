# Backlog — freecad-buddy

> Letzte Aktualisierung: 2026-09-28

## Übersicht

Domain-Backlog für den FreeCAD-MCP-Server. Tickets sind nach Priorität gelistet. Jedes Ticket ist eine eigene `.md`-Datei in diesem Ordner. Der Aufbau-Sprint [`freecad-buddy-aufbau`](../../3-sprints-erledigt/2026-09-freecad-buddy-aufbau/00-index.md) ist abgeschlossen (2026-09-28).

## Status-Marker

| Marker | Bedeutung |
|---|---|
| 🔴 | Kritisch / blockierend |
| 🟡 | Folgetask / Vorbereitung |
| 🔵 | In Vorbereitung für nächsten Sprint |
| ⏸️ | Pausiert |

## Tickets

| Status | Ticket | Pfad | Architektur-Impact | Kurzbeschreibung |
|---|---|---|---|---|
| 🟡 | Druckprüfung: Überhänge an gekrümmten Flächen und freie Brücken | [`druckpruefung-ueberhang-kruemmung.md`](druckpruefung-ueberhang-kruemmung.md) | core | Griff-Test: Überhang am runden Stab nicht erkannt (eine Normale pro Fläche) |
| 🔵 | Design-Regelwerk und Design-Tool-Regel | [`design-regelwerk.md`](design-regelwerk.md) | server | Eingeplant im Sprint `freecad-buddy-design-regelwerk` |
| 🔵 | Addon-Manager-Integration (Suche, Installation) | [`addon-manager-integration.md`](addon-manager-integration.md) | mehrere | Eingeplant im Sprint `freecad-buddy-design-regelwerk` |
| 🔵 | Recherche fertige Grid-Lösung | [`grid-loesung-recherche.md`](grid-loesung-recherche.md) | keiner | Eingeplant im Sprint `freecad-buddy-design-regelwerk` |
| 🔵 | TUI: Tool-Log als farbige Chat-Ansicht | [`tui-chat-log.md`](tui-chat-log.md) | server | Eingeplant im Sprint `freecad-buddy-design-regelwerk` (Phase 4) |
| 🔵 | GUI-Abnahme FreeCAD Buddy 0.1.0 (G1–G8) | [`gui-abnahme.md`](gui-abnahme.md) | keiner | Eingeplant im Sprint `freecad-buddy-design-regelwerk` (Phase 5) |

## Ideen-Parkplatz (noch keine Tickets)

Aus den Nicht-Zielen des Sprints; erst bei Bedarf als Ticket ausformulieren.

- Slicer-Integration (Orca/Prusa/Bambu-CLI): Slicen, Druckzeit/Materialschätzung zurückmelden.
- Bauteil-Bibliothek: Snap-Fits, Scharniere, Gewindeeinsätze, Schraubendome als Intent-Tools.
- Multi-Body-Projekte mit Passungen zwischen Bauteilen (ohne volle Assembly).
- Veröffentlichung als FreeCAD-Addon (Addon-Manager).

## Hinweise

- Tickets ohne klare Sprint-Zuordnung leben hier.
- Bei Einplanung wandert das Ticket in einen Sprint (`2-sprints-aktiv/<sprint>/`) oder wird Teil eines neuen Sprint-Plans.
- Architektur-Impact früh markieren, damit der spätere Sprint ein passendes Architektur-Update-Artefakt anlegt.
- Bei Wegfall: Ticket-Datei löschen und im Index entfernen.
