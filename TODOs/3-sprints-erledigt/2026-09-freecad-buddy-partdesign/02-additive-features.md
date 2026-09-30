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
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #2.2 | `features.make_helix` (gemeinsamer Kern) und `features.helix(sketch, pitch, height\|turns, axis, angle, left_handed, subtractive)` → `AdditiveHelix`/`SubtractiveHelix`, Modus `pitch-height-angle` bzw. `pitch-turns-angle`, Achse wie `revolve` (Skizzen- oder Body-Achse; Datum Line folgt in #3.2); `thread.py` nutzt `make_helix`; Bridge `feature.helix`; Server-Tool `helix`; Tests: Feder (Volumen nach Pappus, folgt `Spring_Pitch`), Nut über `turns`, Ablehnungen; `thread`-Tests unverändert grün | keins | 2026-09-29 |
| #2.3 | `features.primitive(kind, dims, plane, center, offset, subtractive, body)` mit Tabelle `_PRIMITIVES` (8 Arten, Additive*/Subtractive*), Maße als Durchmesser/Ausdehnungen über `values.resolve` (Radius = Durchmesser/2 als Expression), Lage per `_attach` an Ursprungs-/Datum-Ebene mit `AttachmentOffset`-Expressions, Box um die Fußabdruck-Mitte, Wedge um 90° gedreht; `_ensure_primitive_cuts` (Primitive haben kein `Reversed`); Bridge `feature.primitive`; Server-Tool `primitive`; `plane_support` aus `sketch/model.py` (vorher privat) wiederverwendet; Tests: 8 Volumenformeln ±1 %, subtraktiver Zylinder folgt Parameter, Kugel auf Datum-Ebene mit `center`/`offset` parametrisch, Ablehnungen. Volumenhelfer liegen als `_PRIMITIVE_CASES` im Testmodul (statt conftest, nur dort gebraucht) | Primitive-Regel in 98 | 2026-09-29 |
| #2.1 | `features.loft(sketches, subtractive, ruled, closed, purpose)` → `AdditiveLoft`/`SubtractiveLoft` mit `Profile` + `Sections`; Vorprüfung: ≥ 2 Skizzen, gleicher Body, jede Skizze hat Wires (ob sie geschlossen sind, wird nicht geprüft), keine zwei aufeinanderfolgenden Skizzen auf derselben Ebene (`validation` mit Hinweis auf `datum_plane`); Härtung (Geschlossenheit, alle Paare) im Backlog-Eingang (E-39); Bridge `feature.loft`; Server-Tool `loft`; Beispiel in `gen_tool_docs`, `docs/tools.md` regeneriert (52 Tools). Tests: Trichter (Kegelstumpf-Volumen ±1 %, folgt `Funnel_Height`), subtraktiver Kegelstumpf aus dem Quader, Ablehnungen | keins | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| GUI-Anteil (Loft, Helix, Primitiv in der GUI öffnen und ändern) läuft gesammelt als AC-11 in Phase 5 | bestanden | Ralf, 2026-09-30 (G13) | AC-11/G13 am 2026-09-30 durch Ralf in der GUI bestätigt, siehe [05-regelwerk-doku-abschluss.md](05-regelwerk-doku-abschluss.md) |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0
> - Nächste Session: S3 (Phase 3, #3.1)
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/features.py` (`datum_plane`, `_attach`, `_revolve_axis`), `src/buddy_server/tools/reference.py`
> - Architektur-Deltas: Primitive-Regel in `98-architecture-update.md` (Status: in `docs/architecture.md` übernommen, #5.2)
> - Startpunkt: #3.1
