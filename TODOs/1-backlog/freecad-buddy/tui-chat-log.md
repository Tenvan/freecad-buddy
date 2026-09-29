# TUI: Tool-Log als farbige Chat-Ansicht mit Anfrage und Antwort

> Erstellt: 2026-09-28 │ Status: ✅ Umgesetzt im Sprint [`freecad-buddy-design-regelwerk`](../../3-sprints-erledigt/2026-09-freecad-buddy-design-regelwerk/00-index.md) (2026-09-29) │ Priorität: hoch │ Architektur-Impact: server

## Spezifikation

> Spec-Stand: 1 │ Spec-Status: Freigegeben │ Freigabe: durch Ralf im Chat, 2026-09-28 (über den Sprint-Index)

Vollständige Spezifikation im Sprint-Index (R-11, AC-14, AC-15). Dieses Ticket hält nur den Auftrag fest.

## Ausgangslage

Das Tool-Log der TUI zeigt pro Aufruf nur eine Zeile: Zeit, Tool, ok/FEHLER, Dauer und eine Kurzfassung. Das Event `ToolFinished` (`src/buddy_server/events.py`) trägt weder die Argumente noch die Antwort.

## Auftrag (Ralf, 2026-09-28)

- Tool-Logging deutlich ausbauen: Im Log soll stehen, was angefragt und welche Antwort geschickt wurde, am besten als farbige Chat-Ansicht.
