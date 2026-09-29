# Phase 3 — Datum & Bestandserweiterungen

> **Ziel:** Datum Point, Line und LCS als Tool `datum`, Achsen über Datum Line in `revolve`, `pattern` und `helix`, dazu Taper und `up_to_first` in `pad`/`pocket` und `model_thread` in `hole`.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-06, AC-07, AC-08. Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S3 — Datum, Achsen, Taper, Innengewinde

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/features.py` (`datum_plane`, `_revolve_axis`, `pad`, `pocket`, `hole`), `addon/FreeCADBuddy/buddy_core/sketch/external.py` (`DATUM_TYPES`), `src/buddy_server/tools/reference.py`, `tests/core/test_binder_hole.py`
- **Einstiegspunkt:** #3.1
- **Erfolgskriterium:** Alle vier Aufgaben mit grünen Core-Tests; Spike-Ergebnis OF-03 umgesetzt.
- **Architektur-Relevanz:** `docs/architecture.md` (Referenzen: Datum Point/Line/LCS als stabile Basen)
- **Architektur-Notiz:** Datum-Objekte sind wie `datum_plane` die einzigen erlaubten Nicht-Ursprungs-Referenzen; Solid-Flächen bleiben tabu.

Enthaltene Aufgaben: #3.1, #3.2, #3.3, #3.4

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #3.1 | `features.datum(body, kind=point\|line\|lcs, base, offset[], angle, name)` → `PartDesign::Point`/`Line`/`CoordinateSystem` mit `AttachmentOffset` aus Parametern; Bridge `reference.datum`; Server-Tool `datum` in `tools/reference.py`; Tests: Lage folgt Parametern, `get_model_tree` zeigt die Datums | Geplant | `core`, `bridge`, `server` | — | — | AC-06 |
| #3.2 | `_revolve_axis`, `pattern kind=polar` und `helix` akzeptieren eine Datum Line als `axis`; `create_sketch` akzeptiert einen LCS als Basis; Tests: Revolve/Polar um Datum Line auf der Body-Achse = Ergebnis um Body-Achse (Volumen, Bounding-Box) | Geplant | `core` | #3.1 | — | AC-06 |
| #3.3 | `pad`/`pocket`: Parameter `taper` (→ `TaperAngle`, bei `two_sides` auch `TaperAngle2`) und Modus `up_to_first`; Tests: Volumen eines getaperten Pads gegen Pyramidenstumpf-Formel, `up_to_first` stoppt an der nächsten Fläche | Geplant | `core`, `server` | — | — | AC-07 |
| #3.4 | `hole`: Option `model_thread` (nur mit `threaded=true`) → `ModelThread`; ohne Eigenschaft im Build `unsupported`; Regel: ab M5 sinnvoll; Tests: Volumen kleiner als ohne, Solid gültig, Fehlerpfade | Geplant | `core`, `server` | #1.2 | — | AC-08 |

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
> - Offene Aufgaben: 4
> - Nächste Session: S3
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/features.py`, `src/buddy_server/tools/reference.py`, `src/buddy_server/tools/feature.py`
> - Architektur-Deltas: Datum-Referenzregel in `98-architecture-update.md`
> - Startpunkt: #3.1
