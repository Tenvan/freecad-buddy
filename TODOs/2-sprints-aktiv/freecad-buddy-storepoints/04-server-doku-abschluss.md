# Phase 4 — Server, Doku & Abschluss

> **Ziel:** Die drei Tools im Katalog, Regelwerk und Architektur auf dem neuen Stand, Version, Gesamtcheck, GUI-Abnahme nach Freigabe.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-09 sowie GUI-Anteile von AC-07 und AC-10. Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S3 — Server-Tools, Doku, Abschluss

- **Kontext-Anker:** `src/buddy_server/tools/session.py`, `tools/gen_tool_docs.py`, `src/buddy_server/design_rules.py` (Thema `workflow`), `docs/architecture.md`, `CHANGELOG.md`, `docs/acceptance.md`
- **Einstiegspunkt:** #4.1
- **Erfolgskriterium:** `uv run poe check` grün, 60 Tools, Doku aktuell, Version gesetzt, GUI-Prüfungen abgenommen oder per Scope-Entscheidung verschoben.
- **Architektur-Relevanz:** `docs/architecture.md`
- **Architektur-Notiz:** Neuer Abschnitt „Design-Stream“ (Aufzeichnung in der Registry, Ablage im Dokument, Replay in der Bridge).

Enthaltene Aufgaben: #4.1, #4.2, #4.3

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #4.3 | GUI-Abnahme G14 (Marker, Beschreibung, Doppelklick) und G15 (`manual_edit` nach GUI-Änderung) nur nach Freigabe durch Ralf; `poe check` ist grün | Blockiert (wartet auf Ralf) | `keine` | #4.2 | — | AC-07/AC-10 (GUI) |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #4.1 | Server-Tools `storepoint`, `list_storepoints`, `replay` (Gruppe Session, Timeout 600 s für Replay); Bridge `stream.storepoint`, `stream.list`, `stream.replay`; Beispiele; E2E `test_storepoints_and_replay_over_mcp` | keins | 2026-09-29 |
| #4.2 | Regelwerk `workflow` + Storepoint-Regel; `docs/architecture.md` Abschnitt „Design-Stream und Storepoints“, Tool-Zahl 60; README-Zeile; `CHANGELOG.md` 0.4.0; Version 0.4.0 in `pyproject.toml`, `uv.lock`, Server, Bridge, Core; `docs/acceptance.md` G14/G15; `docs/tools.md` regeneriert | in `docs/architecture.md` übernommen (98) | 2026-09-29 |
| #4.3 (Teil) | `uv run poe check`: ruff, pyright 0 Fehler, 186 Projekt-Tests, 255 FreeCAD-Tests | keins | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G14 (AC-10 GUI): siehe Phase 2 | offen | ausstehend | ausstehend |
| G15 (AC-07 GUI): Skizze in der GUI verschieben, danach `pad` über MCP → `list_storepoints`/Stream zeigt `manual_edit`, `replay` warnt | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 1 (#4.3 GUI-Anteil, wartet auf Ralf)
> - Nächste Session: S2 (Abnahme und Sprint-Abschluss)
> - Relevante Dateien: `docs/acceptance.md` (G14, G15), `00-index.md`
> - Architektur-Deltas: alle übernommen
> - Startpunkt: #4.3 – Ralf fragen: G14/G15 selbst prüfen, dem Agenten übertragen oder verschieben
