# Architektur-Update — FreeCAD Buddy: PartDesign-Vollständigkeit

> Erstellt: 2026-09-29 │ Letzte Aktualisierung: 2026-09-29 (S5) │ Status: übernommen

## Zweck

Dieses Dokument sammelt während des Sprints stabile Architektur-Erkenntnisse. Am Sprint-Ende werden daraus gezielte Updates für `docs/architecture.md` abgeleitet.

Nicht hier sammeln: temporäre Implementierungsdetails, Debug-Notizen, reine Code-Snippets oder lokale Workarounds ohne Architekturwirkung.

## Betroffene Architektur-Dokumente

| Dokument | Status | Ziel-Dokumente |
|---|---|---|
| `docs/architecture.md` | erledigt (S5, #5.2): Selektoren, Modellierungsregeln, Kompatibilität, Tool-Katalog | `docs/architecture.md` |
| `docs/tools.md` | erledigt (regeneriert, 57 Tools) | `docs/tools.md` |

## Architektur-Deltas

| Quelle | Bereich | Erkenntnis | Ziel-Skill | Ziel-Dokument | Status |
|---|---|---|---|---|---|
| Planung 2026-09-29 | Tool-Katalog | Sechs neue Tools (`loft`, `helix`, `primitive`, `boolean`, `draft`, `datum`); ein Tool je PartDesign-Werkzeug, keine Sammel-Tools | `docs/architecture.md` | `docs/architecture.md#tool-katalog` | übernommen (S5) |
| Planung 2026-09-29 | Modellierungsregeln | Primitive sind die einzige Ausnahme von „Skizze zuerst“, beschränkt auf Kugel, Torus, Ellipsoid, Keil und Hilfskörper | `docs/architecture.md` | `docs/architecture.md` Modellierungsregeln | übernommen (S5) |
| Planung 2026-09-29, Spike S1 #1.1, S4 #4.1 | Modellierungsregeln | Boolean verbindet nur Bodies desselben Bauteils. FreeCAD verschiebt die Werkzeug-Bodies in die Boolean-Gruppe des Ziel-Bodys (kein Root-Objekt mehr, Shape bleibt gültig); Undo und Rollback stellen beide Bodies her; Assembly-Parts und bereits verbrauchte Bodies werden abgelehnt | `docs/architecture.md` | `docs/architecture.md` Modellierungsregeln | übernommen (S5) |
| S4 #4.2 | Selektoren | Face-Filter `vertical` (planare Flächen mit waagrechter Normale) ergänzt die Selektor-Grammatik; Dress-up `draft` speichert den Selektor wie `fillet` | `docs/architecture.md` | `docs/architecture.md#semantische-selektoren` | übernommen (S5) |
| Spike S1 #1.2 | Modellierungsregeln | `hole(model_thread=true)` erzeugt echte Gewindegeometrie (≈ 1,5 s, 60–90 Flächen je Loch); das Regelwerk beschränkt es auf einzelne Gewinde, Raster bleiben kosmetisch | `docs/architecture.md` | Regelwerk-Thema `features` (#5.1) | übernommen (S5) |
| Planung 2026-09-29, S3 #3.1/#3.2 | Referenzen | Datum Point, Line und LCS sind neben Datum Plane die einzigen erlaubten Nicht-Ursprungs-Referenzen. Offsets in Ebenenkoordinaten der Basis-Ebene; Datum Line = Achse für revolve/helix/polar, LCS = Skizzenebene. `plane_support` ist der eine Ebenen-Resolver (Skizzen, Primitive, Datums) und liefert den Attachment-Modus | `docs/architecture.md` | `docs/architecture.md` Referenzen, Modellierungsregeln | übernommen (S5) |
| Planung 2026-09-29 | Kompatibilität | `REQUIRED_TYPES` wächst um die neuen PartDesign-Typen; `get_status` meldet fehlende Typen vorab | `docs/architecture.md` | `docs/architecture.md#kompatibilität-und-api-drift` | übernommen (S5) |

## Neue oder geänderte Architekturregeln

- Primitive dürfen ohne Skizze entstehen, ihre Lage kommt aus Parametern über Attachment an Ursprungs- oder Datum-Ebenen, nie aus Solid-Flächen.
- `boolean` ist kein Ersatz für Assembly oder Shape-Binder: nur Bodies, die zusammen ein druckbares Bauteil ergeben.
- `thread` ist ein Intent-Tool über `helix`; es gibt genau eine Helix-Implementierung im Core.

## Veraltete oder widersprüchliche Dokumentation

| Dokument | Problem | Entscheidung |
|---|---|---|
| — | — | — |

## Abschlussprüfung

- [x] Alle Phasen auf Architektur-Deltas geprüft.
- [x] `99-session-log.md` auf Architektur-Erkenntnisse geprüft.
- [x] `docs/architecture.md` aktualisiert oder bewusst unverändert gelassen.
- [x] Keine unnötigen Code-Samples in Architektur-Doku übernommen.
- [x] Neue Architektur-Dokumente im Projekt-README verlinkt (keine neuen Dokumente; README nennt die 57 Tools).

## Abschlussnotiz

`docs/architecture.md` (S5, 2026-09-29): Selektor-Grammatik um `faces:vertical` und Draft; Modellierungsregeln um LCS als Skizzenebene, `plane_support` als einzigen Ebenen-Resolver, Datum-Referenzen, Primitive-Ausnahme, Boolean-Regel und die eine Helix-Implementierung; Kompatibilität um die neuen `REQUIRED_TYPES` und 26.3-Eigenheiten (Point `ObjectOrigin`, Draft-Neutral-Plane, `ModelThread`); Tool-Katalog 51 → 57. `docs/tools.md` regeneriert.
