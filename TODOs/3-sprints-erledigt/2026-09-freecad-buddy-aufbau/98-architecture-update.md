# Architektur-Update — FreeCAD Buddy: PartDesign-first für 3D-Druck

> Erstellt: 2026-09-27 │ Letzte Aktualisierung: 2026-09-27 (S10) │ Status: übernommen

## Zweck

Dieses Dokument sammelt während des Sprints stabile Architektur-Erkenntnisse. Am Sprint-Ende werden daraus gezielte Updates für `docs/architecture.md` abgeleitet (Erstanlage in S1, #1.3).

Nicht hier sammeln: temporäre Implementierungsdetails, Debug-Notizen, reine Code-Snippets oder lokale Workarounds ohne Architekturwirkung.

## Betroffene Architektur-Dokumente

| Dokument | Status | Ziel-Abschnitte |
|---|---|---|
| `docs/architecture.md` | angelegt (S1, 2026-09-27); Tool-Katalog folgt | Schichten, Prozessmodell, RPC-Vertrag, Threading, Sicherheit, Modellierungsregeln, Namenskonvention, Tool-Katalog |
| `docs/tools.md` | neu anzulegen (S9) | Tool-Katalog mit Beispielen |

## Architektur-Deltas

| Quelle | Bereich | Erkenntnis | Ziel-Dokument | Status |
|---|---|---|---|---|
| Planung 2026-09-27 | Prozessmodell | Zwei Prozesse: Bridge-Addon in FreeCAD (Stdlib-only) + MCP-Server (`uv`, stdio) | `docs/architecture.md` | übernommen (S1) |
| Planung 2026-09-27 | Schichten | `core` enthält die gesamte FreeCAD-Logik und ist headless testbar; `bridge` nur Transport; `server` ohne FreeCAD-Import | `docs/architecture.md` | übernommen (S1) |
| Planung 2026-09-27 | Integration | JSON-RPC 2.0 über TCP `127.0.0.1` (NDJSON), Token-Auth | `docs/architecture.md` | übernommen (S1), Implementierung S2 |
| Planung 2026-09-27 | Modellierung | PartDesign-first, voll bestimmte Skizzen, Parameter in VarSet, semantische Selektoren | `docs/architecture.md` | übernommen (S1) |
| S1 #1.2 | Layout | Core/Bridge unter `addon/FreeCADBuddy/` statt `src/freecad_mcp/…`, weil FreeCAD `Mod/<Addon>` in `sys.path` aufnimmt | `docs/architecture.md#repository-layout` | übernommen (S1) |
| S1 #1.4 | Tests | Core-Tests in FreeCADs `python.exe`; Umgebungsvariablen `PYTHONHOME`/`PYTHONPATH`/`VIRTUAL_ENV`/`__PYVENV_LAUNCHER__` entfernen, sonst Stdlib-Mix | `docs/architecture.md#teststrategie` | übernommen (S1) |
| S1 #1.1 | Transaktionen | `HasPendingTransaction` → `busy_user_transaction`; Konsolen-Mitschnitt im `ToolResult` | `docs/architecture.md#transaktionen-und-ergebnisvertrag` | übernommen (S1) |
| Spec-Stand 2 | Prozessmodell/Transport | MCP-Server als manuell gestartete TUI `freecad-buddy`; MCP über Streamable HTTP (`127.0.0.1:8765/mcp`) statt stdio; Server-Kern und TUI über Ereignisse entkoppelt; `--headless` | `docs/architecture.md#mcp-transport-client--server`, `#tui-textual` | übernommen (Stand 2 freigegeben) |
| Spec-Stand 2 | Sicherheit | Zwei Tokens unter `%APPDATA%\FreeCADBuddy\` (`bridge-token`, `mcp-token`); DNS-Rebinding-Schutz per `TransportSecuritySettings` | `docs/architecture.md#sicherheit` | übernommen (Stand 2 freigegeben) |
| Umbenennung 2026-09-27 | Naming | Projekt „FreeCAD Buddy“: Addon `FreeCADBuddy`, Pakete `buddy_core`/`buddy_bridge`/`buddy_server`, CLI `freecad-buddy`, Sprint `freecad-buddy-aufbau` | alle | übernommen |
| S2 #1.5 | Threading | Hauptthread-Dispatch per Qt-Signal (`QueuedConnection`), Timeout-Code `1009 gui_timeout` | `docs/architecture.md#geklärte-architekturpunkte` | übernommen |
| S3 #1.6 | Server | eigene Bearer-Middleware, `AppStatus`-Reset, Logging-Umleitung, Tool-Ereignisse über `ToolContext` | `docs/architecture.md#geklärte-architekturpunkte` | übernommen |
| S4 #2.2 | Transaktionen | Konsolen-Mitschnitt nicht möglich (kein Observer) → Objektstatus + Fehlerkatalog; nur neu ungültige Objekte führen zum Rollback | `docs/architecture.md#transaktionen-und-ergebnisvertrag` | übernommen |
| S4 #2.3 | Werte | Zahl / Parametername / Ausdruck (AST-sicher) → FreeCAD-Expression | `docs/architecture.md#maße-parameter-und-ausdrücke` | übernommen |
| S8 #4.5 | Selektoren | Grammatik inkl. Koordinaten-Filter mit Parametern; `BuddySelector` + Re-Resolve in `set_parameters` | `docs/architecture.md#semantische-selektoren` | übernommen |
| S10 #6.1 | Tool-Katalog | 32 Tools + opt-in, generierte Doku, Vertragstest Tool↔Bridge; keine MCP-Resources (würden Tools duplizieren) | `docs/architecture.md#tool-katalog`, `docs/tools.md` | übernommen |
| S1 #1.4 | Kompatibilität | `compat.missing_types()` prüft benötigte Dokumenttypen gegen den laufenden Build | `docs/architecture.md#kompatibilität-und-api-drift` | übernommen (S1) |

## Neue oder geänderte Architekturregeln

- FreeCAD-Dokumentzugriffe erfolgen ausschließlich im Qt-Hauptthread.
- Jeder mutierende Tool-Call ist genau eine FreeCAD-Transaktion; Fehler führen zum Rollback.
- Kein Client-seitiger Zustands-Cache: jedes Tool liest den Live-Zustand des Dokuments, weil der Nutzer parallel manuell arbeitet.
- Topologie-Referenzen (Kanten/Flächen) werden nur über semantische Selektoren angesprochen und bei Recompute neu aufgelöst.
- Beliebige Codeausführung ist opt-in und standardmäßig deaktiviert.

## Veraltete oder widersprüchliche Dokumentation

| Dokument | Problem | Entscheidung |
|---|---|---|
| Sprint-Phasendateien 02–06 | Kontext-Anker nannten `src/freecad_mcp/core/…` | in S1 auf `addon/FreeCADBuddy/buddy_core/…` bzw. `src/buddy_server/…` korrigiert |

## Abschlussprüfung

- [ ] Alle Phasen auf Architektur-Deltas geprüft.
- [ ] `99-session-log.md` auf Architektur-Erkenntnisse geprüft.
- [ ] `docs/architecture.md` aktualisiert oder bewusst unverändert gelassen.
- [ ] Keine unnötigen Code-Samples in Architektur-Doku übernommen.
- [ ] Neue Architektur-Dokumente im Projekt-README verlinkt.

## Abschlussnotiz

<Kurz festhalten, welche Architektur-Dokumente geändert wurden oder warum kein Update nötig war.>
