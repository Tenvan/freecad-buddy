# Phase 5 — Regelwerk, Doku & Abschluss

> **Ziel:** Regelwerk und Katalog auf den neuen Stand, Architektur-Doku und Version, Gesamtcheck, GUI-Abnahme AC-11 nach Freigabe.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-09, AC-10, AC-11. Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S5 — Regelwerk, Doku, Abschluss

- **Kontext-Anker:** `src/buddy_server/design_rules.py`, `tools/gen_tool_docs.py`, `docs/architecture.md`, `98-architecture-update.md`, `CHANGELOG.md`, `pyproject.toml`
- **Einstiegspunkt:** #5.1
- **Erfolgskriterium:** `uv run poe check` grün, ≤ 100 Tools, `docs/tools.md` regeneriert, Architektur-Deltas übernommen, Version gesetzt, AC-11 abgenommen oder per Scope-Entscheidung verschoben.
- **Architektur-Relevanz:** `docs/architecture.md`
- **Architektur-Notiz:** Deltas aus 98 (Primitive-Ausnahme, Boolean-Regel, Datum-Referenzen, neue `REQUIRED_TYPES`).

Enthaltene Aufgaben: #5.1, #5.2, #5.3, #5.4

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #5.4 | GUI-Abnahme AC-11 = G13 in `docs/acceptance.md` (Trichter, Feder, Kugelknauf in der GUI öffnen, Parameter ändern, Recompute) – nur nach Freigabe durch Ralf; Nachweis in der Tabelle unten | Blockiert (wartet auf Freigabe/Prüfung durch Ralf) | `keine` | #5.3 | — | AC-11 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #5.1 | Regelwerk: Thema `features` um fünf Regeln (loft, helix + model_thread, primitive, draft/taper/up_to_first, boolean) und Thema `references` um die Datum-Regel erweitert, jeweils mit `requires`; Tests `test_rules_only_name_registered_tools`, `test_every_topic_of_r03_is_covered`, `test_language.py` grün | keins | 2026-09-29 |
| #5.2 | `docs/tools.md` regeneriert (57 Tools); `docs/architecture.md` mit allen sieben Deltas aus 98; README (57 Tools, PartDesign-Abdeckung); `CHANGELOG.md` 0.3.0; Version 0.3.0 in `pyproject.toml`, `uv.lock`, Server, Bridge, Core; `docs/acceptance.md` um G13 ergänzt | in `docs/architecture.md` übernommen (98) | 2026-09-29 |
| #5.3 | Gesamtcheck `uv run poe check` grün (siehe Session-Log S5); jedes neue Tool ist ein Undo-Schritt (Core-Tests nutzen `documents.undo` gegen `boolean`, `hole`, `draft`), Labels nach Konvention (`Loft_`, `Helix_`, `HelixCut_`, `<Primitive>_`/`<Primitive>Cut_`, `DatumPoint_`/`DatumLine_`/`LCS_`, `Boolean_`, `Draft_`) | keins | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G13 (AC-11): Dokument mit Trichter (`loft`), Feder (`helix`) und Kugelknauf (`primitive`) über MCP bauen; in der GUI jedes Feature öffnen, einen Parameter im VarSet ändern, Recompute ohne Fehler, Skizzen weiterhin vollständig bestimmt | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 1 (#5.4, wartet auf Ralf)
> - Nächste Session: S6 (Abnahme und Sprint-Abschluss), erst nach Ralfs Freigabe oder Scope-Entscheidung zu G13
> - Relevante Dateien: `docs/acceptance.md` (G13), `00-index.md` (AC-11, Definition of Done)
> - Architektur-Deltas: alle übernommen
> - Startpunkt: #5.4 – Ralf fragen: G13 selbst prüfen, dem Agenten übertragen („Agent führt, ich schaue“) oder per Scope-Entscheidung in `gui-abnahme.md` verschieben
