# Messlöffel Kaffeeweißer

- **Modell:** Claude Sonnet 5.5, FreeCAD Buddy (PartDesign, 1 Body `Messloeffel`)
- **Effort-Stufe:** medium

## Aufbau
Pad_Cup (Zylinder Ø25,2 × 17,6) → Pad_Handle (Rechteck 105 × 12, R4, 3,5 dick) → Pocket_Bowl (Ø22 × 16 tief). Alle Maße als Parameter im VarSet `Parameters`.

## Maße (mm)
| Parameter | Wert |
|---|---|
| Innendurchmesser Kappe | 22 |
| Innentiefe | 16 |
| Wand / Boden | 1,6 / 1,6 |
| Außen-Ø / Höhe | 25,2 / 17,6 |
| Griff L × B × D | 105 × 12 × 3,5 (ab x=0, überlappt Kappe) |
| Gesamtgröße | 117,6 × 25,0 × 17,6 |

## Füllmenge
π · 11² · 16 = 6082 mm³ ≈ **6,1 ml** bis zum Rand (Pocket-Volumendifferenz im Modell: 6082,1 mm³). Gestrichen ≈ 6,1 ml, entspricht einem gehäuften Teelöffel (~5 ml gestrichen, ~6–7 ml gehäuft).

## Printability
`check_printability`: keine Befunde, Überhang 0, Wandstärke min. 1,6 mm. Export 3mf: Abweichung 0,07 %.

## Bekannte Lücken
- Zylindrische Kappe statt löffelartiger Form; keine Verrundungen/Fase (Hinweis: Bodenkante 0,4 mm Fase gegen Elephant Foot).
- Füllmenge rein geometrisch bis Rand, Pulver-Schüttdichte/Häufung nicht berücksichtigt.
- Abgeleitete Maße (Außen-Ø, Höhe) sind Zahlen, keine Ausdrücke – bei Parameteränderung manuell nachziehen.
- Kein Slicing, keine Praxistests; Griffansatz an der Kappe ohne Verrundung.
