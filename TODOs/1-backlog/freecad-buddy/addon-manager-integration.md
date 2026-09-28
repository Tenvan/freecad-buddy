# Addon-Manager-Integration: fertige Lösungen suchen und installieren

> Erstellt: 2026-09-28 │ Status: 🔵 Eingeplant → Sprint [`freecad-buddy-design-regelwerk`](../../2-sprints-aktiv/freecad-buddy-design-regelwerk/00-index.md) │ Priorität: hoch │ Architektur-Impact: mehrere

## Spezifikation

> Spec-Stand: 1 │ Spec-Status: Freigegeben │ Freigabe: durch Ralf im Chat, 2026-09-28 (über den Sprint-Index)

Vollständige Spezifikation, Kriterien und Aufgaben stehen im Sprint-Index (AC-06 bis AC-09). Dieses Ticket hält nur den Auftrag fest.

## Ausgangslage

FreeCAD 26.3 bringt den Addon Manager 2026.8.18 mit. Er nutzt seit FreeCAD 1.1 einen zentralen Katalog (`https://addons.freecad.org/addon_catalog_cache.zip` mit `.sha256`, Makros über `macro_cache.zip`), einen lokalen Cache (`<UserCache>/AddonManager2026-1`) und die Installer-Klassen `AddonInstaller` und `MacroInstaller`. Auf diesem Rechner wurde der Katalog noch nie geladen (kein lokaler Cache vorhanden, Stand 2026-09-28).

## Auftrag (Ralf, 2026-09-28)

- MCP um die Möglichkeit erweitern, im Addon Manager nach fertigen Lösungen zu suchen und sie zu installieren.

## Vorentscheidungen (Ralf, 2026-09-28)

- Suche und Details sind immer verfügbar. Die Installation braucht ein Opt-in (analog zu `execute_python`) und zusätzlich die Bestätigung in einem FreeCAD-Dialog. Installiert wird über FreeCADs eigenen Installer.
