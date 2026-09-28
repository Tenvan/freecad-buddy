# Phase 5 — Doku, Release & GUI-Abnahme

> **Ziel:** Tool-Katalog, Architektur und Changelog auf dem neuen Stand, Release 0.2.0. GUI-Abnahme G1–G11 abnehmen oder per Scope-Entscheidung verschieben.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-12, AC-13 sowie übernommen `GA-AC-01` … `GA-AC-08` aus [`gui-abnahme.md`](../../1-backlog/freecad-buddy/gui-abnahme.md). Spec-Stand 1 freigegeben am 2026-09-28.

## Session-Pakete

### 📦 Session S6 — Doku, Release, Abnahme

- **Kontext-Anker:** `tools/gen_tool_docs.py`, `docs/tools.md`, `docs/architecture.md`, `docs/acceptance.md`, `README.md`, `CHANGELOG.md`, `pyproject.toml`
- **Einstiegspunkt:** #5.1 — Tool-Katalog mit Kategorien neu erzeugen
- **Erfolgskriterium:** `uv run poe check` ist grün, ≤ 40 Tools. `docs/acceptance.md` enthält G1–G11, und Ralfs Abnahmen sind dokumentiert.
- **Architektur-Relevanz:** `docs/architecture.md`
- **Architektur-Notiz:** Deltas aus `98-architecture-update.md` übernehmen.

Enthaltene Aufgaben: #5.4, #5.1, #5.2, #5.3

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #5.4 | Stand 3: alle MCP-Ausgaben auf Englisch umstellen (Instructions, Regelwerk, Prompts, Tool-/Parameterbeschreibungen, Ergebnisse, Warnungen, Hinweise, Fehler aus Server, Core und Bridge). Sprachprüf-Test (deutsche Stoppwörter und Umlaute in allen MCP-Ausgaben). OF-09 (FreeCAD-UI, TUI) vorher mit Ralf klären | Geplant | `mehrere` | Phasen 1–4 | 4 | AC-17 |
| #5.1 | `gen_tool_docs.py` um Kategorien erweitern (Modellierung, Design-Tools, Addons, Druck, Diagnose), Beispiele für neue Tools, Budgettest ≤ 40 | Geplant | `server` | Phasen 1–4 | 1 | AC-12 |
| #5.2 | `docs/architecture.md`, README (Opt-ins, `--log-file`, Chat-Log), `CHANGELOG.md` 0.2.0, Version in `pyproject.toml` und Addon (OF-06) | Geplant | `mehrere` | #5.1 | 2 | AC-12 |
| #5.3 | `docs/acceptance.md` um G9–G11 ergänzen. GUI-Abnahme G1–G11 mit Ralf nach Freigaberegel. Ergebnisse im Session-Log und im Ticket `gui-abnahme.md` | Geplant | `keine` | #5.2 | 1 (+ Ralf) | AC-13, GA-AC-01 … 08 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G1–G8 laut `docs/acceptance.md` (Teilnachweise G1/G7 im Ticket) | offen | ausstehend | ausstehend |
| G9 Addon-Installationsdialog, G10 `hole_grid`, G11 Chat-Log | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 4
> - Nächste Session: S6
> - Relevante Dateien: `docs/*`, `CHANGELOG.md`
> - Architektur-Deltas: alle aus `98-architecture-update.md` übernehmen
> - Startpunkt: #5.4 (OF-09 klären)
