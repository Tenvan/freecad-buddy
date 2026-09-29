# Grid-Lösungen für Loch- und Wabenraster — Recherche (#3.1, AC-10)

> Stand: 2026-09-29 │ Quelle: offizieller Addon-Katalog, lokaler Cache vom 2026-09-28 (438 Einträge, mit Ralfs Zustimmung in S3 geladen); READMEs von HexFill und Lattice2 am 2026-09-29 mit Ralfs Zustimmung live geladen │ Suche über `buddy_server.addon_catalog.search`, dieselbe Logik wie `search_addons`

## Frage

Gibt es im FreeCAD-Addon-Katalog eine fertige Lösung für Loch- und Wabenraster (Sieb, Lochblech, Lüftungsgitter), die im PartDesign-Workflow von FreeCAD Buddy taugt? Oder braucht es ein eigenes Design-Tool?

## Suchbegriffe und Treffer

| Begriff | Treffer (Ranking) |
|---|---|
| grid | BSurf from grid, FreeGrid, Gridfinity, CarteGrid, Plot, ArrayCopy, FCHoneycombMaker, HexFill |
| array | ArrayCopy, lattice2, GetGlobalPlacement |
| lattice | lattice2, RotaryMoulder |
| pattern | HexFill, RotaryMoulder |
| perforation | HexFill |
| sieve | – |
| gridfinity | Gridfinity |
| honeycomb (Zusatz) | Honeycomb, FCHoneycombMaker, HoneycombSolid, HexFill |

Themenfremd und daher aussortiert: BSurf from grid (Flächen), Plot (Diagramme), CarteGrid (Variantenexport über ein VarSet-Parameterraster), GetGlobalPlacement, RotaryMoulder (Keksrollen).

## Bewertung

Bewertet werden PartDesign-Tauglichkeit, Parametrik, Lizenz, Pflege, Kompatibilität mit 26.3 und Portabilität (braucht jede Person, die die Datei öffnet, das Addon?). Die Angaben zu Lizenz, Pflege und Kompatibilität stammen aus dem Katalog. Für HexFill und Lattice2 stammen die Angaben zur Arbeitsweise aus dem README, für alle anderen aus der Katalogbeschreibung. Getestet ist keine Installation, deshalb bleibt alles **ungeprüft**, was nicht ausdrücklich im README steht.

| Kandidat | Art | PartDesign | Parametrik | Lizenz | Pflege | 26.3 | Portabilität |
|---|---|---|---|---|---|---|---|
| **HexFill** | Addon | ✅ erzeugt eine normale Skizze `HexGrid`, danach natives Pocket/Pad (README) | ❌ Zellgröße und Steg werden einmalig im Dialog gesetzt; eine Nachführung bei Parameteränderung beschreibt das README nicht | MIT | aktiv (1.2.5, 2026-08-19) | ✅ (≥ 1.0) | ✅ normale Skizze (README) |
| Honeycomb | Makro | ⚠️ FeaturePython-Objekt „in und außerhalb von PartDesign“ | ✅ | – (Wiki) | 2024-08 | vermutet ✅ | ❌ Datei braucht das Makro zum Neuberechnen |
| FCHoneycombMaker | Makro | ⚠️ unklar | ✅ laut Beschreibung | – (Wiki) | ❌ 2020-10 | ungeprüft | ungeprüft |
| HoneycombSolid | Makro | ❌ Part-Solid | ❌ | LGPL-2.0+ | unbekannt | ungeprüft | ✅ (statischer Körper) |
| lattice2 | Workbench | ⚠️ Arrays aus Placements, die mit Formen befüllt werden; laut README „erweitert den PartDesign-Workflow“ durch Wiederverwendung von Feature-Folgen, aber über eigene Lattice-Objekte | ✅ | LGPL-2.0+ | aktiv (2026-07-15) | ✅ | ❌ braucht Lattice2 |
| ArrayCopy | Makro | ❌ Kopien von Objekten | ❌ | – | ❌ 2014 | ungeprüft | ✅ |
| Gridfinity | Workbench | eigene Objekte, Domäne Aufbewahrungssystem | ✅ | LGPL-2.1+ | 2026-03 | ✅ | ❌ |
| FreeGrid | Workbench | eigene Objekte, Domäne Aufbewahrungssystem | ✅ | AGPL-3.0+ | 2025-01 | ✅ | ❌ |
| *nativ: PartDesign MultiTransform* | FreeCAD | ✅ | ✅ über Expressions | LGPL (FreeCAD) | FreeCAD | ✅ | ✅ keine Abhängigkeit |

## README-Befund HexFill (2026-09-29)

- **Bedienung:** Nur über die GUI. Der Button steht in der Sketcher-Workbench: Skizze wählen, Zellgröße im Aufgabenbereich mit Live-Vorschau einstellen, OK. Eine Python- oder Makro-Schnittstelle dokumentiert das README nicht. Ein Buddy-Tool könnte HexFill deshalb nur über dessen interne Module ansteuern, mit demselben Bruchrisiko wie beim Addon Manager (vermutet).
- **Ergebnis:** Eine neue, normale Skizze `HexGrid`, die an der Ausgangsskizze hängt (seit 1.2.5). Danach Pocket oder Pad. Die Datei bleibt ohne HexFill öffnen- und berechenbar.
- **Parametrik:** Zellgröße, Steg, Ausrichtung, Anker und Rand werden einmalig im Dialog gesetzt. Dass die Waben einer späteren Maßänderung folgen, steht nirgends. Vermutet ist ein Neuaufruf nötig, und ob die Skizze vollständig bestimmt ist, ist offen.
- **Stärken, die `fill_pattern` nicht hat:** Füllt beliebige Konturen innen oder außen, spart bestehende Ausschnitte und Bohrungen automatisch aus, beschneidet Randzellen (Outfill), setzt einen Rand zu Kontur und Kante (experimentell).

## Empfehlung und Entscheidung

**Entschieden (Ralf, 2026-09-29): kein Addon.** Loch- und Wabenraster baut `fill_pattern` mit `cell="round"` oder `cell="hex"`, rein nativ (Startzelle, Pocket, MultiTransform), parametrisch, per MCP steuerbar und ohne Addon-Abhängigkeit in der Datei. HexFill wird weder angesteuert noch empfohlen: Es ist GUI-only und nicht parametrisch. lattice2, Gridfinity, FreeGrid und Honeycomb bringen eigene Objekttypen in die Datei.

## Folgen fürs Regelwerk

- Thema `design_tools`: `fill_pattern` für Sieb-, Loch- und Wabenraster (`cell` round oder hex).
- Thema `addons`: Unterscheidung zwischen Addons, die nur Skizzen oder native Features erzeugen (unkritisch), und Addons mit eigenen Objekttypen (Datei hängt vom Addon ab). Ist in S5 ergänzt.
