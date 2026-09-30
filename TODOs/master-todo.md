# Master-Todo — FreeCAD Buddy

> **Manuell gepflegt** (kein Index-Generator im Projekt).
> Quelle: alle `00-index.md` unter `TODOs/1-backlog/`, `TODOs/2-sprints-aktiv/`, `TODOs/3-sprints-erledigt/`.

## Roadmap

Reihenfolge der kommenden Sprints mit Domäne je Sprint: [`roadmap.md`](roadmap.md) (nächster Schritt R0: Review-Gate der beiden aktiven Sprints; alle GUI-Abnahmen bestanden).

## Aktive Sprints

| Name | Pfad | Status | Notiz |
|---|---|---|---|
| FreeCAD Buddy: PartDesign-Vollständigkeit | [`2-sprints-aktiv/freecad-buddy-partdesign/00-index.md`](2-sprints-aktiv/freecad-buddy-partdesign/00-index.md) | 🟡 Wartet auf Review-Gate (seit 2026-09-30) | 16/16 Aufgaben (6 neue Tools, Taper, `model_thread`, Regelwerk, Doku, Version 0.3.0); GUI-Abnahme G13 bestanden; offen nur Review-Gate |
| FreeCAD Buddy: Design-Stream mit Storepoints | [`2-sprints-aktiv/freecad-buddy-storepoints/00-index.md`](2-sprints-aktiv/freecad-buddy-storepoints/00-index.md) | 🟡 Wartet auf Review-Gate (seit 2026-09-30) | 10/10 Aufgaben (Aufzeichnung, Storepoints mit Marker, Replay, 3 Tools, Doku, Version 0.4.0, 60 Tools); GUI-Abnahme G14/G15 bestanden (Bugfix `manual_edit`); offen nur Review-Gate |

## Backlog (nach Domain)

| Name | Pfad | Status | Notiz |
|---|---|---|---|
| Backlog — freecad-buddy | [`1-backlog/freecad-buddy/00-index.md`](1-backlog/freecad-buddy/00-index.md) | Backlog | 2 offene Tickets: 🟡 GUI-Abnahme Rest (G2, G6, G8), 🟡 Druckprüfung Überhang/Brücken; 2 Tickets in aktiven Sprints (PartDesign-Vollständigkeit, Design-Stream); 4 umgesetzte Tickets als Historie; dazu Ideen-Parkplatz |

## Konzepte

| Name | Pfad | Notiz |
|---|---|---|
| Marktanalyse bestehender FreeCAD-MCP-Server | [`5-konzepte/freecad-mcp-marktanalyse.md`](5-konzepte/freecad-mcp-marktanalyse.md) | Vergleich bestehender Projekte, Lücken |
| Grid-Lösungen für Loch- und Wabenraster | [`5-konzepte/grid-loesungen.md`](5-konzepte/grid-loesungen.md) | Addon-Recherche (AC-10); Entscheidung: `fill_pattern` (round/hex), kein Addon |

## Erledigte Sprints

| Name | Pfad | Status | Notiz |
|---|---|---|---|
| FreeCAD Buddy: Design-Regelwerk, Design-Tools & Addon-Suche | [`3-sprints-erledigt/2026-09-freecad-buddy-design-regelwerk/00-index.md`](3-sprints-erledigt/2026-09-freecad-buddy-design-regelwerk/00-index.md) | ✅ Erledigt (2026-09-29) | 21/21 Aufgaben, Spec-Stand 6, Version 0.2.0; Regelwerk, `fill_pattern`, Addon-Suche/-Installation, Chat-Log, englische MCP-Ausgaben; GUI-Rest G2/G6/G8 → Backlog |
| FreeCAD Buddy: Externe Geometrie, Shape-Binder & Layout-Skizze | [`3-sprints-erledigt/2026-09-freecad-buddy-referenzen/00-index.md`](3-sprints-erledigt/2026-09-freecad-buddy-referenzen/00-index.md) | ✅ Erledigt (2026-09-28) | 16/16 Aufgaben, Spec-Stand 2; externe Geometrie, `shape_binder`, Hole-Senkungen, gruppierter Katalog, `document`-Tool |
| FreeCAD Buddy: PartDesign-first für 3D-Druck | [`3-sprints-erledigt/2026-09-freecad-buddy-aufbau/00-index.md`](3-sprints-erledigt/2026-09-freecad-buddy-aufbau/00-index.md) | ✅ Erledigt (2026-09-28) | 36/36 Aufgaben, Spec-Stand 2; GUI-Abnahme G1–G8 → Backlog-Ticket |
