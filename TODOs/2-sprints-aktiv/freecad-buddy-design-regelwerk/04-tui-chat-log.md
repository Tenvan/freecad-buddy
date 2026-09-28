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
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #4.1 | Die Events kommen jetzt aus einer MCP-Middleware (`calllog.ToolCallLog`) statt aus `ToolContext`. Sie sieht jeden `tools/call` mit den Originalargumenten und der fertigen Antwort, dadurch sind alle Tools abgedeckt, auch die, die der Server selbst beantwortet. `payloads.py` übernimmt maskieren (Schlüssel, bekannte Tokens, Bearer, tokenartige Strings), Bild-Platzhalter, 200 000-Zeichen-Grenze und Zusammenfassung. Die Session wird als `<clientInfo.name> #n` beschriftet | in 98 notiert | 2026-09-28 |
| #4.2 | `chat.py`: `ToolChat` (ListView) mit `CallItem` aus Anfrage- und Antwort-Blase. Die Rahmenfarbe zeigt den Zustand (läuft, ok, Warnung, Fehler), JSON wird hervorgehoben, Inhalte auf 8 Zeilen gekürzt. Enter öffnet `DetailScreen` (TextArea, `c` kopiert), `v` schaltet auf die Einzeilen-Liste um. Events werden gepuffert und einmal pro Frame angewendet, höchstens 1 000 Einträge | keins | 2026-09-28 |
| #4.3 | `--log-file` (JSONL, maskiert, Rotation ab 10 MB auf `.1`). Headless-Ausgabe zeigt `→ Anfrage` und `← Antwort`. Tests: `test_payloads.py` (5), Chat-Tests in `test_tui.py` (Farben, Detailansicht, Umschalten, Last 10 000 × 50 KB) | keins | 2026-09-28 |
| Bugfix | `q` in der TUI hing laut Ralf. Nicht reproduzierbar, weder mit offenem SSE-Stream noch mit echter TUI, Bridge und Client. Abgesichert an drei Stellen: uvicorn `timeout_graceful_shutdown=2`, `AppStatus.should_exit` beim Stop, zweites `q` erzwingt das Beenden, TUI wartet höchstens 5 s, hängende Threads werden nach 2 s genannt und der Prozess endet trotzdem. Tests: `test_stop_finishes_quickly_while_a_client_holds_the_sse_stream`, `test_q_exits_promptly_with_real_server_and_client`, `test_cli_exits_even_if_a_thread_is_stuck` | keins | 2026-09-28 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G11 (AC-14): Referenzprojekt bauen lassen und dabei den Chat-Log ansehen; Detailansicht eines großen Ergebnisses öffnen | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0 (S2 erledigt)
> - Nächste Session: S3 (Phase 2, Addon-Manager)
> - Relevante Dateien: `src/buddy_server/events.py`, `src/buddy_server/tui.py`, `src/buddy_server/tools.py`
> - Architektur-Deltas: Payload-Aufbereitung im EventBus
> - Startpunkt: #2.1 in `02-addon-manager.md`
