# Architektur-Update — FreeCAD Buddy: Design-Regelwerk, Design-Tools & Addon-Suche

> Erstellt: 2026-09-28 │ Letzte Aktualisierung: 2026-09-28 │ Status: offen

## Zweck

Dieses Dokument sammelt während des Sprints stabile Architektur-Erkenntnisse. Am Sprint-Ende werden daraus gezielte Updates für `docs/architecture.md` abgeleitet.

Nicht hier sammeln: temporäre Implementierungsdetails, Debug-Notizen, reine Code-Snippets oder lokale Workarounds ohne Architekturwirkung.

## Betroffene Architektur-Dokumente

| Dokument | Status | Ziel-Dokumente |
|---|---|---|
| `docs/architecture.md` | aktualisieren | `docs/architecture.md` |

## Architektur-Deltas

| Quelle | Bereich | Erkenntnis | Ziel-Skill | Ziel-Dokument | Status |
|---|---|---|---|---|---|
| S1 | Server / Agentenführung | Das Regelwerk (`design_rules.py`) ist die einzige Quelle für Instructions, `get_design_rules`, Resource und Prompts. Regeln mit `requires` erscheinen nur bei registrierten Tools, deshalb sammelt `build_mcp` die Tool-Namen vor dem Serverstart. Profilwerte kommen über die Bridge, ohne Bridge gilt das Standardprofil | `docs/architecture.md` | `docs/architecture.md` | offen (bestätigt in S1) |
| S3 | Server + Core / Integration | Katalog-Suche und -Details im Server (`addon_catalog.py`, `addon_service.py`: eigener Cache mit SHA-256, asynchron, offline-fähig, keine AM-Preferences). Status (`addons.status`) und Installation (S4) in der Bridge unter `buddy_core/addons/`; nur dieser Adapter importiert AM-Module, abgesichert per Kompatibilitätstest | `docs/architecture.md` | `docs/architecture.md` | offen (bestätigt in S3) |
| S4 | RPC-Vertrag | Job-Muster für lang laufende Methoden: `addons.install` liefert sofort eine Job-Id, die Arbeit startet per `QTimer.singleShot` nach der Antwort, `addons.install_status` pollt. Alle übrigen Methoden bleiben synchron | `docs/architecture.md` | `docs/architecture.md` | offen (bestätigt in S4) |
| S4 | Security | Die Addon-Installation braucht ein doppeltes Opt-in (Server-Flag und FreeCAD-Einstellung, getrennt von `execute_python`) plus Bestätigung im modalen FreeCAD-Dialog. Buddy lehnt Python-Pakete, Addon-Abhängigkeiten und Git-Pflicht ab. Tests arbeiten offline mit Fixtures und Fake-Backend | `docs/architecture.md` | `docs/architecture.md` | offen (bestätigt in S4) |
| Planung | Core / Tools | Die Kategorie Design-Tools umfasst zusammengesetzte Core-Funktionen mit einer Transaktion. Sie entstehen nur im Code, Vorschläge kommen über `propose_design_tool` | `docs/architecture.md` | `docs/architecture.md` | offen (vorgeschlagen) |
| S2 | Server / EventBus | Tool-Events entstehen in der MCP-Middleware `ToolCallLog` (Protokollebene) statt in `ToolContext`, sie tragen aufbereitete Payloads (`payloads.py`: maskiert, gekürzt, Bilder ersetzt). TUI, Headless-Ausgabe und JSONL-Log lesen nur diese Daten | `docs/architecture.md` | `docs/architecture.md` | offen (bestätigt in S2) |

## Neue oder geänderte Architekturregeln

- Agentenregeln gibt es nur in `design_rules`. Keine zweite Kopie in Prompts oder Doku, stattdessen generieren oder verlinken.
- Kein Buddy-Modul außer dem Addon-Adapter importiert Module des FreeCAD-Addon-Managers.
- Geheimnisse verlassen den Server nie in Richtung Anzeige oder Log. Maskiert wird zentral vor dem EventBus.

## Veraltete oder widersprüchliche Dokumentation

| Dokument | Problem | Entscheidung |
|---|---|---|
| `docs/architecture.md` | Tool-Katalog ohne Kategorien und ohne Addon- bzw. Design-Tool-Schicht | in S6 aktualisieren |

## Abschlussprüfung

- [ ] Alle Phasen auf Architektur-Deltas geprüft.
- [ ] `99-session-log.md` auf Architektur-Erkenntnisse geprüft.
- [ ] `docs/architecture.md` aktualisiert oder bewusst unverändert gelassen.
- [ ] Keine unnötigen Code-Samples in Architektur-Doku übernommen.
