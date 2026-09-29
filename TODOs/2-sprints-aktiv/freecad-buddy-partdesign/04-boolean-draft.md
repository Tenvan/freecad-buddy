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
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #4.1 | `features.boolean(op, bodies, body, purpose)` → `PartDesign::Boolean` mit `Type` und `addObjects`; Ablehnungen: unbekannter `op`, leere Liste, Ziel ohne Geometrie, Body = Ziel, Body ohne Geometrie, Body in Assembly-`Parts`, bereits verbrauchter Body; Ergebnis nennt die Bodies und einen Hinweis, wo sie jetzt liegen; Bridge `feature.boolean`; Server-Tool `boolean`; Beispiel; Tests: cut/fuse/common mit Volumen, Undo stellt den Werkzeug-Body als Root wieder her, Ablehnungen inkl. Assembly | Boolean-Regel in 98 bestätigt | 2026-09-29 |
| #4.2 | `features.draft(selector, angle, neutral_plane, reversed, body, purpose)` über `_dress_up` (Selektor gespeichert, Re-Resolve über `refresh_references`); Neutral Plane über `plane_support` (Standard XY); `pull_direction` weggelassen, weil die Neutral Plane die Richtung bereits eindeutig macht (Spike); neuer Face-Selektor `faces:vertical` in `select.py` und `SELECTOR_HELP`; Bridge `feature.draft`; Server-Tool `draft`; Beispiel; Test: Narrowing-Formel ±1 %, Parameteränderung folgt, `reversed` = Widening | `faces:vertical` als Selektor (98) | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| keine erforderlich (Headless-Tests decken die Kriterien ab) | — | — | — |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0
> - Nächste Session: S5 (Phase 5, #5.1)
> - Relevante Dateien: `src/buddy_server/design_rules.py`, `docs/architecture.md`, `CHANGELOG.md`
> - Architektur-Deltas: Boolean-Regel und `faces:vertical` in `98-architecture-update.md` eingetragen
> - Startpunkt: #5.1
