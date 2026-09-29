# Phase 2 — Loft, Helix, Primitive

> **Ziel:** Die drei fehlenden additiven/subtraktiven Feature-Familien als Tools `loft`, `helix` und `primitive` mit Bridge-Methode, Server-Tool und Headless-Core-Test.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-01, AC-02, AC-03. Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S1 (Teil) — `loft`

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/features.py` (`sweep` als Muster für Profil + zweite Skizze), `addon/FreeCADBuddy/buddy_bridge/methods.py`, `src/buddy_server/tools/feature.py`
- **Einstiegspunkt:** #2.1
- **Erfolgskriterium:** Trichter-Test grün, Parameteränderung folgt, subtraktiver Loft schneidet.
- **Architektur-Relevanz:** `keine`
- **Architektur-Notiz:** Loft-Profile liegen auf Ursprungs- oder Datum-Ebenen; keine neue Regel.

Enthaltene Aufgaben: #2.1

### 📦 Session S2 — `helix` und `primitive`

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/thread.py` (bestehende SubtractiveHelix), `addon/FreeCADBuddy/buddy_core/features.py` (`_revolve_axis`, `datum_plane`), `tests/core/test_assembly_material_thread.py`
- **Einstiegspunkt:** #2.2
- **Erfolgskriterium:** Feder und Nut per `helix`, bestehende `thread`-Tests grün; acht Primitive additiv und subtraktiv mit Volumenprüfung.
- **Architektur-Relevanz:** `docs/architecture.md` (Modellierungsregel: Primitive als Ausnahme von „Skizze zuerst“)
- **Architektur-Notiz:** Lage der Primitive über `AttachmentOffset` mit Ausdrücken; falls das nicht parametrisch geht, Lage über Datum-Ebene mit Offset-Parameter.

Enthaltene Aufgaben: #2.2, #2.3

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #2.1 | `features.loft(body, sketches[], subtractive, ruled, closed, name)` → `PartDesign::AdditiveLoft`/`SubtractiveLoft` (`Profile` + `Sections`); Bridge `feature.loft`; Server-Tool `loft`; Tests: Trichter aus zwei Kreisen (XY + `datum_plane` mit Parameter), Parameterfolge, subtraktiv, `validation` bei < 2 Skizzen | Geplant | `core`, `bridge`, `server` | #1.3 | — | AC-01 |
| #2.2 | `features.helix(body, sketch, axis, pitch, height\|turns, angle, left_handed, subtractive, name)` → `PartDesign::AdditiveHelix`/`SubtractiveHelix`; `thread.py` ruft den gemeinsamen Kern; Bridge `feature.helix`; Server-Tool `helix`; Tests: Feder (Windungen aus pitch/height), Nut, Achse als Datum Line (nach #3.1 nachziehen), Ablehnung pitch ≤ 0, bestehende `thread`-Tests | Geplant | `core`, `bridge`, `server` | #1.3 | — | AC-02 |
| #2.3 | `features.primitive(body, kind, dims{}, plane, center, offset, subtractive, name)` mit Tabelle `kind → (Additive*, Subtractive*)` für box, cylinder, sphere, cone, torus, ellipsoid, prism, wedge; Maße als Parameter/Ausdruck; Lage per Attachment an Ursprungs-/Datum-Ebene; Bridge `feature.primitive`; Server-Tool `primitive`; Tests: 8 × additiv mit Volumenformel ±1 %, 8 × subtraktiv aus einem Pad, Warnung wenn nichts geschnitten | Geplant | `core`, `bridge`, `server` | #1.3 | — | AC-03 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| GUI-Anteil (Loft, Helix, Primitiv in der GUI öffnen und ändern) läuft gesammelt als AC-11 in Phase 5 | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 3
> - Nächste Session: S1 (#2.1), danach S2
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/features.py`, `addon/FreeCADBuddy/buddy_core/thread.py`, `src/buddy_server/tools/feature.py`
> - Architektur-Deltas: Primitive-Regel in `98-architecture-update.md`
> - Startpunkt: #2.1
