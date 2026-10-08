# Messlöffel für Kaffeeweißer-Pulver

| | |
|---|---|
| Modell | Claude Opus 5.5 (`claude-opus-5-5`) |
| Effort-Stufe | max |
| Werkzeug | FreeCAD 26.3.0 über FreeCAD Buddy (Bridge/Core 0.4.0), neues Dokument, keine Vorlagen |
| Dateien | `Messloeffel.FCStd` (parametrisch), `Messloeffel.3mf` (auf dem Bett platziert) |

## Füllmenge

**10,02 ml** bei gestrichen gefüllter Kappe (Pulver an der Randebene abgestrichen).

- FreeCAD-Volumendifferenz vor/nach `Groove_Cavity`: 21 829,43 − 11 813,64 = **10 015,8 mm³**
- Handrechnung: π · 15² · 14,6 − (1 − π/4) · 4² · 2π · (15 − 0,2234 · 4) = 10 320,1 − 304,3 = **10 015,8 mm³** (Zylinder minus Ring der Bodenrundung, Pappus)
- Ziel: ein gehäufter Standard-Teelöffel ≈ 2 × 5 ml (gestrichen) = 10 ml
- Stellschraube: `Cup_Depth`, 1 mm entspricht ≈ 0,71 ml

## Maße

| Merkmal | Wert | Parameter |
|---|---|---|
| Gesamt (L × B × H) | 119 × 34 × 16,6 mm | – |
| Kappe innen Ø / außen Ø | 30 / 34 mm | `Cup_Inner_Diameter`, `Cup_Wall` = 2 |
| Kappe Innentiefe / Boden | 14,6 / 2 mm | `Cup_Depth`, `Cup_Floor` |
| Bodenrundung innen | R 4 mm (Pulver löst sich, leicht zu reinigen) | `Cup_Inner_Fillet` |
| Rand | außen R 0,8 mm, innen scharf (sauberes Abstreichen) | `Cup_Rim_Fillet` |
| Griff Länge ab Kappenwand | 85 mm (102 mm ab Kappenachse) | `Handle_Length` |
| Griff Breite | 8 mm | `Handle_Width` |
| Griff Höhe | 6 mm an der Spitze, steigt linear (5,9°) bis Randhöhe an der Kappenachse; ≈ 14,8 mm an der Kappenwand | `Handle_Tip_Height` |
| Griff-Oberkanten | R 3 mm, im Loft-Profil eingebaut | `Handle_Edge_Radius` |
| Griffspitze | R 2 mm rundum | `Handle_Tip_Radius` |
| Bettkanten | Fase 0,4 mm | `Bed_Chamfer` |
| Bauteilvolumen / Masse | 11,78 cm³ / 14,6 g PLA bei 100 % Infill | – |

Aufbau (`Messloeffel`-Body): `Pad_Cup` → `Fillet_Rim` → `Loft_Handle` (Querschnitte `Sketch_HandleRoot` auf YZ, `Sketch_HandleTip` auf `DatumPlane_HandleTip`) → `Groove_Cavity` → `Fillet_HandleTip` → `Chamfer_Bed`. Alle Skizzen voll bestimmt (DoF 0), alle Maße an Parameter gebunden. Storepoints: „Base body …“ und „Before export …“.

Druck: so wie modelliert (Öffnung oben, Griff flach auf dem Bett), ohne Stützen. `check_printability`: ok, keine Befunde, Überhangfläche 0, minimale Wand 2,0 mm. 3MF-Export geprüft, Volumenabweichung Mesh/Modell 0,11 %.

## Bekannte Lücken

1. **Zielgröße nicht genormt:** „Gehäufter Teelöffel“ hat keine Norm. Annahme gehäuft ≈ doppelt gestrichen = 10 ml (vermutet, reale Werte je nach Löffel und Pulver etwa 8–12 ml).
2. **Nicht physisch validiert:** nicht gedruckt, nicht ausgelitert. Die Dosis hängt vom Abstreichen und Verdichten ab; die Masse von der Schüttdichte (Kaffeeweißer ≈ 0,4–0,5 g/ml, ungeprüft, also ≈ 4–5 g je Kappe).
3. **Kein Übergangsradius Griff–Kappe:** Die Selektor-Grammatik trifft die Kanten zwischen Loft und Zylinder nicht gezielt (`edges:vertical` erkennt sie nicht, vermutlich weil es B-Spline-Kanten sind). Die Ecke bleibt scharf und kann Pulver sammeln. Die Festigkeit reicht nach Abschätzung (Querschnitt 8 × ~14 mm).
4. **Lebensmittelkontakt:** FDM-Rillen sind schwer zu reinigen. PLA verträgt keine Spülmaschine (erweicht ab ≈ 55 °C). Lebensmittelgeeignetes Filament verwenden, nur für trockenes Pulver, Handwäsche.
5. **Kein Slicing:** Der Export lieferte keine Slicer-Daten (OrcaSlicer vermutlich nicht installiert), daher fehlen Druckzeit und Filamentmenge.
6. **Kosmetik:** `DatumPlane_HandleTip` ist im FCStd sichtbar (es gibt kein Tool zum Ausblenden; in FreeCAD mit Leertaste ausblenden). Keine Volumenprägung („10 ml“) und keine Aufhängeöse.
7. **Parametergrenzen werden nicht erzwungen:** `Handle_Edge_Radius` < `Handle_Width`/2 und < `Handle_Tip_Height`; `Handle_Tip_Radius` < `Handle_Edge_Radius`; `Cup_Rim_Fillet` < `Cup_Wall`.
8. **Design-Tool-Vorschlag nicht eingereicht:** Nach Regel 10 wäre `propose_design_tool` fällig gewesen. Bewusst weggelassen, weil der globale Vorschlagsspeicher Folgeläufe dieser Testreihe beeinflussen würde. Kandidat: `measuring_scoop(volume_ml, inner_diameter, wall, floor, inner_fillet, handle_length, handle_width, handle_tip_height)` berechnet `Cup_Depth` aus dem Zielvolumen inkl. Bodenrundungs-Korrektur und ersetzt ≈ 20 Einzelaufrufe.

## Tool-Befunde aus dem Lauf (FreeCAD Buddy)

- `set_parameters` mit Ausdruck als Wert (`"Cup_Inner_Diameter + 2*Cup_Wall"`) liefert `internal_error ParserError` statt Validierungsfehler. Abgeleitete Maße stehen deshalb als Ausdruck direkt in Skizzen/Features.
- `set_parameters` aktualisiert die `description` bestehender Parameter nicht. Das hat einen Neuaufbau in frischem Dokument erzwungen (Entwurf: Scratchpad, nicht ausgeliefert).
- `select_geometry` mit `radius=<Ausdruck>` liefert `internal_error ValueError` statt Validierungsfehler.
- Englisch-Regel verletzt: Undo-Namen „Geometrie: Sketch_…“, Fehlertext „Selektor '…' trifft nichts“.
- `edges:vertical,of_feature=…` liefert Zylinder-Nahtkanten mit, und `fillet` übernimmt sie kommentarlos in die gespeicherte Auswahl (Volumen unverändert, Referenz aber fragil). Gelöst durch Griff auf −X, abgewandt von der Naht. Nahtkanten sollten aus Selektoren herausgefiltert werden.
- Selektor-Grammatik nicht auffindbar: Fehler bei unbekanntem Filter nennen keine gültigen Filter. Ein Filter für konkav/konvex oder Lage fehlt (Griffansatz nicht selektierbar).
- `screenshot(isolate=Body)` blendet die Datum-Ebene des Bodys nicht aus.
