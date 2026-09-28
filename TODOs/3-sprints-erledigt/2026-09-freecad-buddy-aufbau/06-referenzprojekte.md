# Phase 6 — Agenten-Workflow & Referenzprojekte

> **Ziel:** Der Agent wird durch MCP-Prompts und Resources zu einem sauberen Konstruktionsablauf geführt; drei Referenzprojekte belegen den Gesamtablauf und die manuelle Weiterbearbeitbarkeit.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 2, Kriterien AC-13, AC-14, AC-15.

## Session-Pakete

### 📦 Session S10 — Prompts, Referenzprojekte, Doku, Abnahme ✅ (Nutzerabnahme offen)

Enthaltene Aufgaben: #6.1, #6.2, #6.3, #6.4

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | Alle Aufgaben umgesetzt; Nutzerabnahme G5 offen | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #6.1 | Server-`instructions`, Prompts `design_part` und `human_modeling_guide` (`src/buddy_server/prompts.py`); Tool-Obergrenze per Test. Resources bewusst nicht umgesetzt: Modellbaum, Parameter und Profil sind als Tools abrufbar, Resources würden nur duplizieren | Entscheidung notiert | 2026-09-27 |
| #6.2 | `examples/reference_projects.py`: Box mit Deckel (zwei Bodies, Passungsspiel), Wandhalter (Polyline + benannte Maße, Senkbohrungen, Innenkanten-Verrundung per Koordinaten-Selektor), Drehknopf (Revolution, Polar-Riffelung per Integer-Parameter, Wellenbohrung); E2E-Test `tests/server/test_reference_projects.py` | — | 2026-09-27 |
| #6.3 | README, `docs/tools.md` (generiert, Test gegen Veralten), `CHANGELOG.md`, `uv run poe check` als ein Befehl | — | 2026-09-27 |
| #6.4 | Abnahme-Checkliste `docs/acceptance.md` (G1–G8) | — | 2026-09-27 |

## Geplante Abnahmeprüfungen

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G5 / AC-14: Referenzprojekte in der GUI weiterbearbeiten (Baum, Skizze, VarSet-Parameter, eigenes Feature) | offen | ausstehend (nur Nutzer) | E2E headless grün (3/3) |

## 🔄 Nächste Session

> **Einstieg:** Umsetzung abgeschlossen. Offen: Nutzerabnahme G1–G8 nach `docs/acceptance.md`, danach Sprint-Abschluss (Verschieben nach `3-sprints-erledigt/`).
