# Phase 2 — Shape-Binder & Senkungsmaße

> **Ziel:** Referenzen über Body-Grenzen laufen über ein eigenes Tool `shape_binder`; Senkungen von `hole` sind in Durchmesser, Tiefe und Winkel parametrisch.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-07, AC-08, Anteil AC-11. OF-01 entschieden (eigenes Tool, Budget 100).

## Session-Pakete

### 📦 Session S2 — `shape_binder` und `hole`-Senkungen ✅

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/binder.py` (neu), `buddy_core/features.py` (`hole`), `buddy_core/compat.py`, `buddy_bridge/methods.py`, `src/buddy_server/tools.py`, `tests/core/test_binder_hole.py`
- **Einstiegspunkt:** #2.1 — `SubShapeBinder` im Core
- **Erfolgskriterium:** AC-07 und AC-08 per Core-Test grün, Vertragstest deckt `shape_binder` ab — **erreicht**
- **Architektur-Relevanz:** `docs/architecture.md` (Tool-Katalog, Kompatibilität)
- **Architektur-Notiz:** Body-übergreifend nur über Binder; `PartDesign::SubShapeBinder` in `compat.REQUIRED_TYPES`.

Enthaltene Aufgaben: #2.1, #2.2, #2.3, #2.4

---

## ✅ Active Tasks

*Keine – alle Aufgaben der Phase erledigt (S2, 2026-09-28).*

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #2.1 | `buddy_core/binder.py`: `shape_binder(sources, body, purpose)` mit Quellen `Object`, `Object:Element`, `Body:Object[:Element]` (Element `EdgeN`/`FaceN`/`VertexN` oder `g<N>` einer Skizze), Label `Binder_<Zweck>`, synchron; Quelle im Ziel-Body → `validation` mit Hinweis auf `external`; `SubShapeBinder` in `compat.REQUIRED_TYPES`, `Binder` im Default-Label-Lint | in 98 notiert | 2026-09-28 |
| #2.2 | Bridge-Methode `feature.shape_binder`, Server-Tool `shape_binder` (englisch), Beispiel in `gen_tool_docs`, `docs/tools.md` (49 Tools); Test-Budget in `test_tool_docs.py` auf ≤ 100 | in 98 notiert | 2026-09-28 |
| #2.3 | `hole`: `cut_diameter`, `cut_depth`, `countersink_angle` (Zahl/Parameter/Ausdruck) über `HoleCutCustomValues`; Validierung vor dem Anlegen (Kombinationen) bzw. nach Durchmesserermittlung (`cut_diameter` > Bohrung), jeweils ohne Dokumentänderung | keins | 2026-09-28 |
| #2.4 | `tests/core/test_binder_hole.py`: 12 Tests (Binder folgt Kastenbreite 60 → 80 über externe Defining-Kanten, Einzelelement `g0`, 4 Fehlerfälle; Senkung parametrisch nachgeführt, Countersink-Winkel, 4 ungültige Kombinationen) | keins | 2026-09-28 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| Keine manuelle Prüfung in Phase 2 erforderlich (GUI-Sichtung gebündelt in #3.4 / AC-12) | — | — | — |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0 (Phase abgeschlossen)
> - Nächste Session: S3 ([03-regel-referenzmodell-abschluss.md](03-regel-referenzmodell-abschluss.md))
> - Startpunkt: #3.1
