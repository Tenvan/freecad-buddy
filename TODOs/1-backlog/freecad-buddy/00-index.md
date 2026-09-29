# Backlog — freecad-buddy

> Letzte Aktualisierung: 2026-09-29

## Übersicht

Domain-Backlog für den FreeCAD-MCP-Server. Tickets sind nach Priorität gelistet. Jedes Ticket ist eine eigene `.md`-Datei in diesem Ordner. Die Sprints [`freecad-buddy-aufbau`](../../3-sprints-erledigt/2026-09-freecad-buddy-aufbau/00-index.md) (2026-09-28) und [`freecad-buddy-design-regelwerk`](../../3-sprints-erledigt/2026-09-freecad-buddy-design-regelwerk/00-index.md) (2026-09-29, Version 0.2.0) sind abgeschlossen.

## Status-Marker

| Marker | Bedeutung |
|---|---|
| 🔴 | Kritisch / blockierend |
| 🟡 | Folgetask / Vorbereitung |
| 🔵 | In Vorbereitung für nächsten Sprint |
| ⏸️ | Pausiert |
| ✅ | Erledigt (Historie) |

## Tickets

| Status | Ticket | Pfad | Architektur-Impact | Kurzbeschreibung |
|---|---|---|---|---|
| 🔵 | PartDesign-Vollständigkeit: Loft, Helix, Primitive, Boolean, Draft, Datum | [`partdesign-vollstaendigkeit.md`](partdesign-vollstaendigkeit.md) | mehrere | In Sprint [`freecad-buddy-partdesign`](../../2-sprints-aktiv/freecad-buddy-partdesign/00-index.md) (seit 2026-09-29): 6 neue Tools plus Taper in `pad`/`pocket` und `model_thread` in `hole` (51 → 57 Tools) |
| 🟡 | Druckprüfung: Überhänge an gekrümmten Flächen und freie Brücken | [`druckpruefung-ueberhang-kruemmung.md`](druckpruefung-ueberhang-kruemmung.md) | core | Griff-Test: Überhang am runden Stab nicht erkannt (eine Normale pro Fläche) |
| ✅ | Design-Regelwerk und Design-Tool-Regel | [`design-regelwerk.md`](design-regelwerk.md) | server | Umgesetzt im Sprint `freecad-buddy-design-regelwerk` |
| ✅ | Addon-Manager-Integration (Suche, Installation) | [`addon-manager-integration.md`](addon-manager-integration.md) | mehrere | Umgesetzt im Sprint `freecad-buddy-design-regelwerk` |
| ✅ | Recherche fertige Grid-Lösung | [`grid-loesung-recherche.md`](grid-loesung-recherche.md) | keiner | Umgesetzt: kein Addon, eigenes `fill_pattern` |
| ✅ | TUI: Tool-Log als farbige Chat-Ansicht | [`tui-chat-log.md`](tui-chat-log.md) | server | Umgesetzt im Sprint `freecad-buddy-design-regelwerk` |
| 🟡 | GUI-Abnahme (Rest G2, G6, G8) | [`gui-abnahme.md`](gui-abnahme.md) | keiner | GUI bedienbar während eines Baus, 3MF im Slicer, Probedruck (optional) |

## Ideen-Parkplatz (noch keine Tickets)

Aus den Nicht-Zielen des Sprints; erst bei Bedarf als Ticket ausformulieren.

- Slicer-Integration (Orca/Prusa/Bambu-CLI): Slicen, Druckzeit/Materialschätzung zurückmelden.
- Bauteil-Bibliothek: Snap-Fits, Scharniere, Gewindeeinsätze, Schraubendome als Intent-Tools.
- Multi-Body-Projekte mit Passungen zwischen Bauteilen (ohne volle Assembly).

## Hinweise

- Tickets ohne klare Sprint-Zuordnung leben hier.
- Bei Einplanung wandert das Ticket in einen Sprint (`2-sprints-aktiv/<sprint>/`) oder wird Teil eines neuen Sprint-Plans.
- Architektur-Impact früh markieren, damit der spätere Sprint ein passendes Architektur-Update-Artefakt anlegt.
- Bei Wegfall: Ticket-Datei löschen und im Index entfernen.
