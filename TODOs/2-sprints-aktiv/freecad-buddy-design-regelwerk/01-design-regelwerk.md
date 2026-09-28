# Phase 1 — Design-Regelwerk & Instructions

> **Ziel:** Ein thematisch gegliedertes Design-Regelwerk aus einer Quelle. Daraus entstehen die kompakten Server-Instructions, das Tool `get_design_rules`, die MCP-Resource und der Prompt `human_modeling_guide`.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-01 bis AC-04. Spec-Stand 1 freigegeben am 2026-09-28.

## Session-Pakete

### 📦 Session S1 — Regelwerk, Instructions, Tool und Resource

- **Kontext-Anker:** `src/buddy_server/prompts.py`, `src/buddy_server/app.py`, `src/buddy_server/tools.py`, `addon/FreeCADBuddy/buddy_core/printing/profile.py`
- **Einstiegspunkt:** #1.1 — Umgang von Claude Code und MCP-Spec mit Instructions und Resources prüfen
- **Erfolgskriterium:** `get_design_rules("printing")` liefert Regeln mit Profilwerten. Die Instructions liegen im Budget. Die Tests sind grün.
- **Architektur-Relevanz:** `docs/architecture.md` (Abschnitt Server und Agentenführung)
- **Architektur-Notiz:** Das Regelwerk ist eine neue Server-Komponente. Profilwerte kommen per Bridge-Aufruf, der Server rechnet keine eigenen Druckwerte.

Enthaltene Aufgaben: #1.1, #1.2, #1.3, #1.4, #1.5

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #1.1 | Recherche mit aktuellen Quellen: Wie übernimmt Claude Code MCP-Server-Instructions (Längengrenze, Kürzung)? Wie werden Resources und Resource-Templates angeboten? Ergebnis setzt OF-01 | Geplant | `server` | — | 1 | AC-01 (OF-01) |
| #1.2 | Regelwerk-Quelle `buddy_server/design_rules.py` mit Themen aus R-03: je Thema Titel, Einzeiler und Regeln. FDM-Regeln als Vorlagen mit Profilwerten (Mindestwand, Überhang, Spiel, Layerhöhe, Brückenlänge, Bohrungsaufmaß, Elefantenfuß-Fase, Orientierung). Inhalt aus `HUMAN_MODELING_GUIDE` übernehmen und ausbauen | Geplant | `server` | #1.1 | 3 | AC-02, AC-03 |
| #1.3 | Kompakte `INSTRUCTIONS` aus der Quelle erzeugen: Kernregeln, Design-Tool-Regel (R-04), Verweis auf `get_design_rules`, innerhalb des Budgets | Geplant | `server` | #1.2 | 1 | AC-01, AC-04 |
| #1.4 | Tool `get_design_rules(topic=None)` (Profilwerte über `get_printer_profile` der Bridge, ohne Bridge mit Standardprofil und Hinweis), Resources `buddy://design-rules` und `buddy://design-rules/{topic}`, `human_modeling_guide` und `design_part` aus der Quelle | Geplant | `server` | #1.2 | 2 | AC-02, AC-04 |
| #1.5 | Tests: Budget und Pflichtinhalte der Instructions, jedes genannte Tool existiert, Profilwechsel (Düse 0,6) ändert Zahlen, unbekanntes Thema ergibt `validation`, E2E über MCP (Tool und Resource) | Geplant | `server` | #1.3, #1.4 | 2 | AC-01 bis AC-04 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-01: Nach Neustart von Claude Code erscheinen die neuen Instructions ungekürzt im Server-Abschnitt | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 5
> - Nächste Session: S1
> - Relevante Dateien: `src/buddy_server/prompts.py`, `src/buddy_server/app.py`
> - Architektur-Deltas: in `98-architecture-update.md` ergänzen
> - Startpunkt: #1.1
