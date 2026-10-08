# Messlöffel für Kaffeeweißer-Pulver (Testlauf haiku_medium)

## Modell
- Dokument: `Messloeffel.FCStd`, Body `Messloeffel`
- Export: `Messloeffel.3mf` (platziert auf dem Bett)
- Features: `Pad_Handle` → `Pad_Cup` → `Pocket_Cavity` (Skizzen: `Sketch_Handle`, `Sketch_Cup`, `Sketch_Cavity`)

## Effort-Stufe
- medium (laut Auftrag/Ordnername)

## Maße
Parameter in der VarSet `Parameters`:

| Parameter | Wert | Bedeutung |
|---|---|---|
| `Cup_OuterDia` | 30 mm | Außendurchmesser der Kappe |
| `Cup_InnerDia` | 23 mm | Innendurchmesser der Mulde |
| `Cup_Height` | 20 mm | Höhe der Kappe |
| `Cup_Floor` | 3 mm | Bodenstärke |
| `Cup_Depth` | 17 mm | Tiefe der Mulde (Höhe − Boden) |
| `Handle_Length` | 90 mm | Länge des Griffs ab Kappenmitte |
| `Handle_Width` | 10 mm | Griffbreite |
| `Handle_Thickness` | 4 mm | Griffstärke |

Gesamtmaße (Bounding Box): 105 × 30 × 20 mm

## Füllmenge
- Mulde: π · (11,5 mm)² · 17 mm ≈ **7,06 ml** (FreeCAD-Volumendifferenz vor/nach `Pocket_Cavity`: 7 063 mm³)
- Ziel laut Auftrag: ungefähr ein gehäufter Standard-Teelöffel.
- Annahme (ungeprüft): gehäufter Standard-Teelöffel ≈ 7 ml. Ein Standard-Teelöffel gilt mit 5 ml als gestrichen; die Häufung ist eine Schätzung.
- Kaffeeweißer-Pulver hat eine Schüttdichte, die je nach Marke stark schwankt. Das Gewicht pro Kappe ist daher nicht berechnet und nicht gemessen.

## Prüfung
- `check_printability`: keine Befunde (`issues: []`), Überhang 0 %, minimale Wandstärke ≈ 3,0 mm, Volumen 10 085 mm³.
- Export-Check: Volumen Modell 10 085 mm³, Datei 10 076 mm³, Abweichung 0,10 %.

## Bekannte Lücken
- Die Kappe ist nur ein Zylinder mit Flachboden. Keine Schaufel-Rundung und keine Entnahmeschräge. Das Pulver lässt sich eventuell schlecht abstreichen.
- Füllmenge nur geometrisch berechnet. Keine Messung mit realem Pulver.
- Die Griffmitte (`Handle_CenterX` = 45) ist ein fester Zahlenwert und nicht an einen Parameter gebunden (Lint-Info aus `analyze_sketch`).
- Keine Unterkante-Fase. Der Hinweis aus `check_printability` (0,4 mm Fase gegen Elephant Foot) wurde nicht umgesetzt.
- Griffstärke 4 mm ist für PLA-Biegung unter Last ungeprüft.
- Keine Slicer-Prüfung (Druckzeit, Filament) durchgeführt.
- Keine Sichtprüfung per Screenshot durchgeführt.
