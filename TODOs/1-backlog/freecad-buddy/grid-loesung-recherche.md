# Recherche: fertige Grid-Lösung im Addon-Katalog

> Erstellt: 2026-09-28 │ Status: 🔵 Eingeplant → Sprint [`freecad-buddy-design-regelwerk`](../../2-sprints-aktiv/freecad-buddy-design-regelwerk/00-index.md) │ Priorität: mittel │ Architektur-Impact: keiner

## Spezifikation

> Spec-Stand: 1 │ Spec-Status: Freigegeben │ Freigabe: durch Ralf im Chat, 2026-09-28 (über den Sprint-Index)

Vollständige Spezifikation im Sprint-Index (AC-10, AC-11). Dieses Ticket hält nur den Auftrag fest.

## Ausgangslage

Das Sieb der Testplatte (918 Löcher Ø 1 mm, Raster 3 mm) brauchte ein 2D-Raster. PartDesign kann kein Muster auf ein Muster legen; gelöst wurde das mit `pattern kind="grid"` (MultiTransform). Offen ist, ob es im Addon-Katalog eine fertige, bessere Lösung gibt.

## Auftrag (Ralf, 2026-09-28)

- Als Beispiel für die Addon-Suche prüfen, ob es eine fertige Grid-Lösung gibt.

## Notizen

- Kandidaten, vermutet und ungeprüft: Lattice2 (Arrays, allerdings Part-basiert), Gridfinity-Workbench (Gridfinity-Behälter, kein Lochraster). Bewertet wird PartDesign-Tauglichkeit, Parametrik, Lizenz, Pflege und Kompatibilität mit 26.3.
