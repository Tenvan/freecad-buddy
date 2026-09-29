# Architektur-Update — FreeCAD Buddy: Design-Stream mit Storepoints

> Erstellt: 2026-09-29 │ Letzte Aktualisierung: 2026-09-29 (S1) │ Status: übernommen

## Zweck

Dieses Dokument sammelt während des Sprints stabile Architektur-Erkenntnisse. Am Sprint-Ende werden daraus gezielte Updates für `docs/architecture.md` abgeleitet.

Nicht hier sammeln: temporäre Implementierungsdetails, Debug-Notizen, reine Code-Snippets oder lokale Workarounds ohne Architekturwirkung.

## Betroffene Architektur-Dokumente

| Dokument | Status | Ziel-Dokumente |
|---|---|---|
| `docs/architecture.md` | erledigt (S1, #4.2): neuer Abschnitt „Design-Stream und Storepoints“, Tool-Katalog 60 | `docs/architecture.md` |
| `docs/tools.md` | erledigt (regeneriert, 60 Tools) | `docs/tools.md` |

## Architektur-Deltas

| Quelle | Bereich | Erkenntnis | Ziel-Skill | Ziel-Dokument | Status |
|---|---|---|---|---|---|
| Planung 2026-09-29 | Datenfluss | Design-Stream: die Bridge-Registry zeichnet jeden mutierenden Aufruf (Methode, Parameter, erzeugte Objekte, Undo-Name) auf, der Core legt ihn im Dokument ab (Gruppe `Storepoints`), die Bridge spielt ihn über denselben Ausführungsweg in ein neues Dokument ab | `docs/architecture.md` | neuer Abschnitt Design-Stream | übernommen (S1) |
| Planung 2026-09-29 | Transaktionen | Mutierend = Undo-Zähler gewachsen; Undo kompaktiert den Stream über die Transaktionsnamen; fremde Transaktionen (GUI) werden als `manual_edit` erkannt, nicht rekonstruiert | `docs/architecture.md` | `docs/architecture.md#transaktionen-und-ergebnisvertrag` | übernommen (S1) |
| Planung 2026-09-29 | Modellbaum | Buddy-Objekte im Dokument neben dem VarSet: Gruppe `Storepoints` mit Marker-Objekten (`App::FeaturePython`, Link auf das Feature, ViewProvider mit Icon nur in der GUI); `Label2` am Feature als Beschreibung | `docs/architecture.md` | Modellierungsregeln / Design-Stream | übernommen (S1) |
| Planung 2026-09-29 | Sicherheit | Replay führt `python.*` und `addons.install` nie aus; Einträge tragen die Buddy-Version, Abweichung ergibt eine Warnung | `docs/architecture.md` | `docs/architecture.md#sicherheit` | übernommen (S1) |

## Neue oder geänderte Architekturregeln

- Es gibt genau einen Ausführungsweg für Bridge-Methoden (`MethodRegistry.execute`); Aufzeichnung und Replay hängen dort, nie in den Core-Funktionen.
- Der Stream ist Teil des Dokuments; Labels bleiben Referenzen und werden für Storepoints nicht verändert (`Label2` statt Label).

## Veraltete oder widersprüchliche Dokumentation

| Dokument | Problem | Entscheidung |
|---|---|---|
| — | — | — |

## Abschlussprüfung

- [x] Alle Phasen auf Architektur-Deltas geprüft.
- [x] `99-session-log.md` auf Architektur-Erkenntnisse geprüft.
- [x] `docs/architecture.md` aktualisiert oder bewusst unverändert gelassen.
- [x] Keine unnötigen Code-Samples in Architektur-Doku übernommen.
- [x] Neue Architektur-Dokumente im Projekt-README verlinkt (kein neues Dokument; README beschreibt den Design-Stream).

## Abschlussnotiz

`docs/architecture.md` (S1, 2026-09-29): neuer Abschnitt „Design-Stream und Storepoints“ mit Aufzeichnung in der Registry (`execute` als einziger Ausführungsweg), Ablage in der Gruppe `Storepoints`, Abgleich mit der Undo-Historie (Kompaktierung, `manual_edit`, 20-Schritte-Fenster), Storepoints (Marker + `Label2`, ViewProvider nur GUI) und Replay in der Bridge (Skips, Warnungen, Abbruch, Timeout 600 s). Tool-Katalog 57 → 60. `docs/tools.md` regeneriert.
