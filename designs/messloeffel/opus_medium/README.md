# Messlöffel für Kaffeeweißer

- Modell: Claude Opus 5.5 (`claude-opus-5-5`)
- Effort-Stufe: medium
- Werkzeug: FreeCAD 26.3 über FreeCAD-Buddy-MCP-Tools (PartDesign, ein Body, alle Sketches DoF 0)

## Maße (Parameter im VarSet `Parameters`)

| Parameter | Wert |
|---|---|
| Cup_Inner_Diameter | 26 mm |
| Cup_Depth | 15 mm |
| Wall (Wand + Boden) | 2 mm |
| Becher außen | Ø 30 mm × 17 mm |
| Handle_Length (ab Bechermitte) | 80 mm |
| Handle_Width | 12 mm |
| Handle_Thickness | 3 mm |
| Handle_Radius | 5 mm |
| Inner_Fillet (Mulde unten) | 3 mm |
| Bodenfase | 0,4 mm |

Gesamtmaß: 95 × 30 × 17 mm, Bauteilvolumen 6,51 cm³ (PLA, druckbar ohne Support, Becheröffnung nach oben).

## Füllmenge

- Zylinder: π · 13² · 15 = 7964 mm³
- abzüglich Kehle unten (R 3): −150 mm³ (aus FreeCAD-Volumendifferenz)
- **Füllmenge glatt gestrichen: ≈ 7,8 ml**

Ziel: ein gehäufter Teelöffel ≈ 7–10 ml (gestrichen 5 ml). Eine glatt gestrichene Kappe liegt im unteren Bereich davon.

## Bekannte Lücken

- „Gehäufter Teelöffel“ ist nicht normiert; der Zielwert 7–10 ml ist eine Annahme, nicht gemessen. Für mehr Füllmenge `Cup_Depth` erhöhen (+1 mm ≈ +0,53 ml).
- Die Kehle wählt die Kante über `z=2` aus – nach Änderung von `Wall` kann der Selektor ins Leere laufen.
- Oberer Becherrand ist scharfkantig (keine Verrundung).
- Griff ist flach (3 mm), keine Versteifungsrippe; bei PETG/PLA unkritisch für Pulver, nicht für Hebelbelastung getestet.
- Keine Lebensmittelzertifizierung: FDM-Drucke haben Riefen; lebensmittelechtes Filament verwenden.
- Kein Slicing durchgeführt (Druckzeit/Filament nicht ermittelt).
