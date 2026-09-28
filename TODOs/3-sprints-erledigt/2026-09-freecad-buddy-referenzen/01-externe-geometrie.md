# Phase 1 — Externe Geometrie

> **Ziel:** Skizzen übernehmen Kanten, Punkte und Kreise aus anderen Skizzen, Datums und Bindern desselben Bodys als externe Geometrie und constrainen darauf mit `x<N>`.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-01 bis AC-06. #1.1 (Spike) war vorbereitende Klärung für OF-02.

## Session-Pakete

### 📦 Session S1 — Spike und `external` im Core ✅

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/sketch/refs.py`, `sketch/external.py` (neu), `sketch/lowlevel.py`, `sketch/analysis.py`, `tests/core/test_sketch_external.py`
- **Einstiegspunkt:** #1.1 — Spike gegen FreeCAD 26.3 headless
- **Erfolgskriterium:** Core-Tests für AC-01 bis AC-06 grün; Spike-Ergebnis in `98-architecture-update.md` — **erreicht**
- **Architektur-Relevanz:** `docs/architecture.md` (Modellierungsregeln, Kompatibilität)
- **Architektur-Notiz:** Referenzmodell `g<N>`/`x<N>` und Abbildung `g<N>` → `EdgeN` über die ElementMap.

Enthaltene Aufgaben: #1.1, #1.2, #1.3, #1.4, #1.5

---

## ✅ Active Tasks

*Keine – alle Aufgaben der Phase erledigt (S1, 2026-09-28).*

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #1.1 | Spike FreeCAD 26.3 (drei Skripte headless). Ergebnisse: Konstruktionsgeometrie steckt nicht in der Skizzen-Shape → nicht referenzierbar (**OF-02 geklärt**); falsche Elementnamen ignoriert FreeCAD still; `g<N>` ↔ `EdgeN` über `Shape.ElementReverseMap` (`g<N+1>;SKT`); `x<N>`-Reihenfolge = Hinzufüge-Reihenfolge, Quelle je Element in `ExternalGeometryExtension.Ref`; `defining` nur als 3. Positionsargument; Zyklen und fremde Bodies lehnt FreeCAD ab; gelöschte Quelle hinterlässt hängende Constraints bei formal gültiger Skizze; `SubShapeBinder` synchron und extern referenzierbar; `hole`: `HoleCutCustomValues` + `HoleCutDiameter`/`HoleCutDepth`/`HoleCutCountersinkAngle`, Expressions funktionieren | in 98 notiert | 2026-09-28 |
| #1.2 | `refs`: `x<N>[.start\|end\|center]` ↔ GeoId `-3-N`, Helper `position()`, englische Fehler | in 98 notiert | 2026-09-28 |
| #1.3 | Neues Modul `buddy_core/sketch/external.py`; `add_geometry` Typ `external` (Quelle prüfen inkl. Kandidatenliste, Elemente übersetzen/validieren, Duplikate wiederverwenden, `defining`, `allow_face_reference` mit Warnung); Server-Beschreibungen von `add_geometry`/`add_constraints`/`analyze_sketch` englisch; `docs/tools.md` neu generiert | in 98 notiert | 2026-09-28 |
| #1.4 | `analyze_sketch`: Feld `external` (`ref`, `source`, `element`, `defining`), Lint `info` (Skizze/Datum/Binder) bzw. `warning` (Körper), `error` für hängende Constraints; `fully_constrain_sketch` kompatibel (Test) | keins | 2026-09-28 |
| #1.5 | `tests/core/test_sketch_external.py`: 16 Tests für AC-01…AC-06 | keins | 2026-09-28 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| Keine manuelle Prüfung in Phase 1 erforderlich (GUI-Sichtung gebündelt in #3.4 / AC-12) | — | — | — |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0 (Phase abgeschlossen)
> - Nächste Session: S2 ([02-binder-und-hole.md](02-binder-und-hole.md))
> - Architektur-Deltas: in `98-architecture-update.md` eingetragen
> - Startpunkt: #2.1
