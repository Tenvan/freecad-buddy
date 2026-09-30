# Phase 1 — Aufzeichnung & Ablage

> **Ziel:** Jeder erfolgreiche mutierende Bridge-Aufruf landet als Eintrag im Stream des Dokuments; der Stream liegt im Dokument, überlebt Speichern und Öffnen, kompaktiert bei Undo und markiert fremde Transaktionen.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-01, AC-02, AC-07, AC-08. Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S1 — Stream-Modul und Registry-Hook

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_bridge/registry.py` (`MethodRegistry.invoke`), `addon/FreeCADBuddy/buddy_core/transaction.py`, `addon/FreeCADBuddy/buddy_core/documents.py` (`model_tree`, `undo`), `tests/bridge/test_methods.py`
- **Einstiegspunkt:** #1.1
- **Erfolgskriterium:** Bridge-Test (`tests/bridge/test_stream.py`): Aufrufe erscheinen in Reihenfolge, zurückgerollte nicht, Undo kompaktiert, fremde Transaktion ergibt `manual_edit`, Stream nach Speichern/Öffnen vorhanden.
- **Architektur-Relevanz:** `docs/architecture.md` (Design-Stream, Transaktionen)
- **Architektur-Notiz:** Die Registry ist der einzige Ort, an dem Methode und Parameter zusammen mit dem Ergebnis bekannt sind; Aufzeichnung dort hält Core frei von Bridge-Wissen.

Enthaltene Aufgaben: #1.1, #1.2, #1.3

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #1.1 | `buddy_core/stream.py`: Gruppe `Storepoints` (Name `BuddyStorepoints`, `App::DocumentObjectGroup`) mit Properties `Stream` (StringList, ein JSON je Eintrag) und `StreamVersion`; `entries(doc)`, `append(doc, entry)`, `snapshot()`, `record(...)`, `reconcile(doc)` (Abgleich mit der Undo-Historie: Kompaktierung zurückgenommener Schritte); Eintrag = method, params, created, undo_name, time, version; fremde Transaktionen über `UndoNames` → Eintrag `manual_edit` mit `undo_names` | siehe 98 | 2026-09-29 |
| #1.2 | `MethodRegistry.execute(name, params)` als gemeinsamer Ausführungsweg (auch für Replay): Commit-Zähler aller Dokumente vor/nach dem Aufruf, Aufzeichnung nur bei gewachsenem Zähler, sonst nur Abgleich mit der Undo-Historie (`reconcile`); was nie aufgezeichnet wird, steht in `NOT_RECORDED` (`registry.py`); `invoke` nutzt `execute` | siehe 98 | 2026-09-29 |
| #1.3 | `get_model_tree`: Gruppe und Marker lesbar (Typ, Position, verlinktes Feature); `undo`-Tool bleibt unverändert, Kompaktierung passiert in der Registry | siehe 98 | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-07 GUI-Anteil (G15): in der GUI eine Skizze von Hand verschieben, danach ein Tool aufrufen → `list_storepoints`/Stream zeigt `manual_edit` | ✅ bestanden (2. Lauf) | Ralf bearbeitet `Sketch_Recess` in der GUI, Agent führt MCP-Schritte aus, 2026-09-30 | 1. Lauf ❌ → Fix `0b8025f`; 2. Lauf: genau ein `manual_edit`, eine Replay-Warnung (Session-Log S2) |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0
> - Nächste Session: S3 (Review-Gate in frischer Session, `97-review.md`, Bereich `da5701a..HEAD`)
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_bridge/registry.py`, `addon/FreeCADBuddy/buddy_core/stream.py`, `tests/bridge/test_stream.py`
> - Architektur-Deltas: Design-Stream in `98-architecture-update.md`, alle übernommen
> - Startpunkt: `git diff --name-status da5701a..HEAD` in `97-review.md` eintragen
