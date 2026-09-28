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
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #1.1 | Recherche: Claude Code dokumentiert weder Übernahme noch Längengrenze der MCP-Instructions. Resource-Templates sind nur in der MCP-Spec beschrieben. Tool-Ausgaben sind standardmäßig auf 25 000 Tokens begrenzt (`MAX_MCP_OUTPUT_TOKENS`). OF-01 bleibt bei ≤ 2 000 Zeichen, geprüft wird per Sichtung | keins | 2026-09-28 |
| #1.2 | `src/buddy_server/design_rules.py`: 9 Themen und 42 Regeln. Regeln mit `requires` erscheinen nur, wenn ihre Tools registriert sind. FDM-Werte als Vorlagen aus dem Profil plus abgeleitete Werte (tragende Wand, Bettfase, M3-Spiel) | in 98 notiert | 2026-09-28 |
| #1.3 | `build_instructions`: Kernregeln plus Verweis auf `get_design_rules`, 1 688 Zeichen, Namen vorab per `NameCollector` gesammelt | in 98 notiert | 2026-09-28 |
| #1.4 | Tool `get_design_rules` (Profil aus der Bridge, sonst Standardprofil mit Hinweis), Resource `buddy://design-rules` und Template `/{topic}`, Prompts `human_modeling_guide` und `design_part` aus der Quelle. `ToolContext.local` für serverseitige Tools | keins | 2026-09-28 |
| #1.6 | Stand 2, Ansichtsregel: `set_view` (Core `view.set_view`, Bridge `view.set`, Tool) mit iso/dimetric/trimetric/Normalansichten und `fit`. Kernregel im Thema `workflow` (mit `requires=set_view`), `design_part` mit erstem und letztem Schritt. Tests für Instructions und Bridge (headless `unsupported`). Instructions jetzt 1 874 Zeichen | keins | 2026-09-28 |
| #1.5 | `tests/server/test_design_rules.py` (8 Tests): Budget, Kernregeln, nur registrierte Tools genannt (mit und ohne `execute_python`), Themenabdeckung, Profilwerte bei Düse 0,6, versteckte Themen, E2E über MCP mit Tool, Fehlerfall, Resource-Template und Prompt | keins | 2026-09-28 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-01: Nach Neustart von Claude Code erscheinen die neuen Instructions ungekürzt im Server-Abschnitt | offen | ausstehend | ausstehend |
| G12 (AC-16): `set_view` in der GUI, das Bauteil ist danach komplett sichtbar und isometrisch | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0 (S1 erledigt)
> - Nächste Session: S2 (Phase 4, TUI-Chat-Log)
> - Relevante Dateien: `src/buddy_server/prompts.py`, `src/buddy_server/app.py`
> - Architektur-Deltas: in `98-architecture-update.md` ergänzen
> - Startpunkt: #4.1 in `04-tui-chat-log.md`
