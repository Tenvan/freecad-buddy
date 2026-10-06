# Backlog — freecad-buddy

> Letzte Aktualisierung: 2026-09-30

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
| ✅ | PartDesign-Vollständigkeit: Loft, Helix, Primitive, Boolean, Draft, Datum | [`partdesign-vollstaendigkeit.md`](partdesign-vollstaendigkeit.md) | mehrere | Umgesetzt im Sprint [`freecad-buddy-partdesign`](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md) (erledigt 2026-09-30, Review-Gate bestanden) |
| ✅ | Design-Stream mit Storepoints: Aufbau aufzeichnen, neu aufbauen, zurückspringen | [`design-stream-storepoints.md`](design-stream-storepoints.md) | mehrere | Umgesetzt im Sprint [`freecad-buddy-storepoints`](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md) (erledigt 2026-09-30, Review-Gate bestanden) |
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
| E-01 | 2026-09-29 | `infra` | schuld | Komplexitätsgrenze `C901` (max. 10) in ruff aktivieren, bestehende 14 Befunde als eingefrorene Baseline (Stand Review-Gate PartDesign, 2026-09-30) | Roadmap-Planung | R1 |
| E-02 | 2026-09-29 | `infra` | idee | `poe review-files`: geänderte Dateien seit dem Start-Commit des Sprints auflisten (Basis für `97-review.md`) | Roadmap-Planung | R1 |
| E-03 | 2026-09-29 | `infra` | idee | CI (GitHub Actions) für `lint`, `typecheck`, `test-tools`; `test-core` bleibt lokal (braucht FreeCAD) | Roadmap-Planung | R1 |
| E-04 | 2026-09-29 | `infra` | idee | Projekteigene `CLAUDE.md` mit Kurzfassung der Arbeitsweise, Befehlen und Schichtregeln | Roadmap-Planung | R1 |
| E-05 | 2026-09-29 | `core` | schuld | `buddy_core/features.py` hat 1025 Zeilen – in ein Paket nach Feature-Gruppen aufteilen | Roadmap-Planung | R3 |
| E-06 | 2026-09-29 | `core` | schuld | `C901`-Befunde in `core`: `fill_pattern` 20, `_add_constraint_item` 14, `_edge_filter` 13, `_face_filter` 12, `screenshot` 12, `add_fastener` 11 (`_face_filter` 11 → 12 und `tools/feature.register` 12 → 17 im Sprint PartDesign gewachsen) | `ruff --select C901` | R3 |
| E-07 | 2026-09-29 | `server` | schuld | `C901`-Befunde in `server`: `register` in `tools/rules` 19, `tools/feature` 17, `tools/assembly` 11; `payloads.compact_text` 16, `describe_result` 11; `slicer.read_result` 11 | `ruff --select C901` | R4 |
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
| E-24 | 2026-09-30 | `core` | problem | Nach `loft` bleibt die Datum-Ebene der oberen Skizze sichtbar und verdeckt die Öffnung (Trichter); nach dem Feature ausblenden wie die Skizzen | GUI-Abnahme G13 | Kandidat |
| E-25 | 2026-09-30 | `bridge` | idee | Offenes Task-Panel sperrt auch reine Lesezugriffe (`get_model_tree`, `list_storepoints`) mit `[busy_user_transaction]`; prüfen, ob Lesen ohne Transaktion erlaubt werden kann | GUI-Abnahme G13/G15 | Kandidat |
| E-26 | 2026-09-30 | `bridge` | idee | Gruppe `Storepoints` steht nach jedem Aufruf auf `Touched` (Recompute-Symbol im Baum) | GUI-Abnahme G14 | Kandidat |
| E-27 | 2026-09-30 | `infra` | idee | GUI-Testlauf: FreeCAD im GUI-Modus, Prüfungen in-process über `FreeCADGui` und Qt (`setEdit`/`Control.closeDialog`, Baum-Widget auslesen, `QTest`-Doppelklick) statt pyautogui/pywin32; automatisiert G13, G14, G15 (echte Sketcher-Transaktionen), G2 (Event-Loop-Latenz). G6/G7/G8 bleiben manuell. Spike 2026-09-30 (über `execute_python` in der laufenden GUI) trägt: G13 `setEdit` → Task-Panel aktiv → `closeDialog` für Loft/Helix/Kugel; G14 Baum-Widget liefert Spalte „Beschreibung“ = `Label2`, Tooltip leer, Marker-Icon gesetzt, Doppelklick-Handler wählt das verlinkte Feature (synthetischer `QTest.mouseDClick` im Baum unzuverlässig, deshalb am ViewProvider geprüft). Übergangsskript `tools/gui_checks.py` | Ralf, GUI-Abnahme | R1 |
| E-28 | 2026-09-30 | `server` | idee | Tool `edit_feature`: ein Feature im Task-Panel für den Nutzer öffnen (`setEdit`), z. B. zum Nachjustieren; Budget 60 → 61 | Ralf, GUI-Abnahme | Kandidat |
| E-29 | 2026-09-30 | `bridge` | problem | Scheitert `stream.record` nach einem erfolgreichen Aufruf (z. B. fremde Gruppe `BuddyStorepoints` ohne `Stream`), meldet die RPC einen Fehler, obwohl das Modell geändert ist; ein Retry baut das Feature doppelt. Aufzeichnungsfehler als Warnung im Ergebnis melden | Review-Gate Storepoints (`/code-review`) | Kandidat |
| E-30 | 2026-09-30 | `core` | schuld | Design-Stream wird bei jeder Änderung komplett geparst und neu geschrieben (O(n) je Aufruf, O(n²) je Design); geparste Einträge je Dokument cachen oder nur anhängen | Review-Gate Storepoints (`/code-review`) | Kandidat |
| E-31 | 2026-09-30 | `bridge` | schuld | Aufzeichnung und Replay über Flags an der Methoden-Registrierung (`recorded`, `replayable`, gebundene Registry) statt über die Präfixlisten `NOT_RECORDED` (Opt-out, fail-open) und `REPLAYABLE`/`NEVER_REPLAYED`; seit dem Commit-Zähler braucht `NOT_RECORDED` nur noch transaktionsbildende Methoden | Review-Gate Storepoints (`/code-review`, `/simplify`) | Kandidat |
| E-32 | 2026-09-30 | `core` | problem | `storepoint` findet das Feature über die im Stream gespeicherten Labels; nach einem Umbenennen in der GUI verlinkt der Marker still ein älteres Objekt. Über den internen Namen verknüpfen oder warnen | Review-Gate Storepoints (`/code-review`) | Kandidat |
| E-33 | 2026-09-30 | `server` | schuld | `src/buddy_server/design_rules.py` hat 436 Zeilen (395 → 429 → 436 in den Sprints PartDesign und Storepoints) – Regeln nach Themen auf Module aufteilen | Review-Gate Storepoints/PartDesign | R4 |
| E-34 | 2026-09-30 | `bridge` | idee | Zurückgestellte Spec-Punkte aus `design-stream-storepoints.md`: Replay bietet den letzten Snapshot als Fallback an (A-05); Replay prüft vor dem ersten Schritt, ob nötige Addons fehlen, statt erst beim Schritt abzubrechen | Review-Gate Storepoints | Kandidat |
| E-35 | 2026-09-30 | `core` | problem | `documents.has_unsaved_changes` erkennt Änderungen headless über `UndoCount`; bei vollem Undo-Stack (20) wächst der Zähler nicht mehr, `close` verwirft dann ungespeicherte Änderungen ohne Rückfrage. `transaction.commits` nutzen wie der Design-Stream | Review-Gate Storepoints (Reviewer) | R0a |
| E-36 | 2026-09-30 | `infra` | schuld | `C901`-Befund `tests/tools/test_addon_imports._iter_forbidden_imports` 11 fehlte in E-06/E-07/E-09 | Review-Gate Storepoints (Doku-Review) | R1 |
| E-37 | 2026-09-30 | `infra` | schuld | TODO-Doku: Statuslegende in `backlog-domain-index.template.md` weicht von der README ab (🔵, ✅); README widersprüchlich zu `master-todo.md` („Auto-Generat“) und mit Tippfehlern („gehoeren“, „Grossbuchstaben“) | Review-Gate Storepoints (Doku-Review) | Kandidat |
| E-39 | 2026-09-30 | `core` | problem | `loft`-Vorprüfung: offene Wires passieren (Meldung spricht von „closed profile“), die Ebenenprüfung vergleicht nur aufeinanderfolgende Skizzen | Review-Gate PartDesign | Kandidat |
| E-40 | 2026-09-30 | `core` | schuld | Testlücken PartDesign: alle 8 Primitive subtraktiv mit Volumen (AC-03); Revolve/Polar um eine Datum-Achse gegen die Body-Achse (AC-06); `unsupported`-Pfad von `model_thread` (Fake); `datum` mit Winkel als Parameter; `center` mit falscher Länge; Helix-Profil schneidet die Achse; `draft` ohne Treffer; Vorzeichen des `pocket`-Tapers belegen und in der Tool-Beschreibung nennen | Review-Gate PartDesign | R3 |
| E-41 | 2026-09-30 | `core` | problem | `primitive` prüft Maße nicht auf > 0 (`diameter=0` endet in „creates 2 separate solids“); Prisma mit `sides=6.5` wird still auf 6 gekürzt; unbekannte Schlüssel in `dims` (Tippfehler) werden still ignoriert | Review-Gate PartDesign | Kandidat |
| E-42 | 2026-09-30 | `core` | problem | Meldungen: disjunktes `boolean fuse` bekommt den Hinweis „The profile must touch…“; Tippfehler bei `axis` meldet nur „Object not found“ ohne erlaubte Achsen; `draft` mit LCS als `neutral_plane` scheitert erst beim Recompute | Review-Gate PartDesign | Kandidat |
| E-43 | 2026-09-30 | `core` | schuld | Lesbarkeit: `(a or b or Value(1.0))` in `features.py` (Helix); `select.py`-Docstring erklärt `vertical` nur für Kanten, Zylindermäntel fallen nicht unter `faces:vertical` | Review-Gate PartDesign | R3 |
| E-44 | 2026-09-30 | `server` | problem | Deutsche MCP-Texte in `tools/sketch.py` („Skizzen-Label“); `test_language.py` erkennt solche Beschreibungen nicht | Review-Gate PartDesign | Kandidat |
| E-45 | 2026-09-30 | `server` | schuld | `test_design_rules` akzeptiert jeden Tool-Parameternamen und Enum-Wert als bekannten Bezeichner in Regeltexten; das schwächt `test_rules_only_name_registered_tools` (z. B. `length`, `height`) – Liste gezielt statt pauschal | Review-Gate PartDesign | Kandidat |
| E-46 | 2026-09-30 | `server` | idee | Beschreibung von `create_sketch.plane` nennt den LCS (Datum-Koordinatensystem) nicht, obwohl er seit dem Sprint PartDesign erlaubt ist | Review-Gate PartDesign | Kandidat |
| E-47 | 2026-09-30 | `abnahme` | idee | Druckbarkeit von `hole(model_thread=true)` mit 0,4-mm-Düse ungeprüft (OF-03); in die GUI-Abnahme bzw. einen Probedruck aufnehmen | Review-Gate PartDesign | Kandidat |
| E-48 | 2026-09-30 | `core` | schuld | Regressionstest: `get_model_tree` listet Bodies innerhalb eines Boolean (OF-02 bisher nur im Spike belegt) | Review-Gate PartDesign | R3 |
| E-49 | 2026-09-30 | `infra` | idee | `gen_tool_docs.py` schneidet Kurzbeschreibungen in `docs/tools.md` mitten im Satz ab („funnels,“) | Review-Gate PartDesign | Kandidat |
| E-50 | 2026-09-30 | `core` | schuld | Umbau-Kandidaten aus `/simplify` (PartDesign), zusammen mit E-05: gemeinsames Gerüst für pad/pocket/revolve/sweep/loft/primitive (`first`, `before`, `_ensure_cuts`, `_finish` wie `_dress_up`); `datum_plane` über `datum`/`_attach` und `select._AXES`; deklarative Primitive-Tabelle statt `required` plus Lambdas; `values.apply(unit='int')` statt zwei Integer-Settern; `thread.py` nutzt `_attach`/`_volume`; `_volume(body.Tip) if body.Tip else 0.0` vereinfachen | Review-Gate PartDesign (`/simplify`) | R3 |
| E-51 | 2026-10-06 | `infra` | schuld | Kein Test sichert die Schichtgrenze „`buddy_server` importiert nie FreeCAD“; AST-Import-Wächter über `src/buddy_server` analog zu `tests/tools/test_addon_imports.py` ergänzen | CLAUDE.md-Audit | Kandidat |

## Hinweise

- Tickets ohne klare Sprint-Zuordnung leben hier.
- Bei Einplanung wandert das Ticket in einen Sprint (`2-sprints-aktiv/<sprint>/`) oder wird Teil eines neuen Sprint-Plans.
- Architektur-Impact früh markieren, damit der spätere Sprint ein passendes Architektur-Update-Artefakt anlegt.
- Bei Wegfall: Ticket-Datei löschen und im Index entfernen.
- Eingangszeilen, die in ein umgesetztes Ticket eingeflossen sind, beim Sprint-Abschluss löschen.
