# Marktanalyse — bestehende FreeCAD-MCP-Server

> Stand: 2026-09-27 │ Grundlage: README-Analyse und Code-Analyse (Sprint `freecad-buddy-aufbau`, Aufgabe #1.1)

Read-only Referenz. Nur Ideen übernehmen, keinen Code kopieren; Lizenzen beachten (überwiegend MIT, blwfish LGPL – ungeprüft im Detail).

## Übersicht

| Projekt | Architektur | Umfang | Stärken | Schwächen für unser Ziel |
|---|---|---|---|---|
| [neka-nat/freecad-mcp](https://github.com/neka-nat/freecad-mcp) | Addon in FreeCAD (XML-RPC, Port 9875) + MCP-Server | klein, generisch | Etabliert, Queue-basiertes Thread-Safety-Muster, Screenshots | Generische `create_object`/`execute_code`-Tools, kein Sketch-Konzept |
| [spkane/freecad-addon-robust-mcp-server](https://github.com/spkane/freecad-addon-robust-mcp-server) | Modi `xmlrpc`, `socket`, `embedded`; Docker; PyPI | groß (Kategorien inkl. Macros, Undo/Redo) | Robuste Verbindungsmodi, Undo/Redo-Tools, Konsolen-Output, Headless-Modus | Tool-Masse, Undo nur als Einzeltool statt Transaktion pro Aufruf |
| [JakobThiessen/FreeCad_MCP_Server](https://github.com/JakobThiessen/FreeCad_MCP_Server) | Live-FreeCAD, GUI-Updates in Echtzeit | 136 Tools, u. a. 24 Constraint-Tools | Sehr vollständige Sketcher-Constraint-Abdeckung, Messung, Capabilities-Abfrage | 1:1-API-Spiegelung → Agent muss menschliches Konstruieren selbst „wissen“ |
| [blwfish/freecad-mcp](https://github.com/blwfish/freecad-mcp) | Live-FreeCAD | 32 Tools | Unit- und Integrationstests gegen echte FreeCAD-Instanz in CI | Breiter Workbench-Fokus (CAM, Draft), wenig Druck-Bezug |
| [contextform/freecad-mcp](https://github.com/contextform/freecad-mcp) | Workbench „AICopilot“ | PartDesign 13 Ops, Part 18 Ops | Operationen gebündelt, Demo-Workflows | Python-Execution als Ausweg, Part-CSG gleichrangig |
| [sergiudanstan/freecad-mcp](https://github.com/sergiudanstan/freecad-mcp) | Node.js-Server, Fallback auf `freecadcmd` headless | 165 Tools, 15 Module | Automatischer Headless-Fallback | Node + FreeCAD-Python = zwei Stacks, extreme Tool-Masse |

## Gemeinsame Muster

- Zwei-Prozess-Architektur (Addon in FreeCAD + separater MCP-Server) ist Standard und bewährt.
- FreeCAD-API wird über Queue/Timer im GUI-Thread ausgeführt (neka-nat-Muster, von spkane übernommen).
- Screenshots nur mit GUI; Headless für Tests/Automation.

## Lücken, die wir schließen

| Lücke | Unser Ansatz | Sprint-Bezug |
|---|---|---|
| Tool-Explosion (bis 165 Tools) überfordert Tool-Auswahl des Agents | ≤ 40 Intent-Level-Tools, Low-Level als Fallback | AC-15 |
| Skizzen oft unterbestimmt, mit Lock/Block | Profile erzeugen voll bestimmte Skizzen mit menschlichen Constraint-Mustern; Lint | AC-04 |
| Maße hart kodiert | Benannte Constraints mit Expressions auf VarSet-Parameter | AC-05 |
| `Edge12`-Referenzen brechen bei Änderungen (TNP) | Semantische Selektoren mit Re-Resolve, Robustheitstests | AC-07 |
| Undo als separates Tool | Jede Mutation = eine benannte Transaktion, Rollback bei Fehler | AC-03 |
| Kein 3D-Druck-Bezug | Druckerprofil, Druckbarkeits-Check, Export mit Bettplatzierung | AC-10, AC-11 |
| `execute_python` als Normalfall | Opt-in, standardmäßig aus | AC-12 |
| Unstrukturierte Rückmeldungen | Einheitliches `ToolResult` mit DoF, Recompute-Status, Hinweisen | AC-03, AC-04 |

## Code-Erkenntnisse (#1.1, 2026-09-27)

Analysiert: neka-nat (Stand 2026-09-25), spkane (2026-09-06), JakobThiessen (2026-09-17), blwfish (2026-09-24), jeweils flacher Clone. Lizenzen: neka-nat, JakobThiessen und spkane (Code) MIT; spkane-Icons CC BY-NC-SA; **blwfish LGPL** → nur Konzepte übernehmen, keinen Code.

| Thema | Befund | Konsequenz für uns |
|---|---|---|
| Main-Thread-Dispatch | Alle nutzen Queue + `QTimer.singleShot`-Polling (50–100 ms) + `Future` mit Timeout. blwfish dokumentiert Abstürze durch Dokumenterzeugung und `reload_modules` aus dem Socket-Thread. | Gleiches Grundmuster, aber Aufwecken per Qt-Signal (`QueuedConnection`) statt Polling prüfen; nichts außerhalb des Hauptthreads anfassen. |
| Transaktionen | Nur JakobThiessen hat einen Transaktions-Kontextmanager: prüft `HasPendingTransaction` (fremde offene Transaktion), setzt `UndoMode`, stellt bei Abbruch Sichtbarkeiten wieder her. blwfish vermerkt fehlendes `openTransaction` als bekannte Lücke. | Übernommen als Konzept, erweitert um Konsolen-Mitschnitt und einheitliches `ToolResult`; `busy_user_transaction`, wenn der Nutzer gerade editiert. |
| Sketch-Analyse | `sketch.solve()` liefert einen Solver-Statuscode, **nicht** die DoF-Anzahl; maßgeblich sind `sketch.DoF` und `sketch.FullyConstrained` nach `solve()` (blwfish-Kommentar). | `analyze_sketch` liest DoF/FullyConstrained/Conflicting/Redundant nach `solve()`; in S5 gegen 26.3 verifizieren. |
| Parameter | blwfish baut Skizzen aus Spreadsheet-Parametern und hat eine VarSet-Spec; Bindung von Constraints an Expressions war dort lange ein Known Issue. | Expressions-Bindung ist Kern-Feature (AC-05), von Anfang an mit VarSet. |
| Screenshots | `view.saveImage(path, w, h, bg)` → Datei → Base64 → `ImageContent`. `saveImage` kann bei großen Szenen den GUI-Thread minutenlang blockieren; auf macOS Deadlock. | Längerer Timeout für Screenshots, Bildgröße begrenzen; Windows-only reicht für uns. |
| Konsolenmeldungen | blwfish: `execute_python` gibt FreeCAD-Konsolenwarnungen nicht zurück. | Konsolen-Observer während jedes Tool-Aufrufs, Meldungen im Ergebnis. |
| Tests | blwfish startet in CI headless `FreeCADCmd` mit Socket (AppImage-Matrix inkl. Weekly) und leert die Pipes aktiv, um Hänger zu vermeiden; Lauf ohne bestandene Tests gilt als Fehler. JakobThiessen testet Dispatcher/Transaktionen mit Mocks. | Wir testen den Core direkt in FreeCADs Python (kein Socket nötig), Bridge/Server separat; Integrationslauf gegen GUI nur mit Freigabe. |
| API-Drift | blwfish prüft Typ-Strings wie `PartDesign::Pad` gegen den laufenden Build. | Umgesetzt in `buddy_core.compat.missing_types()` mit Core-Test. |
| Sicherheit | blwfish: Auth-Token für TCP (CWE-306); neka-nat: IP-Filter. | Token + `127.0.0.1`-Bindung (AC-12). |

## Offene Punkte (verschoben)

- Sketcher-APIs für Konflikt-/Redundanzanalyse konkret gegen 26.3 prüfen → S5 (#3.4).
- Signal-basiertes Aufwecken des Hauptthreads verifizieren → S2 (#1.5).
