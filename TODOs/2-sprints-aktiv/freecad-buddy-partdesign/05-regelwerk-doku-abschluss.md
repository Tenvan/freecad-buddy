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
| #5.1 | Regelwerk-Themen `features` und `references`: neue Tools mit Einsatzregel (Loft für Übergänge, Helix für Federn und Sondergewinde, Primitive nur für Kugel/Torus/Ellipsoid/Keil und Hilfskörper, Boolean nur innerhalb eines Bauteils, Datum statt Solid-Flächen); Tests `test_rules_only_name_registered_tools`, `test_every_topic_of_r03_is_covered` | Geplant | `server` | #2.1–#4.2 | — | AC-09 |
| #5.2 | `python tools/gen_tool_docs.py` → `docs/tools.md`; `docs/architecture.md` aus 98; README-Tool-Zahl; `CHANGELOG.md`; Version (OF-05, vermutet 0.3.0) in `pyproject.toml`, Server, Bridge, Core | Geplant | `docs/architecture.md` | #5.1 | — | AC-09, AC-10 |
| #5.3 | Gesamtcheck `uv run poe check`; Stichprobe: jedes neue Tool ein Undo-Schritt, Labels nach Konvention, `test_language.py` grün | Geplant | `keine` | #5.2 | — | AC-10 |
| #5.4 | GUI-Abnahme AC-11 (Loft, Helix, Primitiv in der GUI öffnen, Parameter ändern, Recompute) – nur nach Freigabe durch Ralf; Nachweis in der Tabelle unten | Geplant | `keine` | #5.3 | — | AC-11 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G13 (AC-11): Dokument mit Trichter (`loft`), Feder (`helix`) und Kugelknauf (`primitive`) über MCP bauen; in der GUI jedes Feature öffnen, einen Parameter im VarSet ändern, Recompute ohne Fehler, Skizzen weiterhin vollständig bestimmt | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 4
> - Nächste Session: S5
> - Relevante Dateien: `src/buddy_server/design_rules.py`, `docs/architecture.md`, `CHANGELOG.md`
> - Architektur-Deltas: alle aus `98-architecture-update.md` übernehmen
> - Startpunkt: #5.1
