# Phase 3 — Sketch-Engine

> **Ziel:** Der Agent erzeugt Skizzen, die aussehen, als hätte sie ein erfahrener Mensch gezeichnet: am Ursprung verankert, voll bestimmt, mit benannten, parametrisierten Maßen und ohne Block/Lock-Krücken.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 2, Kriterien AC-04, AC-05, AC-08.

## Session-Pakete

### 📦 Session S5 — Sketch-Grundlagen ✅

Enthaltene Aufgaben: #3.1, #3.2, #3.3, #3.4

### 📦 Session S6 — Intent-Profile, Fully-Constrain-Assistent, Lint ✅

Enthaltene Aufgaben: #3.5, #3.6, #3.7

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | Alle Aufgaben umgesetzt | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #3.1 | `sketch/model.py` `create_sketch` (XY/XZ/YZ, Datum-Ebene, `face:` nur opt-in mit TNP-Warnung, Offset parametrisierbar) | — | 2026-09-27 |
| #3.2 | `sketch/lowlevel.py` `add_geometry` (line/circle/arc/point, Konstruktion), Referenzen `g<N>` | Referenzsyntax in `sketch/refs.py` | 2026-09-27 |
| #3.3 | `add_constraints` (15 Typen, benannte Maße, Wert als Zahl/Parameter/Ausdruck) | — | 2026-09-27 |
| #3.4 | `sketch/analysis.py` (DoF, Konflikte, Redundanzen, Wires, Lint); Konflikte → Rollback `sketch_invalid` | — | 2026-09-27 |
| #3.5 | `sketch/profiles.py`: rectangle (center/corner), rounded_rectangle, slot, circle, polygon, hole_rect, polyline – menschliche Constraint-Muster | Punkt auf Achse per `PointOnObject` statt 0-mm-Maß | 2026-09-27 |
| #3.6 | `sketch/assist.py` Fully-Constrain-Assistent (Koinzidenz/HV, dann einzeln geprüfte X/Y-Maße, nie Block) | — | 2026-09-27 |
| #3.7 | Lint in `analysis.lint` (Block, unbenannte Maße, ungebundene Maße, externe Geometrie) | — | 2026-09-27 |

## Geplante Abnahmeprüfungen

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| Teil von G5 / AC-04, AC-05: Skizze in der GUI öffnen → „vollständig bestimmt“, Maße benannt, Parameteränderung wirkt | offen | ausstehend (nur Nutzer) | headless belegt (`tests/core/test_sketch.py`, 18 Tests) |

## 🔄 Nächste Session

> **Einstieg:** Phase umgesetzt. Offen: Teil von G5 (`docs/acceptance.md`).
