# Phase 2 — Dokument-Kern & Feedback

> **Ziel:** Dokumente, Bodies und Parameter sind per Tool verwaltbar; jede Mutation ist atomar, rückgängig machbar und liefert strukturierte Rückmeldung inklusive Screenshot.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 2, Kriterien AC-03, AC-05, AC-08, AC-09.

## Session-Pakete

### 📦 Session S4 — Dokument, Body, Parameter, Transaktionen, Screenshot ✅

Enthaltene Aufgaben: #2.1, #2.2, #2.3, #2.4, #2.5

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | Alle Aufgaben umgesetzt; offen ist nur die GUI-Abnahme | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #2.1 | `buddy_core/documents.py` (new/open/save, Modellbaum mit DoF und Label-Lint, get_object, delete, undo), `body.py` | — | 2026-09-27 |
| #2.2 | `buddy_core/transaction.py` + `result.py` (`ToolResult`); Nutzer-Bearbeitung → `busy_user_transaction`; nur neu ungültige Objekte führen zum Rollback | Konsolen-Mitschnitt nicht möglich (kein Observer in 26.3) → Objektstatus + Fehlerkatalog | 2026-09-27 |
| #2.3 | `parameters.py` (VarSet `Parameters`, Typen length/distance/angle/integer/float/bool, Typ bleibt bei Updates), `values.py` (Zahl, Parametername, Ausdruck) | Ausdrücke über AST | 2026-09-27 |
| #2.4 | `view.py` Screenshot (GUI-only, headless `unsupported`), Server liefert PNG als Image-Content | — | 2026-09-27 |
| #2.5 | `naming.py` (`<Typ>_<Zweck>`, ASCII, eindeutig) + Label-Lint im Modellbaum | — | 2026-09-27 |

## Geplante Abnahmeprüfungen

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G3 / AC-03: Undo-Liste in der GUI zeigt genau einen benannten Schritt pro Tool | offen | ausstehend | headless belegt (`tests/core/test_documents_transactions.py`) |
| G4 / AC-09: `screenshot` zeigt die aktuelle 3D-Ansicht | offen | ausstehend | nur GUI; headless `unsupported` belegt (`tests/bridge/test_methods.py`) |

## 🔄 Nächste Session

> **Einstieg:** Phase umgesetzt. Offen: GUI-Abnahmen G3, G4 (`docs/acceptance.md`).
