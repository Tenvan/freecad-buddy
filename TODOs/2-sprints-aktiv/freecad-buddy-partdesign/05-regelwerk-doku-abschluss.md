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
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #5.1 | Regelwerk: Thema `features` um fünf Regeln (loft, helix + model_thread, primitive, draft/taper/up_to_first, boolean) und Thema `references` um die Datum-Regel erweitert, jeweils mit `requires`; Tests `test_rules_only_name_registered_tools`, `test_every_topic_of_r03_is_covered`, `test_language.py` grün | keins | 2026-09-29 |
| #5.2 | `docs/tools.md` regeneriert (57 Tools); `docs/architecture.md` mit allen sieben Deltas aus 98; README (57 Tools, PartDesign-Abdeckung); `CHANGELOG.md` 0.3.0; Version 0.3.0 in `pyproject.toml`, `uv.lock`, Server, Bridge, Core; `docs/acceptance.md` um G13 ergänzt | in `docs/architecture.md` übernommen (98) | 2026-09-29 |
| #5.4 | GUI-Abnahme AC-11 = G13 bestanden (Nachweis in der Tabelle unten) | keins | 2026-09-30 |
| #5.3 | Gesamtcheck `uv run poe check` grün (siehe Session-Log S5); jedes neue Tool ist ein Undo-Schritt (Core-Tests nutzen `documents.undo` gegen `boolean`, `hole`, `draft`), Labels nach Konvention (`Loft_`, `Helix_`, `HelixCut_`, `<Primitive>_`/`<Primitive>Cut_`, `DatumPoint_`/`DatumLine_`/`LCS_`, `Boolean_`, `Draft_`) | keins | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G13 (AC-11): Dokument mit Trichter (`loft`), Feder (`helix`) und Kugelknauf (`primitive`) über MCP bauen; in der GUI jedes Feature öffnen, einen Parameter im VarSet ändern, Recompute ohne Fehler, Skizzen weiterhin vollständig bestimmt | ✅ bestanden | Ralf im Chat, 2026-09-30 (Agent baut `Abnahme_G13` über MCP, Ralf prüft in der GUI) | Doppelklick öffnet `Loft_Funnel`, `Helix_Spring`, `Sphere_Knob` im Task-Panel; Parameter geändert (`Funnel_Height` 40 → 60, `Spring_Pitch` 5 → 3, `Knob_Diameter` 25 → 45), Recompute ohne Fehler. Nachgemessen: Loft 81 681 mm³ (Kegelstumpf h = 60), Helix 1 974 mm³ (10 Windungen), Kugel 47 713 mm³ auf XY; alle Features gültig, alle Skizzen DoF 0 (Session-Log S6) |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: keine; Sprint wartet auf das Review-Gate
> - Nächste Session: S7 (Review-Gate in frischer Session, `97-review.md`, Bereich `4fd92f8..da5701a`)
> - Relevante Dateien: `00-index.md`, `TODOs/README.md#review-gate-sprint-abnahme`
> - Architektur-Deltas: alle übernommen
> - Startpunkt: `git diff --name-status 4fd92f8..da5701a` in `97-review.md` eintragen
