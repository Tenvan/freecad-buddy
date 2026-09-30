# Phase 3 — Replay

> **Ziel:** Ein neues Dokument aus dem Stream bis zu einem Storepoint aufbauen, über denselben Ausführungsweg wie die Aufzeichnung.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-04, AC-05, AC-06, AC-08. Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S2 (Teil) — Replay

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_bridge/registry.py` (`execute`), `addon/FreeCADBuddy/buddy_core/stream.py`, `examples/reference_projects.py`
- **Einstiegspunkt:** #3.1
- **Erfolgskriterium:** Bridge-Test: Replay bis zum letzten und bis zu einem mittleren Storepoint liefert gleiche Labels und Volumen; scheiternder Schritt bricht mit Schrittnummer ab; Einträge außerhalb der Allowlist (u. a. Python, Addon-Installation) werden übersprungen und gemeldet; `manual_edit` erzeugt eine Warnung.
- **Architektur-Relevanz:** `docs/architecture.md` (Design-Stream)
- **Architektur-Notiz:** Replay läuft in der Bridge, weil nur sie Methoden per Name kennt; Core bleibt frei von Bridge-Wissen.

Enthaltene Aufgaben: #3.1

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #3.1 | `buddy_bridge/replay.py` `replay(storepoint, into, document)`: Storepoint suchen (`not_found` mit Liste), Zielname frei (`validation`), neues Dokument, Einträge bis einschließlich Storepoint über `registry.execute` mit `document=<into>` ausführen; nur Methoden der Allowlist `REPLAYABLE` (Modellier-Methoden) ausführen, `assembly.insert_step` (`NEVER_REPLAYED`) und alles andere überspringen und melden (Allowlist seit `53e57bd`, zuvor Denylist `python.*`/`addons.install`); Warnung bei abweichender Buddy-Version; `manual_edit` → Warnung; Fehler eines Schritts → `CoreError` mit Schrittnummer, Methode, Fehler, Zieldokument bleibt; Ergebnis: Dokument, Schritte, Warnungen, Skips; Bridge-Methode `stream.replay` mit Timeout 600 s | siehe 98 | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| keine erforderlich (Headless-Tests decken die Kriterien ab) | — | — | — |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0
> - Nächste Session: S3 (Review-Gate in frischer Session, `97-review.md`, Bereich `da5701a..HEAD`)
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_bridge/replay.py`, `tests/bridge/test_stream.py`
> - Architektur-Deltas: Replay-Datenfluss in `98-architecture-update.md`, übernommen
> - Startpunkt: `git diff --name-status da5701a..HEAD` in `97-review.md` eintragen
