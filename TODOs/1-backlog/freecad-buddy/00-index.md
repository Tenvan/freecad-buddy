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
| 🔵 | Design-Stream mit Storepoints: Aufbau aufzeichnen, neu aufbauen, zurückspringen | [`design-stream-storepoints.md`](design-stream-storepoints.md) | mehrere | In Sprint [`freecad-buddy-storepoints`](../../2-sprints-aktiv/freecad-buddy-storepoints/00-index.md) (seit 2026-09-29): Stream im Dokument, `storepoint`/`list_storepoints`/`replay` umgesetzt, GUI-Abnahme offen |
| 🟡 | Druckprüfung: Überhänge an gekrümmten Flächen und freie Brücken | [`druckpruefung-ueberhang-kruemmung.md`](druckpruefung-ueberhang-kruemmung.md) | core | Griff-Test: Überhang am runden Stab nicht erkannt (eine Normale pro Fläche) |
| ✅ | Design-Regelwerk und Design-Tool-Regel | [`design-regelwerk.md`](design-regelwerk.md) | server | Umgesetzt im Sprint `freecad-buddy-design-regelwerk` |
| ✅ | Addon-Manager-Integration (Suche, Installation) | [`addon-manager-integration.md`](addon-manager-integration.md) | mehrere | Umgesetzt im Sprint `freecad-buddy-design-regelwerk` |
| ✅ | Recherche fertige Grid-Lösung | [`grid-loesung-recherche.md`](grid-loesung-recherche.md) | keiner | Umgesetzt: kein Addon, eigenes `fill_pattern` |
| ✅ | TUI: Tool-Log als farbige Chat-Ansicht | [`tui-chat-log.md`](tui-chat-log.md) | server | Umgesetzt im Sprint `freecad-buddy-design-regelwerk` |
| 🟡 | GUI-Abnahme (Rest G2, G6, G8) | [`gui-abnahme.md`](gui-abnahme.md) | keiner | GUI bedienbar während eines Baus, 3MF im Slicer, Probedruck (optional) |

## Eingang

Schnelle Erfassung von Ideen und Problemen ohne Spezifikation (Regeln: [README → Backlog-Eingang](../../README.md#backlog-eingang)). Triage bei jeder Sprint-Planung; Zuordnung zur Roadmap in [`roadmap.md`](../../roadmap.md).

| ID | Datum | Domäne | Typ | Beschreibung | Quelle | Roadmap |
|---|---|---|---|---|---|---|
| E-01 | 2026-09-29 | `infra` | schuld | Komplexitätsgrenze `C901` (max. 10) in ruff aktivieren, bestehende 18 Befunde als eingefrorene Baseline | Roadmap-Planung | R1 |
| E-02 | 2026-09-29 | `infra` | idee | `poe review-files`: geänderte Dateien seit dem Start-Commit des Sprints auflisten (Basis für `97-review.md`) | Roadmap-Planung | R1 |
| E-03 | 2026-09-29 | `infra` | idee | CI (GitHub Actions) für `lint`, `typecheck`, `test-tools`; `test-core` bleibt lokal (braucht FreeCAD) | Roadmap-Planung | R1 |
| E-04 | 2026-09-29 | `infra` | idee | Projekteigene `CLAUDE.md` mit Kurzfassung der Arbeitsweise, Befehlen und Schichtregeln | Roadmap-Planung | R1 |
| E-05 | 2026-09-29 | `core` | schuld | `buddy_core/features.py` hat 1025 Zeilen – in ein Paket nach Feature-Gruppen aufteilen | Roadmap-Planung | R3 |
| E-06 | 2026-09-29 | `core` | schuld | `C901`-Befunde in `core`: `fill_pattern` 20, `_add_constraint_item` 14, `_edge_filter` 13, `_face_filter` 12, `screenshot` 12, `add_fastener` 11, `loft` 11, `_primitive_props` 11 | `ruff --select C901` | R3 |
| E-07 | 2026-09-29 | `server` | schuld | `C901`-Befunde in `server`: `register` in `tools/rules` 19, `tools/feature` 17, `tools/session` 13, `tools/assembly` 11; `payloads.compact_text` 16, `describe_result` 11; `slicer.read_result` 11 | `ruff --select C901` | R4 |
| E-08 | 2026-09-29 | `bridge` | schuld | `C901`-Befund `buddy_bridge/replay.replay` 12 | `ruff --select C901` | Kandidat |
| E-09 | 2026-09-29 | `tui` | schuld | `C901`-Befund `chat._flush` 12 | `ruff --select C901` | Kandidat |
| E-10 | 2026-09-29 | `core` | problem | `create_sketch(plane='XZ', offset=…)` landet mit umgekehrtem Vorzeichen (Normale −Y); Verhalten vereinheitlichen oder die tatsächliche globale Lage im Ergebnis melden | Workspace-`CLAUDE.md`, Becherschutz | R6 |
| E-11 | 2026-09-29 | `core` | problem | Lokale Achsen flächengebundener Skizzen (`face:…`) sind gedreht/gespiegelt, ohne dass das Ergebnis es sagt; Achszuordnung im Ergebnis melden | Workspace-`CLAUDE.md` | R6 |
| E-12 | 2026-09-29 | `core` | problem | `add_profile`-Koordinaten akzeptieren keine `sin()`/`cos()`-Ausdrücke, anders als `pad`/`pocket`/`datum_plane` | Workspace-`CLAUDE.md`, Becherschutz | R6 |
| E-13 | 2026-09-29 | `core` | problem | Winkeländerung per `set_parameters` erreicht bestehende Features auf einer rotierten `datum_plane` nicht (auch nicht nach Neuöffnen) | Workspace-`CLAUDE.md`, Becherschutz | R7 |
| E-14 | 2026-09-29 | `core` | problem | Ein auf 0 Pad/Pocket-Features geleerter Body lässt den Recompute der ganzen Datei hängen; nur `revert` hilft. Schutz (Ablehnen/Warnen beim Löschen des letzten Solids) nötig | Workspace-`CLAUDE.md`, Becherschutz | R7 |
| E-15 | 2026-09-29 | `core` | problem | Labels aus `add_fastener` werden beim Recompute umnummeriert (`M10-Scheibe001` → `…004`) | Workspace-`CLAUDE.md` | R7 |
| E-16 | 2026-09-29 | `regelwerk` | idee | Bewährte Kniffe aus der Workspace-`CLAUDE.md` als Regeln in `get_design_rules` übernehmen (Sweep `u_path`, Kreissegment, Muster auf Muster, Gewinde nicht spiegeln, `add_fastener` stapelt, Assembly-Koordinatenrahmen, Bohrungsstart mit Sicherheitsabstand, mehrere Profile auf flacher Fläche) | Workspace-`CLAUDE.md` | R8 |
| E-20 | 2026-09-29 | `server` | idee | Slicer-Integration (Orca/Prusa/Bambu-CLI): Slicen, Druckzeit und Material zurückmelden | früherer Ideen-Parkplatz | Kandidat |
| E-21 | 2026-09-29 | `core` | idee | Bauteil-Bibliothek: Snap-Fits, Scharniere, Gewindeeinsätze, Schraubendome als Intent-Tools | früherer Ideen-Parkplatz | Kandidat |
| E-22 | 2026-09-29 | `core` | idee | Multi-Body-Projekte mit Passungen zwischen Bauteilen (ohne volle Assembly) | früherer Ideen-Parkplatz | Kandidat |
| E-23 | 2026-09-29 | `server` | idee | Tool-Budget-Review (60 von 100 Tools): Überschneidungen finden, Zusammenlegungen prüfen | Roadmap-Planung | Kandidat |

## Hinweise

- Tickets ohne klare Sprint-Zuordnung leben hier.
- Bei Einplanung wandert das Ticket in einen Sprint (`2-sprints-aktiv/<sprint>/`) oder wird Teil eines neuen Sprint-Plans.
- Architektur-Impact früh markieren, damit der spätere Sprint ein passendes Architektur-Update-Artefakt anlegt.
- Bei Wegfall: Ticket-Datei löschen und im Index entfernen.
- Eingangszeilen, die in ein umgesetztes Ticket eingeflossen sind, beim Sprint-Abschluss löschen.
