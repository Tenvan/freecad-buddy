# GUI-Abnahme FreeCAD Buddy 0.1.0 (G1–G8)

> Erstellt: 2026-09-28 │ Letzte Aktualisierung: 2026-09-29 │ Status: 🟡 Rest offen (G2, G6, G8) – Rest aus Sprint [`freecad-buddy-design-regelwerk`](../../3-sprints-erledigt/2026-09-freecad-buddy-design-regelwerk/00-index.md) │ Priorität: mittel │ Architektur-Impact: keiner

## Spezifikation

> Spec-Stand: 1 │ Spec-Status: Entwurf │ Freigabe: ausstehend

## Ausgangslage

Sprint [`freecad-buddy-aufbau`](../../3-sprints-erledigt/2026-09-freecad-buddy-aufbau/00-index.md) wurde am 2026-09-28 auf Wunsch von Ralf abgeschlossen. Die automatisierbaren Anteile aller Akzeptanzkriterien sind erfüllt (`uv run poe check`). Die GUI-, Slicer- und Probedruck-Prüfungen G1–G8 aus [`docs/acceptance.md`](../../../docs/acceptance.md) waren zu diesem Zeitpunkt nicht abgenommen. Ralf hat per Scope-Entscheidung festgelegt, sie in dieses Folgeticket zu verschieben.

## Ziel

Alle GUI-Anteile der Sprint-Kriterien AC-01, AC-02, AC-09, AC-11 und AC-14 sind von Ralf abgenommen oder bewusst verworfen. Die optionalen Prüfungen G3, G7 und G8 sind entschieden.

## Beteiligte und Zielgruppen

- **Ralf:** führt die Prüfungen in FreeCAD, im Slicer und am Drucker durch und bestätigt sie.
- **Agent:** bereitet Prüfläufe vor und behebt gefundene Fehler; führt Prüfungen nur mit ausdrücklicher Freigabe aus.

## Anforderungen

Ablauf und erwartete Ergebnisse je Prüfung stehen in [`docs/acceptance.md`](../../../docs/acceptance.md) (Stand 2026-09-27) und werden hier nicht dupliziert.

## Nicht-Ziele

- Neue Tools oder Features. Gefundene Fehler werden als Bugfix behoben, nicht als Erweiterung.
- Wiederholung der automatisierten Tests.

## Regeln und Einschränkungen

- Freigaberegel aus [`TODOs/README.md`](../../README.md#browser--und-manuelle-abnahmeprüfungen): vor jeder Prüfung klären, was Ralf bereits selbst geprüft hat und was der Agent übernehmen darf.
- Nachweise nicht erfinden; ohne Bestätigung bleibt eine Prüfung offen.

## Beispiele

- Ralf meldet „G4 ok“ im Chat → AC-04 dieses Tickets mit Datum als erfüllt eintragen.

## Ausnahme- und Fehlerfälle

- Eine Prüfung schlägt fehl → Befund im Ticket festhalten, Bugfix-Ticket oder Fix-Session anlegen, danach Prüfung wiederholen.

## Akzeptanzkriterien

- [x] AC-01 (G1 → Sprint-AC-01): `get_status` aus Claude Code gegen die GUI-Bridge liefert Version und Status „verbunden“; nach dem Schließen von FreeCAD kommt `[bridge_unavailable]` in ≤ 10 s und die TUI zeigt „wartet“.
- [ ] AC-02 (G2 → Sprint-AC-02): Während ein Referenzprojekt gebaut wird, bleibt die FreeCAD-GUI bedienbar, ohne Hänger oder Absturz.
- [x] AC-03 (G3, optional → Sprint-AC-03): Die Undo-Liste zeigt genau einen sprechend benannten Schritt pro Tool-Aufruf.
- [x] AC-04 (G4 → Sprint-AC-09): `screenshot` (view iso) liefert ein Bild der 3D-Ansicht in Claude Code.
- [x] AC-05 (G5 → Sprint-AC-14): Die drei Referenzprojekte sind in der GUI manuell weiterbearbeitbar (Skizze vollständig bestimmt, Parameteränderung im VarSet wirkt, eigenes Feature ergänzbar).
- [ ] AC-06 (G6 → Sprint-AC-11): Die exportierte 3MF liegt im Slicer korrekt auf dem Bett, die Maße stimmen.
- [x] AC-07 (G7, optional → Sprint-AC-16): Status, Sessions, Tool-Log und Meldungen der TUI sind verständlich.
- [ ] AC-08 (G8, optional): Beim Probedruck der Box mit Deckel passt der Deckel mit dem Spiel `clearance_fit`.

## Stand 2026-09-29

Abgenommen im Sprint `freecad-buddy-design-regelwerk` (Agent und Ralf, Version 0.2.0): G1, G3, G4, G5, G7. Nicht getestet und weiter offen: G2 (GUI bedienbar während eines Baus), G6 (3MF im Slicer), G8 (Probedruck, optional). Die neuen Prüfungen G9–G12 sind im Sprint abgenommen.

## Offene Fragen

- Soll die optionale Prüfung G8 (Probedruck) durchgeführt werden? Verantwortlich: Ralf. (G3 und G7 sind abgenommen.)

## Umsetzung und Nachweis

| Kriterium | Geplante Aufgabe / Schritte | Prüfebene und erwartetes Ergebnis | Nachweis / Status |
|---|---|---|---|
| AC-01 | G1 gemäß `docs/acceptance.md` | Nutzerprüfung GUI | ✅ Ralf, 2026-09-29 (inkl. FreeCAD schließen → `[bridge_unavailable]`) |
| AC-02 | G2 | Nutzerprüfung GUI | offen |
| AC-03 | G3 | Nutzerprüfung GUI | ✅ Agent (20 benannte Undo-Schritte) und Ralf (Menü „Bearbeiten → Rückgängig“), 2026-09-29 |
| AC-04 | G4 | Nutzerprüfung GUI | ✅ Agent, 2026-09-29 (Screenshots iso/top) |
| AC-05 | G5 | Nutzerprüfung GUI | ✅ Ralf, 2026-09-29 |
| AC-06 | G6 | Nutzerprüfung Slicer | offen |
| AC-07 | G7 | Sichtung TUI | ✅ Ralf, 2026-09-29 (zusammen mit G11) |
| AC-08 | G8 | Probedruck | offen |

Umsetzung folgt dem freigegebenen Spec-Stand. Browser-/manuelle Prüfungen zusätzlich nach der [Abnahmefreigabe](../../README.md#browser--und-manuelle-abnahmeprüfungen) behandeln; Spec-Freigabe ist keine Testfreigabe.

## Architektur-Impact

| Bereich | Einschätzung |
|---|---|
| `docs/architecture.md` | nicht betroffen |

## Relevante Dateien / Module

- `docs/acceptance.md`
- `examples/reference_projects.py`

## Abhängigkeiten

- Laufendes FreeCAD 26.3 mit installiertem Addon (`uv run poe install-addon`) und gestarteter TUI (`uv run freecad-buddy`).
- Slicer und Drucker für G6/G8.

## Notizen

- Im Live-Test angefangen, aber nicht fertig: Sieb-Raster in `out/Testplatte.FCStd` (918 Löcher Ø 1 mm, Raster 3 mm, Feld 100 × 80 mm, per `pattern kind="grid"`). Skizze und Start-Pocket existieren, das Raster fehlt noch. Kann als Prüflauf für G2 dienen.

## Übergabe an Sprint-Planung

- Architektur-Update-Artefakt nötig: nein
- Vermutete Ziel-Dokumente: keine
- Offene Klärungen vor Umsetzung: Auswahl der optionalen Prüfungen
