# Messlöffel für Kaffeeweißer-Pulver

Eine Kappe (ein Schöpfvorgang, bündig bis zur Randebene gefüllt) soll ungefähr einem gehäuften Standard-Teelöffel entsprechen. Interpretation von „Kappe“: die Löffelschale als Kugelkappe.

| | |
|---|---|
| **Modell (KI)** | Claude Sonnet 5.5 (`claude-sonnet-5-5`) |
| **Effort-Stufe** | max |
| **Werkzeuge** | FreeCAD Buddy (MCP, Bridge/Core 0.4.0) in FreeCAD 26.3.0 (rev 20260922), Python 3.13.15 |
| **Datum** | 2026-10-08 |
| **Dateien** | `Messloeffel.FCStd` (parametrisches PartDesign-Modell, 1 Body), `Messloeffel.3mf` (auf dem Druckbett platziert), `README.md` |

## Füllmenge (berechnet)

**8,01 ml** (8012,7 mm³), gestrichen bis zur Randebene.

- Formel Kugelkappe: V = π·h²·(3R − h)/3 mit R = 17,1 mm, h = 14,4 mm → 8012,7 mm³.
- CAD-Gegenprobe: Volumen vor und nach dem Kavitäten-Groove = 17616,785 − 9604,111 = 8012,674 mm³. Die −0,05 mm³ Differenz stammen vom Flachboden Ø 2 mm.
- Zielwert: gestrichener Teelöffel = 5 ml (metrisch; US 4,93 ml). Gehäuft ≈ 1,5–2 × davon = 7,5–10 ml (Faustwert, ungeprüft). Ausgelegt auf 8,0 ml, also etwa das 1,6-Fache eines gestrichenen Teelöffels.
- Empfindlichkeit (analytisch): 1 mm `Cap_Depth` ≈ 0,9 ml.
- Parametrik geprüft: Testlauf mit `Cap_SphereRadius` 17,5, `Cap_Depth` 15,0, `Handle_Width` 16, `Handle_Length` 120 → alle Features gültig, Kavität 8835,685 mm³ (CAD) gegen 8835,7 mm³ (Formel). Danach auf die Originalwerte zurückgesetzt (Bauteilvolumen wieder 9469,689 mm³).

## Maße (mm)

| Bereich | Wert |
|---|---|
| Gesamt (L × B × H) | 128,9 × 37,8 × 16,4 |
| Kavität | Kugelradius 17,1 (Kugelmittelpunkt 19,1 über dem Bett), Öffnung Ø 33,8, Tiefe 14,4 (real 14,37 durch Flachboden) |
| Wand / Boden | 2,0 / 2,0 (Außenkugel R 19,1 konzentrisch zur Kavität) |
| Rand | Außen Ø 37,8, Randbreite ≈ 2,0, scharfkantig zum Abstreichen |
| Fuß | Standfläche Ø 17,8, Kegel 50° zum Bett (= 40° Überhang zur Senkrechten, Grenze 45°), Übergang in die Außenkugel bei z = 6,82 |
| Griff | Länge 110 (Schalenachse bis Spitze), Breite 14, Dicke 4,0, Spitze rund (R 7) |
| Aufhängeloch | Ø 6,0, Mitte 9 von der Spitze |
| Fasen | 0,4 an allen bettseitigen Kanten (Fuß, Griffkontur, Aufhängeloch) |
| Bauteil | 9469,7 mm³ (9,47 cm³), PLA 1,24 g/cm³ → 11,74 g |

Druckausrichtung wie exportiert: Fuß und Griff flach auf dem Bett, Schale offen nach oben.

## Parameter (VarSet `Parameters`)

| Name | Wert | Rolle |
|---|---|---|
| `Cap_SphereRadius` | 17,1 | Radius der Kavitätskugel |
| `Cap_Depth` | 14,4 | Randebene = `Bowl_Floor` + `Cap_Depth` über dem Bett |
| `Cap_FlatRadius` | 1,0 | Flachboden statt Kugelpol (siehe Lücken) |
| `Bowl_Floor` | 2,0 | Bodenstärke |
| `Bowl_Wall` | 2,0 | Wandstärke |
| `Bowl_FootAngle` | 50° | Fußkegel zum Bett |
| `Handle_Length` / `Handle_Width` / `Handle_Thickness` | 110 / 14 / 4,0 | Griff |
| `Handle_HoleDiameter` / `Handle_HoleInset` | 6,0 / 9,0 | Aufhängeloch |
| `Print_BedChamfer` | 0,4 | Fase an den Bettkanten |

Feature-Reihenfolge: `Sketch_BowlOuter` → `Revolution_BowlOuter` → `Sketch_Handle` → `Pad_Handle` → `Sketch_CapCavity` → `Groove_CapCavity` → (Storepoint „Base body“) → `Sketch_HangHole` → `Pocket_HangHole` → `Chamfer_HangHoleBed` → `Chamfer_HandleBed` → `Chamfer_FootBed` → (Storepoint „Ready for export“). Alle Skizzen DoF 0.

## Prüfungen

- `check_printability`: ok, `issues: []`. Überhangfläche 0 mm², dünnste Wand (gesampelt) 2,0 mm, Bauraum 256³ eingehalten. Profil: PLA, Düse 0,4, Layer 0,2, min. Wand 0,8, Überhang 45°. Die ausgegebenen Hinweise (Fase gegen Elefantenfuß, Passungs-Clearance) sind generisch, keine Befunde.
- `export_body` 3MF: Datei re-importiert, Volumen 9467,862 mm³ gegen 9469,689 mm³ im Modell (−0,019 %, Tesselierung), keine Warnungen.

## Bekannte Lücken

1. **Zielvolumen ist eine Annahme.** „Gehäufter Teelöffel“ ist nicht genormt; 8,0 ml ist ein Faustwert. Rieselverhalten, Verdichtung und Böschungswinkel von Kaffeeweißer wurden nicht gemessen, ebenso keine Umrechnung ml → Gramm (Schüttdichte produktabhängig).
2. **Nur die gestrichene Füllung ist berechnet.** Die Menge über dem Rand (Schüttkegel) ist nicht modelliert.
3. **Kein Praxistest.** Weder gedruckt noch mit Wasser oder Pulver ausgemessen noch gesliced (keine Druckzeit, kein Filamentverbrauch). Maßabweichungen beim Druck wirken direkt aufs Volumen: ±0,1 mm Radius an der Innenfläche ≈ ±0,15 ml (Abschätzung).
4. **Lebensmittelkontakt nicht bewertet.** FDM-Oberflächen mit Schichtfugen sind schwer zu reinigen; keine Zertifizierung. Das Material ist im Profil PLA (die Materialbibliothek kennt kein PETG). PLA erweicht laut Literatur ab ca. 55–60 °C (ungeprüft), also nicht spülmaschinenfest.
5. **Funktion minimal.** Keine Skala, kein zweiter Messbecher, keine Beschriftung. Griff flach in Bodenhöhe (abgewinkelt wäre nur mit Support druckbar), Oberkanten des Griffs nicht verrundet. Ergonomie und Griffsteifigkeit (14 × 4 mm) nicht erprobt.
6. **Kavität mit Flachboden statt Kugelpol (Workaround).** Mit einem subtraktiven Kugel-Primitive brach `check_printability` mit „TypeError: undefined curve type“ ab; mit dem Groove-Profil (Flachboden Ø 2 mm) läuft die Prüfung. Ursache vermutet: degenerierte Polkante der Kugel (nicht direkt geprüft). Effekt: Tiefe −0,03 mm, Volumen −0,05 mm³.
7. **Fasen in drei Einzelschritten (Workaround).** Eine gemeinsame Fase aller Bettkanten erzeugte einen ungültigen Shape (Z-Minimum −10,4 mm, `valid: false`), obwohl das Tool Erfolg meldete. Einzeln (Aufhängeloch, Griffkontur, Fußkreis) ist jede Fase gültig. Ursache ungeprüft, vermutet an den konkaven Ecken zwischen Fuß und Griff.
8. **Selektoren ohne feste Radien.** Die Fasen nutzen `of_feature`/`line`-Selektoren; mit dem Parametertest oben wurden sie erfolgreich neu aufgelöst. Andere Extremwerte (z. B. sehr breiter Griff gegen kleinen Fuß) sind nicht getestet.
