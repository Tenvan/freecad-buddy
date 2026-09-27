# Phase 2 — Dokument-Kern & Feedback

> **Ziel:** Dokumente, Bodies und Parameter sind per Tool verwaltbar; jede Mutation ist atomar, rückgängig machbar und liefert strukturierte Rückmeldung inklusive Screenshot.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-03, AC-05, AC-08, AC-09. Umsetzung nur für freigegebenen Umfang.

## Session-Pakete

### 📦 Session S4 — Dokument, Body, Parameter, Transaktionen, Screenshot

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/`, `docs/architecture.md`
- **Einstiegspunkt:** #2.2 — Transaktions-Wrapper (Basis für alle weiteren mutierenden Tools)
- **Erfolgskriterium:** Headless-Tests belegen einen Undo-Eintrag pro Tool und Rollback bei Fehler; Parameter im VarSet steuern ein Testmaß; Screenshot kommt als Image im Client an.
- **Architektur-Relevanz:** `core`
- **Architektur-Notiz:** Einheitliches Ergebnisobjekt (`ToolResult`: created/modified/warnings/dof/recompute/hints) als Vertrag festhalten.

Enthaltene Aufgaben: #2.1, #2.2, #2.3, #2.4, #2.5

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #2.1 | Dokument-/Body-Tools: `new_document`, `open_document`, `save_document`, `create_body`, `get_model_tree` (inkl. Status gültig/fehlerhaft/touched, Tip, Sichtbarkeit), `get_object`. Liest immer den Live-Zustand (keine Caches). | Geplant | `core` | Phase 1 | — | AC-08 (Voraussetzung) |
| #2.2 | Transaktions-Decorator im Core: `openTransaction(<Toolname: Kurzbeschreibung>)` → Ausführung → Recompute → `commitTransaction`; bei Exception `abortTransaction` und strukturierter Fehler. Einheitliches `ToolResult`. | Geplant | `core` | Phase 1 | — | AC-03 |
| #2.3 | Parameter: VarSet `Parameters` anlegen, `set_parameters` (typisiert: Länge, Winkel, Anzahl, Bool), `list_parameters`, Expressions-Helfer für spätere Constraints/Features (OF-02). | Geplant | `core` | #2.2 | — | AC-05 |
| #2.4 | Feedback: `screenshot` (aktuelle Ansicht, iso/front/top/…, fit, optional Objekt isolieren, Größe) als PNG-Image-Content; `get_recompute_report` (Fehler/Warnungen je Objekt). Headless: klarer Hinweis „nur mit GUI“. | Geplant | `mehrere` | #2.1 | — | AC-09 |
| #2.5 | Namenskonvention im Core: Label-Generator (`<Typ>_<Zweck>`, ASCII, eindeutig), Lint-Funktion über den Modellbaum als Test-Helfer (OF-06). | Geplant | `core` | #2.1 | — | AC-08 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

GUI- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-03/AC-09: In der GUI nach einem Tool-Call `Bearbeiten → Rückgängig` → genau ein Schritt mit sprechendem Namen; `screenshot` zeigt die aktuelle Ansicht | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 5
> - Nächste Session: S4
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/`, `docs/architecture.md`
> - Architektur-Deltas: `ToolResult`-Vertrag in 98-architecture-update.md ergänzen
> - Startpunkt: #2.2
