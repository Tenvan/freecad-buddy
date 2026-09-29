# Phase 4 — Boolean & Draft

> **Ziel:** `boolean` zwischen Bodies gemäß Spike-Ergebnis OF-02 und `draft` als Dress-up mit Selektor.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-04, AC-05. Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S4 — `boolean` und `draft`

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/features.py` (`_dress_up`, `fillet`), `addon/FreeCADBuddy/buddy_core/select.py` (`SELECTOR_PROPERTY`), `addon/FreeCADBuddy/buddy_core/assembly.py` (`Parts`-Gruppe), Spike-Ergebnis #1.1 im Index
- **Einstiegspunkt:** #4.1
- **Erfolgskriterium:** Beide Tools mit grünen Core-Tests; Boolean-Verhalten im Baum entspricht der Entscheidung aus dem Spike.
- **Architektur-Relevanz:** `docs/architecture.md` (Modellierungsregel Boolean)
- **Architektur-Notiz:** Boolean verbindet nur Bodies desselben Bauteils; die Regel kommt ins Regelwerk (#5.1) und in die Architektur-Doku.

Enthaltene Aufgaben: #4.1, #4.2

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #4.1 | `features.boolean(body, op=fuse\|cut\|common, bodies[], name)` → `PartDesign::Boolean` (`Type`, `Group`); Ablehnung: Body aus Assembly-`Parts`, Body = Ziel, unbekannter Body; `get_model_tree` zeigt das Ergebnis lesbar; Bridge `feature.boolean`; Server-Tool `boolean`; Tests: fuse/cut/common mit Volumenprüfung, Ablehnungen, Undo ein Schritt | Geplant | `core`, `bridge`, `server` | #1.1 | — | AC-04 |
| #4.2 | `features.draft(body, selector, angle, neutral_plane, pull_direction, reversed, name)` → `PartDesign::Draft` über `_dress_up` mit gespeichertem Selektor; Bridge `feature.draft`; Server-Tool `draft`; Tests: Winkel als Parameter, Re-Resolve nach Parameteränderung, Selektor ohne Treffer → Fehler mit Vorschau | Geplant | `core`, `bridge`, `server` | — | — | AC-05 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| keine erforderlich (Headless-Tests decken die Kriterien ab) | — | — | — |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 2
> - Nächste Session: S4
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/features.py`, `addon/FreeCADBuddy/buddy_core/select.py`
> - Architektur-Deltas: Boolean-Regel in `98-architecture-update.md`
> - Startpunkt: #4.1
