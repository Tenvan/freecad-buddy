# Phase 6 — Agenten-Workflow & Referenzprojekte

> **Ziel:** Der Agent wird durch MCP-Prompts und Resources zu einem sauberen Konstruktionsablauf geführt; drei Referenzprojekte belegen den Gesamtablauf und die manuelle Weiterbearbeitbarkeit.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-13, AC-14, AC-15. Umsetzung nur für freigegebenen Umfang.

## Session-Pakete

### 📦 Session S10 — Prompts, Referenzprojekte, Doku, Abnahme

- **Kontext-Anker:** `src/buddy_server/prompts/`, `examples/`, `README.md`, `docs/tools.md`
- **Einstiegspunkt:** #6.1 — MCP-Prompts/Resources
- **Erfolgskriterium:** Drei Referenzprojekte laufen per E2E-Skript fehlerfrei durch; Tool-Katalog vollständig; Nutzerabnahme in der GUI dokumentiert.
- **Architektur-Relevanz:** `server`, `docs/architecture.md`
- **Architektur-Notiz:** Finaler Tool-Katalog und Workflow-Prompt als Architekturbestandteil abgleichen.

Enthaltene Aufgaben: #6.1, #6.2, #6.3, #6.4

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #6.1 | MCP-Prompts: „Human Modeling Guide“ (Modellierungsregeln), Workflow „Anforderung → Parameter → Skizze → Feature → Prüfung → Export“; Resources: Modellbaum, Parameter, Druckerprofil. Tool-Anzahl per Test auf ≤ 40 begrenzen. | Geplant | `server` | Phase 5 | — | AC-15 |
| #6.2 | Referenzprojekte als E2E-Skripte über den MCP-Client: (a) Box mit aufsteckbarem Deckel (Passungstoleranz), (b) Wandhalter mit Senkkopfbohrungen und Verrundungen, (c) Drehknopf (Revolution + Polar-Riffelung + D-Welle). Jeweils Druckbarkeits-Check + 3MF-Export. | Geplant | `mehrere` | #6.1 | — | AC-14, AC-07 |
| #6.3 | Doku: `README.md` (Installation, Start, Konfiguration), `docs/tools.md` (Tool-Katalog mit Beispiel je Tool), Troubleshooting, `CHANGELOG.md`; ein Befehl für alle Tests. | Geplant | `docs/architecture.md` | #6.2 | — | AC-13, AC-15 |
| #6.4 | Nutzerabnahme vorbereiten und dokumentieren: Checkliste für manuelle Weiterbearbeitung je Referenzprojekt (Skizze öffnen, Maß im VarSet ändern, Recompute, Feature ergänzen). | Geplant | `keine` | #6.2 | — | AC-14 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

GUI- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-14: Je Referenzprojekt in der GUI: Modellbaum sichten (sprechende Labels), Skizze öffnen (voll bestimmt), einen VarSet-Parameter ändern → Modell aktualisiert sich korrekt, manuell ein Feature ergänzen | offen | ausstehend (nur Nutzer) | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 4
> - Nächste Session: S10
> - Relevante Dateien: `src/buddy_server/`, `examples/`, `docs/`
> - Architektur-Deltas: finalen Tool-Katalog mit `docs/architecture.md` abgleichen
> - Startpunkt: #6.1
