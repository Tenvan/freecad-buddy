# Phase 1 — Spikes & Fundament

> **Ziel:** Die beiden Unbekannten (Boolean im Baum, `ModelThread`) headless klären und die technische Basis für die neuen Typen legen, damit die Feature-Phasen ohne Überraschungen laufen.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-04, AC-08, AC-09 (Voraussetzung). Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S1 — Spikes, Fundament und `loft`

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/features.py` (`_new`, `_finish`, `_ensure_cuts`), `addon/FreeCADBuddy/buddy_core/compat.py` (`REQUIRED_TYPES`), `tests/core/test_features.py`, `tests/core/conftest.py`
- **Einstiegspunkt:** #1.1 — Spike `PartDesign::Boolean`
- **Erfolgskriterium:** OF-02 und OF-03 sind mit Messwerten unter Entscheidungen im Index eingetragen; `REQUIRED_TYPES` enthält die neuen Typen; `loft` (#2.1) ist umgesetzt und getestet.
- **Architektur-Relevanz:** `docs/architecture.md` (Kompatibilität, Modellierungsregel Boolean)
- **Architektur-Notiz:** Falls Boolean die Bodies in seine Gruppe zieht, braucht die Regel „ein Body = ein Bauteil“ eine Ausnahme oder `boolean` wird auf `fuse` beschränkt.

Enthaltene Aufgaben: #1.1, #1.2, #1.3 (dazu #2.1 aus Phase 2)

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #1.1 | Spike OF-02: `PartDesign::Boolean` headless mit zwei Bodies (fuse/cut/common). Festhalten: Wohin wandern die Bodies (`Group`, `InList`), was zeigt `get_model_tree`, was passiert mit einem Body in der Assembly4-`Parts`-Gruppe, bleibt Undo ein Schritt. Ergebnis als Entscheidung im Index | Geplant | `core` | — | — | AC-04 (Voraussetzung) |
| #1.2 | Spike OF-03: `PartDesign::Hole` mit `Threaded=True` und `ModelThread=True` (M6, M10) headless: Eigenschaft vorhanden, Solid gültig, Volumen kleiner als ohne, Rechenzeit. Ergebnis als Entscheidung im Index | Geplant | `core` | — | — | AC-08 (Voraussetzung) |
| #1.3 | `compat.REQUIRED_TYPES` um AdditiveLoft, SubtractiveLoft, AdditiveHelix, SubtractiveHelix, die 16 Primitive, Boolean, Draft, Point, CoordinateSystem erweitern; `test_compat.py` anpassen; Testhelfer für Volumenformeln (Kugel, Kegel, Torus, Ellipsoid, Keil) in `tests/core/conftest.py` | Geplant | `core` | — | — | AC-09; technische Voraussetzung für #2.1 bis #4.2 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| keine erforderlich (nur Headless-Spikes und Tests) | — | — | — |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 3
> - Nächste Session: S1
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/features.py`, `addon/FreeCADBuddy/buddy_core/compat.py`, `tests/core/conftest.py`
> - Architektur-Deltas: Ergebnis der Spikes in `98-architecture-update.md` ergänzen
> - Startpunkt: #1.1
