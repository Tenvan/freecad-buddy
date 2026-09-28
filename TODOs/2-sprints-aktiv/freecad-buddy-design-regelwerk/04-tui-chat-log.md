# Phase 4 — TUI-Chat-Log

> **Ziel:** Das Tool-Log der TUI zeigt jeden Aufruf als farbigen Chat-Verlauf, bestehend aus Anfrage mit Argumenten und Antwort mit Ergebnis oder Fehler. Lange Inhalte sind gekürzt und in einer Detailansicht vollständig lesbar. Geheimnisse sind maskiert, optional wird ein JSONL-Log mitgeschrieben.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-14, AC-15 (R-11). Spec-Stand 1 freigegeben am 2026-09-28.

## Session-Pakete

### 📦 Session S2 — Events mit Payload, Chat-Blasen, Detailansicht, JSONL

- **Kontext-Anker:** `src/buddy_server/events.py`, `src/buddy_server/tools.py` (`ToolContext._finish`), `src/buddy_server/tui.py`, `src/buddy_server/logs.py`, `src/buddy_server/cli.py`, `tests/server/test_tui.py`
- **Einstiegspunkt:** #4.1 — Events `ToolStarted`/`ToolFinished` mit Argumenten und Antwort
- **Erfolgskriterium:** Pilot-Test zeigt Anfrage- und Antwort-Blase mit den richtigen Farben. Der Lasttest mit 10 000 × 50 KB bleibt bedienbar. Tokens erscheinen nirgends.
- **Architektur-Relevanz:** `docs/architecture.md` (Server: EventBus, TUI)
- **Architektur-Notiz:** Payloads werden einmal im Server aufbereitet (maskieren, kürzen, Bilder ersetzen) und dann an TUI, Headless-Ausgabe und JSONL verteilt. Das Rendering sieht nie Rohdaten.

Enthaltene Aufgaben: #4.1, #4.2, #4.3

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #4.1 | Neues Event `ToolStarted(call_id, name, arguments, session)`, `ToolFinished` erweitert um `result` bzw. `error` (Code, Nachricht, Hinweis). Zentrale Aufbereitung: Maskierung (Schlüssel wie token/authorization/password sowie Werte im Token-Format), Bilder als `[PNG n KB]`, Größenlimit pro Payload für die Anzeige, Volltext im Speicher begrenzt | Geplant | `server` | — | 2 | AC-14, AC-15 |
| #4.2 | Chat-Ansicht in der TUI (Textual): Anfrage-Blase (Akzentfarbe) mit Tool, Session und formatiertem JSON. Antwort-Blase grün, gelb bei Warnungen, rot bei Fehler, mit Dauer. Laufende Aufrufe mit Spinner. Syntax-Highlighting für JSON, Kürzung mit „… (+N Zeilen)“, Detailansicht per Enter bzw. Klick (Modal mit vollem JSON, kopierbar), Umschalten per `v` auf Einzeilen-Liste (OF-08), höchstens 1 000 Einträge. Virtualisierte Darstellung, falls der Lasttest das verlangt | Geplant | `server` | #4.1 | 4 | AC-14, AC-15 |
| #4.3 | Optionales JSONL-Log `--log-file` (OF-07) mit Rotation, gleiche maskierte Daten. Headless-Ausgabe (`--headless`) zeigt Anfrage und Antwort kompakt. Tests: Pilot-Snapshot, Maskierung, Bild-Platzhalter, Lasttest, JSONL-Inhalt | Geplant | `server` | #4.2 | 2 | AC-15 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G11 (AC-14): Referenzprojekt bauen lassen und dabei den Chat-Log ansehen; Detailansicht eines großen Ergebnisses öffnen | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 3
> - Nächste Session: S2
> - Relevante Dateien: `src/buddy_server/events.py`, `src/buddy_server/tui.py`, `src/buddy_server/tools.py`
> - Architektur-Deltas: Payload-Aufbereitung im EventBus
> - Startpunkt: #4.1
