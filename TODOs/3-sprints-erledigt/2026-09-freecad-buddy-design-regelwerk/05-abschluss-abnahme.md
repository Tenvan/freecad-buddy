# Phase 5 — Doku, Release & GUI-Abnahme

> **Ziel:** Tool-Katalog, Architektur und Changelog auf dem neuen Stand, Release 0.2.0. GUI-Abnahme G1–G11 abnehmen oder per Scope-Entscheidung verschieben.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-12, AC-13 sowie übernommen `GA-AC-01` … `GA-AC-08` aus [`gui-abnahme.md`](../../1-backlog/freecad-buddy/gui-abnahme.md). Spec-Stand 1 freigegeben am 2026-09-28.

## Session-Pakete

### 📦 Session S6 — Doku, Release, Abnahme

- **Kontext-Anker:** `tools/gen_tool_docs.py`, `docs/tools.md`, `docs/architecture.md`, `docs/acceptance.md`, `README.md`, `CHANGELOG.md`, `pyproject.toml`
- **Einstiegspunkt:** #5.1 — Tool-Katalog mit Kategorien neu erzeugen
- **Erfolgskriterium:** `uv run poe check` ist grün, ≤ 40 Tools. `docs/acceptance.md` enthält G1–G11, und Ralfs Abnahmen sind dokumentiert.
- **Architektur-Relevanz:** `docs/architecture.md`
- **Architektur-Notiz:** Deltas aus `98-architecture-update.md` übernehmen.

Enthaltene Aufgaben: #5.4, #5.1, #5.2, #5.3

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #5.4 | Alle MCP-Ausgaben englisch: Instructions, Regelwerk, Prompts, Resources, Tool-/Parameterbeschreibungen, Ergebnisse, Warnungen, Hinweise (`Hint:` statt `Hinweis:`), Fehler aus Server, Core und Bridge sowie Undo-Namen. UI-Texte nach OF-09 deutsch (Datei-Ausnahmen, Marker `# ui-de`). Sprachtest `tests/server/test_language.py` | Regel: MCP-Ausgaben englisch, UI deutsch (98) | 2026-09-29 |
| #5.1 | Doku-Generator: Gruppen mit Kategorie-Präfix und Budgettest ≤ 100 bestanden bereits seit dem Referenzen-Sprint; neue Gruppe Design-Tools und Beispiele ergänzt, `docs/tools.md` aktuell (51 Tools, 11 Gruppen) | keins | 2026-09-29 |
| #5.2 | `docs/architecture.md` mit allen Deltas aus 98 (Regelwerk, Design-Tools, verschachtelte Transaktion, Addon-Integration, Job-Muster, Sicherheit, Tool-Events, Sprache), README, `CHANGELOG.md` 0.2.0, Version 0.2.0 in `pyproject.toml`, Server, Bridge und Core, `docs/acceptance.md` mit G10–G12 | Architektur-Doku aktualisiert | 2026-09-29 |
| #5.3 | `docs/acceptance.md` um G9–G12 ergänzt; GUI-Abnahme: Agententeil G1/G3/G4/G10/G12 bestanden, Ralf bestätigt G1, G3, G5, G7/G11, G9, G10. G2, G6 und G8 nicht getestet → Folgeticket [`gui-abnahme.md`](../../1-backlog/freecad-buddy/gui-abnahme.md) | keins | 2026-09-29 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G1–G8 laut `docs/acceptance.md` (Teilnachweise G1/G7 im Ticket) | offen | ausstehend | ausstehend |
| G9 Addon-Installationsdialog, G10 `fill_pattern`, G11 Chat-Log | offen | ausstehend | ausstehend |
| Agententeil (Ralf: „Agent führt, ich schaue“, 2026-09-29), Dokument `Abnahme` in der GUI: G1 Teil 1 (`get_status`: FreeCAD 26.3.0, Bridge/Core 0.2.0, keine fehlenden Typen), G3 agentenseitig (20 Aufrufe = 20 benannte Undo-Schritte, z. B. `Fill pattern: Sieve`), G4 (Screenshots iso/top), G10 (Platte mit Rand; `fill_pattern` round 17 × 13 und hex 11 × 10 mit Feld `Plate_Width - 2*Rim_Width`; nach `Plate_Width` 120 und `Sieve_Pitch` 6 → 18 × 11 bzw. 14 × 10, alle Skizzen DoF 0, alles gültig), G12 (Ansicht nach erstem `pad` automatisch iso, nach `set_view` komplett sichtbar); AC-01 Sichtung: englische Instructions kommen in Claude Code an | ✅ bestanden | Agentenfreigabe durch Ralf im Chat | Session-Log 6c |
| Ralfs Teil: G1 (inkl. FreeCAD schließen → `[bridge_unavailable]`), G3 (Menü „Bearbeiten → Rückgängig“), G5, G7/G11, G9 (Dialog ablehnen und zustimmen), G10 (Skizze in der GUI vollständig bestimmt) | ✅ bestanden | Ralf im Chat, 2026-09-29 | Session-Log 6c |
| G2 (GUI bedienbar während eines Baus), G6 (3MF im Slicer), G8 (Probedruck, optional) | ⏭️ nicht getestet, verschoben | Scope-Entscheidung: Folgeticket `gui-abnahme.md` | Session-Log 6c |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0
> - Nächste Session: S6
> - Relevante Dateien: `docs/*`, `CHANGELOG.md`
> - Architektur-Deltas: alle aus `98-architecture-update.md` übernehmen
> - Startpunkt: Sprint abgeschlossen; Rest-Abnahme G2/G6/G8 im Backlog-Ticket `gui-abnahme.md`
