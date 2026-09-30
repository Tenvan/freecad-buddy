# Phase 2 — Storepoints & Baum

> **Ziel:** Storepoints setzen und listen; jeder Storepoint ist im FreeCAD-Baum als Beschreibung am Feature und als Marker in der Gruppe `Storepoints` sichtbar.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-03, AC-10. Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S2 (Teil) — Storepoints, Marker, ViewProvider

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/stream.py`, `addon/FreeCADBuddy/buddy_core/naming.py`, `docs/acceptance.md`
- **Einstiegspunkt:** #2.1
- **Erfolgskriterium:** Headless-Test (`tests/bridge/test_stream.py`): Marker mit Link, `Label2` am Feature, Undo räumt auf, doppelte Namen abgelehnt, Liste korrekt.
- **Architektur-Relevanz:** `docs/architecture.md` (Marker als sichtbare Buddy-Objekte neben dem VarSet)
- **Architektur-Notiz:** Marker sind `App::FeaturePython` ohne App-Proxy (kein Proxy-Zwang beim Laden); nur der ViewProvider hat einen Proxy (GUI).

Enthaltene Aufgaben: #2.1, #2.2, #2.3

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #2.1 | `stream.storepoint(name, snapshot, document)`: eine Transaktion; Marker `App::FeaturePython` in der Gruppe mit `Feature` (Link auf das zuletzt erzeugte Feature laut Stream), `Position`, `Created`, `Steps`; Label `Storepoint_<Name>`; `Label2` „◆ Storepoint <n>: <Name>“ auf dem Feature; doppelter Name → `validation`; optional FCStd-Snapshot neben der Datei (OF-03) | siehe 98 | 2026-09-29 |
| #2.2 | `stream.list_storepoints(document)`: Name, Position, Zeit, Schritte seit dem vorherigen, Feature-Label; leer mit Hinweis, wenn kein Stream | siehe 98 | 2026-09-29 |
| #2.3 | ViewProvider (nur `FreeCAD.GuiUp`) mit Icon und Doppelklick → Auswahl des verlinkten Features; Proxy-Klasse im Addon-Paket, damit Dokumente mit Addon sauber laden | siehe 98 | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G14 (AC-10): Teil bauen lassen, `storepoint("Grundkörper")`; im Baum: Gruppe `Storepoints` mit Marker und Icon, „◆ Storepoint 1: Grundkörper“ in der Beschreibungsspalte am Feature, Doppelklick auf den Marker markiert das Feature | ✅ bestanden | Ralf im Chat, 2026-09-30 | Icon, Beschreibungsspalte und Doppelklick bestätigt; kein Hover-Tooltip (FreeCAD zeigt `Label2` nicht als Tooltip), Katalogtext korrigiert (Session-Log S2) |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0
> - Nächste Session: S3 (Review-Gate in frischer Session, `97-review.md`, Bereich `da5701a..HEAD`)
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/stream.py`, `tests/bridge/test_stream.py`
> - Architektur-Deltas: Marker-Objekte in `98-architecture-update.md`, übernommen
> - Startpunkt: `git diff --name-status da5701a..HEAD` in `97-review.md` eintragen
