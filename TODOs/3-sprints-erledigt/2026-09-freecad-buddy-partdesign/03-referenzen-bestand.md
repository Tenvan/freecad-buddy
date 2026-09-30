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
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #3.1 | `features.datum(kind, base, offset[x,y,z], angle, rotation_axis, body, purpose)` → `PartDesign::Point` (`ObjectOrigin`), `Line` (`ObjectZ`, entlang der Ebenennormalen), `CoordinateSystem` (`ObjectXY`) über `_attach` mit `AttachmentOffset`-Expressions und Winkel-Expression; Labels `DatumPoint_`, `DatumLine_`, `LCS_`; Bridge `feature.datum`; Server-Tool `datum` (Gruppe Referenzen); Beispiel; Test: Lage folgt Parametern | Datum-Referenzregel in 98 | 2026-09-29 |
| #3.2 | `_axis_reference(body, axis)`: X/Y/Z oder Datum Line desselben Bodys; genutzt von `_revolve_axis` (damit `revolve` und `helix`) und `pattern kind=polar`; `plane_support` liefert jetzt `(support, warning, map_mode)` und akzeptiert einen LCS (`ObjectXY`), `create_sketch` und `_attach` nutzen den Modus; Tests: Torus um Datum Line exakt, Helix und Polar um dieselbe Line, Skizze auf LCS, Ablehnung einer Skizze als Achse | `plane_support` als gemeinsamer Ebenen-Resolver (98) | 2026-09-29 |
| #3.3 | `pad`/`pocket`: `taper` (→ `TaperAngle`, bei `two_sides` auch `TaperAngle2`, Helfer `_apply_taper`) und Modus `up_to_first`; Server-Literale und Beschreibungen erweitert (positiver Taper = weiter zum Ende); Tests: Pad-Volumen gegen Pyramidenstumpf-Formel ±1 %, Boss mit `up_to_first` von einer Datum-Ebene bis zum Pad, Pocket `up_to_first` (Volumen) und Taper | keins | 2026-09-29 |
| #3.4 | `hole(model_thread=true)` → `ModelThread`; `validation` ohne `threaded`, `unsupported` ohne Eigenschaft im Build; Server-Parameter mit Kostenhinweis (≈ 1,5 s, 60–90 Flächen je Loch, nur Einzelgewinde); Test: modelliertes M6 entfernt mehr Volumen als kosmetisch, Solid gültig, > 20 Flächen. Nebenbei: deutsche Beschreibung `polar: Gesamtwinkel` im `pattern`-Tool auf Englisch korrigiert | Regel „nur Einzelgewinde“ in 98 (aus S1) | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| keine erforderlich (Headless-Tests decken die Kriterien ab) | — | — | — |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0
> - Nächste Session: S4 (Phase 4, #4.1)
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/features.py` (`_dress_up`, `fillet`), `addon/FreeCADBuddy/buddy_core/select.py`, `addon/FreeCADBuddy/buddy_core/assembly.py`
> - Architektur-Deltas: Datum-Referenzregel in `98-architecture-update.md` eingetragen
> - Startpunkt: #4.1
