# Phase 1 — Spikes & Fundament

> **Ziel:** Die beiden Unbekannten (Boolean im Baum, `ModelThread`) headless klären und die technische Basis für die neuen Typen legen, damit die Feature-Phasen ohne Überraschungen laufen.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-04, AC-08, AC-09 (Voraussetzung). Spec-Stand 1 freigegeben am 2026-09-29.

## Session-Pakete

### 📦 Session S1 — Spikes, Fundament und `loft`

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/features.py` (`_new`, `_finish`, `_ensure_cuts`), `addon/FreeCADBuddy/buddy_core/compat.py` (`REQUIRED_TYPES`), `tests/core/test_features.py`, `tests/core/conftest.py`
- **Einstiegspunkt:** #1.1 — Spike `PartDesign::Boolean`
- **Erfolgskriterium:** OF-02 und OF-03 sind mit Messwerten unter Entscheidungen im Index eingetragen; `REQUIRED_TYPES` enthält die neuen Typen; `loft` (#2.1) ist umgesetzt und getestet.
- **Architektur-Relevanz:** `docs/architecture.md` (Kompatibilität, Modellierungsregel Boolean)
- **Architektur-Notiz:** Falls Boolean die Bodies in seine Gruppe zieht, braucht die Regel „ein Body = ein Bauteil“ eine Ausnahme oder `boolean` wird auf `fuse` beschränkt.

Enthaltene Aufgaben: #1.1, #1.2, #1.3 (dazu #2.1 aus Phase 2)

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #1.1 | Spike OF-02 headless (Skript im Scratchpad, nicht im Repo): `PartDesign::Boolean` mit `addObjects([body])` für Fuse (9000 mm³), Cut (6000), Common (2000), alle gültig; der Werkzeug-Body verlässt `RootObjects` und hängt in `Boolean.Group`, sein Shape bleibt gültig, `InList` zeigt den Boolean; Undo ist ein Schritt, danach und nach `abortTransaction` sind beide Bodies gültig und wieder Root. Assembly-`Parts`-Fall nicht gemessen → Ablehnung per Regel. Ergebnis im Index (OF-02) | Boolean-Regel in 98 bestätigt | 2026-09-29 |
| #1.2 | Spike OF-03 headless: `ModelThread` in 26.3 vorhanden (dazu `CosmeticThread`, `ThreadDepth`, `ThreadDepthType`, `ThreadFit`, `ThreadClass`); `ThreadSize`-Enumeration wird erst durch `ThreadType` gefüllt (bestehender Helfer `_thread_size` deckt das ab). M6: 1767 ms, 91 Flächen, 467 mm³ statt 393; M10: 1396 ms, 64 Flächen, 1321 mm³ statt 1135; Solids gültig. Ergebnis im Index (OF-03) | Regel „nur einzelne Gewinde“ in 98 | 2026-09-29 |
| #1.3 | `compat.REQUIRED_TYPES` um 25 Typen erweitert (Loft, Helix, 16 Primitive, Boolean, Draft, Point, CoordinateSystem); `test_all_required_types_are_available` grün in 26.3. Volumenhelfer verschoben nach #2.3 (erst dort gebraucht, Scope-Entscheidung Agent) | `REQUIRED_TYPES`-Delta in 98 | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| keine erforderlich (nur Headless-Spikes und Tests) | — | — | — |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0
> - Nächste Session: S2 (Phase 2, #2.2)
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/thread.py`, `addon/FreeCADBuddy/buddy_core/features.py`
> - Architektur-Deltas: Spike-Ergebnisse in `98-architecture-update.md` eingetragen
> - Startpunkt: #2.2
