# Phase 3 — Sketch-Engine

> **Ziel:** Der Agent erzeugt Skizzen, die aussehen, als hätte sie ein erfahrener Mensch gezeichnet: am Ursprung verankert, voll bestimmt, mit benannten, parametrisierten Maßen und ohne Block/Lock-Krücken.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-04, AC-05, AC-08. Umsetzung nur für freigegebenen Umfang. Parameter-Ablage: VarSet (OF-02, entschieden 2026-09-27).

## Session-Pakete

### 📦 Session S5 — Sketch-Grundlagen

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/sketch/`, Sketcher-API von FreeCAD 26.3 (`Sketcher.SketchObject`, `solve()`, `getMalformedConstraints`/`Conflicting`/`Redundant`)
- **Einstiegspunkt:** #3.1 — Sketch anlegen und anhängen
- **Erfolgskriterium:** Headless-Test erzeugt eine Low-Level-Skizze, analysiert DoF/Konflikte/Redundanzen korrekt und bindet ein Maß an einen Parameter.
- **Architektur-Relevanz:** `core`
- **Architektur-Notiz:** Stabile Referenzierung von Geometrie innerhalb einer Skizze (Rückgabe-IDs + Rollen wie `edge:bottom`) statt reiner Indizes festlegen.

Enthaltene Aufgaben: #3.1, #3.2, #3.3, #3.4

### 📦 Session S6 — Intent-Profile, Fully-Constrain-Assistent, Lint

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/sketch/profiles.py`, `docs/architecture.md#modellierungsregeln`
- **Einstiegspunkt:** #3.5 — Profil-Bausteine
- **Erfolgskriterium:** Jedes Profil erzeugt eine Skizze mit DoF 0, ohne Block/Lock und mit benannten Maßen; der Lint findet absichtlich schlecht gebaute Skizzen.
- **Architektur-Relevanz:** `core`
- **Architektur-Notiz:** Katalog „menschliche Constraint-Muster“ je Profil in `docs/architecture.md` aufnehmen.

Enthaltene Aufgaben: #3.5, #3.6, #3.7

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #3.1 | `create_sketch`: im Body auf `XY/XZ/YZ` des Body-Origins, auf Datum-Ebene oder mit Offset; Face-Attachment nur mit `allow_face_attachment=true` und TNP-Warnung. Sprechendes Label. | Geplant | `core` | Phase 2 | — | AC-04, AC-08 |
| #3.2 | Low-Level-Geometrie: Linie, Polyline, Kreis, Bogen, Punkt, Konstruktionsgeometrie, externe Geometrie (Ursprungsachsen, andere Skizzen). Rückgabe: Geo-IDs + Rollen. | Geplant | `core` | #3.1 | — | AC-04 |
| #3.3 | Constraint-API: Coincident, Horizontal/Vertical, Parallel/Perpendicular, Tangent, Equal, Symmetric, PointOnObject, Distance/DistanceX/DistanceY, Radius/Diameter, Angle; Maß-Constraints immer benannt, optional mit Expression auf Parameter. | Geplant | `core` | #3.2, #2.3 | — | AC-04, AC-05 |
| #3.4 | `analyze_sketch`: DoF, konfliktbehaftete/redundante/fehlerhafte Constraints, geschlossene Wires, Selbstüberschneidung; Konflikt beim Hinzufügen → Rollback + Constraint-IDs. | Geplant | `core` | #3.3 | — | AC-04 |
| #3.5 | Intent-Profile (ein Tool `add_profile` mit Typ-Parameter): Rechteck (zentriert/eckverankert), abgerundetes Rechteck, Langloch, Kreis, regelmäßiges Polygon (Konstruktionskreis), Lochraster/-kreis, Polyline mit Bögen. Menschliche Muster: Symmetrie zum Ursprung, Equal statt Doppelmaß, Konstruktionslinien. | Geplant | `core` | #3.4 | — | AC-04, AC-05 |
| #3.6 | Fully-Constrain-Assistent: bei DoF > 0 Vorschläge (fehlende Maße, Verankerung am Ursprung/an Achsen) ausgeben und auf Wunsch anwenden; niemals Block/Lock. | Geplant | `core` | #3.4 | — | AC-04 |
| #3.7 | Skizzen-Lint (`lint_sketch` + Test-Helfer): Block/Lock, redundante Constraints, unbenannte Maße, Maße ohne Parameterbindung (Warnung), Referenzen auf instabile Topologie, fehlende Konstruktions-Markierung. | Geplant | `core` | #3.5 | — | AC-04, AC-08 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

GUI- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-04/AC-05: Eine per Profil-Tool erzeugte Skizze in der GUI öffnen → Status „vollständig bestimmt“ (grün), Maße tragen Namen; ein Maß per Doppelklick ändern → Skizze bleibt voll bestimmt | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 7
> - Nächste Session: S5
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/sketch/`
> - Architektur-Deltas: Geometrie-Referenzierung und Constraint-Muster in 98-architecture-update.md ergänzen
> - Startpunkt: #3.1
