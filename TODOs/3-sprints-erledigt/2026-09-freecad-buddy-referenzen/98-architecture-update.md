# Architektur-Update — FreeCAD Buddy: Externe Geometrie, Shape-Binder & Layout-Skizze

> Erstellt: 2026-09-28 │ Letzte Aktualisierung: 2026-09-28 │ Status: übernommen

## Zweck

Dieses Dokument sammelt während des Sprints stabile Architektur-Erkenntnisse. Am Sprint-Ende werden daraus gezielte Updates für `docs/architecture.md` abgeleitet.

Nicht hier sammeln: temporäre Implementierungsdetails, Debug-Notizen, reine Code-Snippets oder lokale Workarounds ohne Architekturwirkung.

## Betroffene Architektur-Dokumente

| Dokument | Status | Ziel-Dokumente |
|---|---|---|
| `docs/architecture.md` | erledigt (S3) | `docs/architecture.md` (Repository-Layout, Modellierungsregeln, Kompatibilität, Tool-Katalog) |

## Architektur-Deltas

| Quelle | Bereich | Erkenntnis | Ziel-Skill | Ziel-Dokument | Status |
|---|---|---|---|---|---|
| Planung 2026-09-28 | Modellierungsregeln | Referenzmodell: Layout-Skizze als einzige Quelle für Lochbilder/Anschlussmaße; abhängige Skizzen im selben Body über externe Geometrie (`x<N>`), andere Bodies nur über `shape_binder` | `docs/architecture.md` | `docs/architecture.md#modellierungsregeln-human-style` | übernommen |
| Planung 2026-09-28 | Sketch-Referenzen | Referenznotation `g<N>` (eigene Geometrie) und `x<N>` (externe Geometrie, GeoId `-3 - N`) mit `.start/.end/.center` | `docs/architecture.md` | `docs/architecture.md` | übernommen |
| Planung 2026-09-28 | Tool-Katalog | Budget ≤ 100 Tools (Ralf); Tools nur zusammenlegen, wenn nötig oder fachlich sinnvoll | `docs/architecture.md` | `docs/architecture.md#tool-katalog` | übernommen |
| #1.1 Spike | Kompatibilität | FreeCAD 26.3: `addExternal(obj, sub[, defining])` nur positional; ungültige Elementnamen werden still ignoriert → Buddy validiert selbst; `g<N>` ↔ `EdgeN`/`VertexN` über `Shape.ElementReverseMap` (`g<N+1>;SKT`); Konstruktionsgeometrie ist nicht Teil der Skizzen-Shape und damit nicht referenzierbar; Quelle je externem Element in `ExternalGeometryExtension.Ref`; `ExternalGeo` kann nach gelöschter Quelle veraltete Einträge behalten → Zählung über `ExternalGeometry` | `docs/architecture.md` | `docs/architecture.md#kompatibilität-und-api-drift` | übernommen |
| #1.1 Spike | Modellierungsregeln | Layout-Skizze: referenzierbare Lagen müssen reale Geometrie sein (z. B. Lochkreise); Konstruktionslinien dienen nur innerhalb der Layout-Skizze | `docs/architecture.md` | `docs/architecture.md#modellierungsregeln-human-style` | übernommen |
| #2.1 | Core-Module / Kompatibilität | Neues Modul `buddy_core/binder.py` (`shape_binder`); `PartDesign::SubShapeBinder` in `compat.REQUIRED_TYPES`; Tool-Katalog 49 | `docs/architecture.md` | `docs/architecture.md#repository-layout`, `#tool-katalog` | übernommen |
| #1.3 | Core-Module | Neues Modul `buddy_core/sketch/external.py` kapselt Quellenprüfung, Element-Übersetzung, `describe` und `dangling`; `analysis` und `lowlevel` nutzen es | `docs/architecture.md` | `docs/architecture.md#repository-layout` | übernommen |

## Neue oder geänderte Architekturregeln

- Externe Referenzen zeigen nur auf Objekte im selben Body, die im Baum vor der Zielskizze liegen; Zyklen werden vor der Änderung abgelehnt.
- Body-übergreifende Bezüge laufen ausschließlich über `PartDesign::SubShapeBinder`; der Typ gehört zu `compat.REQUIRED_TYPES`.
- Bezüge auf Körperflächen/-kanten sind Opt-in und werden als TNP-Risiko gemeldet.

## Veraltete oder widersprüchliche Dokumentation

| Dokument | Problem | Entscheidung |
|---|---|---|
| `TODOs/2-sprints-aktiv/freecad-buddy-design-regelwerk/00-index.md` R-10/AC-12 | Budget ≤ 40 überholt | aktualisiert auf ≤ 100 (Spec-Stand 5, 2026-09-28) |

## Abschlussprüfung

- [x] Alle Phasen auf Architektur-Deltas geprüft.
- [x] `99-session-log.md` auf Architektur-Erkenntnisse geprüft.
- [x] `docs/architecture.md` aktualisiert oder bewusst unverändert gelassen.
- [x] Keine unnötigen Code-Samples in Architektur-Doku übernommen.
- [x] Neue Architektur-Dokumente im Projekt-README verlinkt.

## Abschlussnotiz

`docs/architecture.md` in S3 aktualisiert: Repository-Layout (Tool-Paket, `external.py`, `binder.py`), Modellierungsregeln (Layout-Skizze, Binder, Referenznotation), Kompatibilität (externe Geometrie, Hole-Senkungen), Tool-Katalog (45 Tools, Gruppen, Budget 100). Keine neuen Architektur-Dokumente.
