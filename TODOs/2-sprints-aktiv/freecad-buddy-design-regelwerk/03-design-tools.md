# Phase 3 — Grid-Recherche & Design-Tools

> **Ziel:** Als Beispiel für die Addon-Suche klären, ob es eine fertige Grid-Lösung gibt. Außerdem die Vorschlagsliste für Design-Tools und das erste Design-Tool `hole_grid` umsetzen.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-04, AC-05, AC-10, AC-11. Spec-Stand 1 freigegeben am 2026-09-28.

## Session-Pakete

### 📦 Session S5 — Grid-Recherche, Vorschlagsliste, `hole_grid`

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/features.py` (`pattern`, `grid`), `buddy_core/sketch/profiles.py`, `src/buddy_server/tools.py`, `src/buddy_server/tui.py`, `TODOs/5-konzepte/`
- **Einstiegspunkt:** #3.1 — Grid-Recherche über `search_addons`
- **Erfolgskriterium:** Recherche dokumentiert. Das Sieb der Testplatte entsteht mit einem `hole_grid`-Aufruf. Vorschläge erscheinen in der TUI.
- **Architektur-Relevanz:** `docs/architecture.md` (Tool-Kategorien, Design-Tools)
- **Architektur-Notiz:** Design-Tools sind zusammengesetzte Core-Funktionen mit einer Transaktion und bauen auf bestehenden Features auf, ohne neue Primitive.

Enthaltene Aufgaben: #3.1, #3.2, #3.3

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #3.1 | Grid-Recherche: `search_addons` mit grid, array, lattice, pattern, perforation, sieve und gridfinity. Kandidaten bewerten (PartDesign-Tauglichkeit, Parametrik, Lizenz, Pflege, 26.3-Kompatibilität, Portabilität der Modelle), Empfehlung in `TODOs/5-konzepte/grid-loesungen.md`. Regelwerk-Thema `addons` (wann Addon, wann eigenes Tool) nachziehen. Live-Suche nur mit Ralfs Zustimmung | Geplant | `keine` | #2.2 | 2 | AC-10, AC-04 |
| #3.2 | `propose_design_tool(name, problem, inputs, steps, example)` plus `list_design_tool_proposals`: Ablage `%APPDATA%\FreeCADBuddy\design-tool-proposals.json`, Zusammenführung per Name mit Zähler, TUI-Meldung (Event `DesignToolProposed`) | Geplant | `server` | #1.2 | 2 | AC-05 |
| #3.3 | Design-Tool `hole_grid` (Core und Tool): Parameter im VarSet, vollständig bestimmte Startloch-Skizze, Pocket, Raster über MultiTransform, Layout `rect` (und `hex` laut OF-05), Validierung von Feld und Raster, ein Undo-Schritt. Tests: Sieb der Testplatte (34 × 27, Ø 1, Raster 3) und Parameteränderung auf Raster 4 | Geplant | `core`, `server` | #3.1 | 4 | AC-11 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G10 (AC-11): Sieb der Testplatte per `hole_grid`, in der GUI Parameter `Sieve_Pitch` ändern und Skizze öffnen (vollständig bestimmt) | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 3
> - Nächste Session: S5
> - Relevante Dateien: `buddy_core/features.py`, `src/buddy_server/tools.py`
> - Architektur-Deltas: Kategorie Design-Tools
> - Startpunkt: #3.1
