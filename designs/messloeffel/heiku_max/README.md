# Messlöffel für Kaffeeweißer-Pulver

Testlauf `heiku_max`: Entwurf mit FreeCAD Buddy in einem neuen Dokument.

## Modell

- **Modell:** Claude Haiku 5.5 (`claude-haiku-5-5`)
- **Effort-Stufe:** max (vermutet: aus dem Ordnernamen `heiku_max` abgeleitet, im Session-Kontext nicht ausgewiesen, ungeprüft)
- **Werkzeug:** FreeCAD Buddy, FreeCAD 26.3.0, Bridge 0.4.0
- **Isolation:** Nur Prompt und FreeCAD-Tools verwendet. Keine bestehenden Dateien oder Ordner geöffnet, gelesen oder durchsucht. Keine Gedächtnisnotizen genutzt. Der Zielordner wurde vorab nur auf Existenz geprüft (nicht vorhanden) und dann angelegt.

## Annahmen

- **„Kappe“** = Messmulde: zylindrischer Becher mit ebenem Boden. Gefüllt wird bündig bis zur Oberkante.
- **Zielvolumen:** gehäufter Standard-Teelöffel = 1,5 × 5 ml = **7,5 ml** (vermutet, ungeprüft; keine Recherche laut Isolation).

## Maße

| Bauteil | Maß | Wert |
|---|---|---|
| Kappe | Außendurchmesser | 36,6 mm |
| Kappe | Höhe (Bett bis Oberkante) | 14,0 mm |
| Kappe | Wandstärke | 3,0 mm |
| Mulde | Durchmesser | 30,6 mm |
| Mulde | Tiefe | 10,2 mm |
| Kappe | Bodendicke unter der Mulde | 3,8 mm |
| Griff | Breite | 22,0 mm |
| Griff | Stärke | 4,0 mm |
| Griff | Länge ab Kappenmitte | 120,0 mm |
| Gesamt | Länge (Kappenaußenkante bis Griffspitze) | 138,3 mm |
| Gesamt | Breite / Höhe | 36,6 mm / 14,0 mm |

## Füllmenge

- Berechnet: π · r² · h = π · (15,3 mm)² · 10,2 mm = 7 501,2 mm³ = **7,50 ml**
- Gegenprobe in FreeCAD: Volumen `Pad_Handle` 23 781,89 mm³ − Volumen Körper 16 280,66 mm³ = 7 501,24 mm³. Stimmt überein.
- Die Zylindermulde hat dasselbe Volumen wie eine Halbkugel mit r = 15,3 mm, weil h = 2/3 · r gilt. Die Kugelvariante wurde verworfen (siehe Werkzeug-Befunde).

## Modellaufbau

| Feature | Quelle | Inhalt |
|---|---|---|
| `Pad_Cup` | `Sketch_Cup` | Kreis Ø `Cup_Outer_Dia`, Höhe `Cup_Height` |
| `Pad_Handle` | `Sketch_Handle` | Rechteck `Handle_Length` × `Handle_Width`, Stärke `Handle_Thickness`, Stirnseite innerhalb der Kappe |
| `Pocket_Cavity` | `Sketch_Cavity` | Kreis Ø `Cup_Cavity_Dia` auf der Oberkante, Tiefe `Cup_Cavity_Depth` |

Die Parameter liegen im VarSet `Parameters`.

## Druckbarkeit

- **check_printability:** ok, 0 Befunde. Überhangfläche 0 mm², Überhangsanteil 0, minimale Wanddicke (Stichprobe) 3,0 mm.
- **Hinweise ohne Befund:** Bodenkante mit ca. 0,4 mm chamfern (Elefantenfuß). Nicht umgesetzt. Der Passungshinweis ist nicht relevant, da es keine Bohrungen oder Passungen gibt.
- **Export:** 3MF, auf dem Bett platziert. Volumen Modell 16 280,66 mm³, Datei 16 278,04 mm³, Abweichung 0,016 %. Kein Slicer-Lauf.
- **Druckprofil:** PLA, 0,4 mm Düse, 0,2 mm Schichthöhe.

## Bekannte Lücken

1. **Volumen ist geometrisch.** Die Füllmenge gilt in ml, nicht in Gramm. Schüttdichte und Setzverhalten des Pulvers sind nicht berücksichtigt und nicht getestet.
2. **„Gehäuft“ ist nicht modelliert.** Die Kappe fasst 7,5 ml bis zur Oberkante. Ein Haufen über dem Rand fehlt. Die flache Oberkante dient als Abstreifkante.
3. **Kein Elefantenfuß-Chamfer.** Der Checker empfiehlt 0,4 mm, umgesetzt ist er nicht.
4. **Griffspitze eckig.** Ohne Radius. Die Slot-Variante mit Rundung wurde verworfen (siehe Werkzeug-Befunde).
5. **Abgeleitete Parameter sind manuell zu pflegen.** `set_parameters` akzeptiert nur Zahlen. Deshalb stehen `Cup_Cavity_Dia` (= 2 · Radius), `Cup_Outer_Dia` (= 2 · (Radius + Wand)), `Handle_Center_X` (= Länge / 2) und `Cup_Cavity_Depth` (= 2/3 · Radius) als feste Zahlen drin. Bei Änderungen in FreeCAD die Ausdrücke nachtragen.
6. **Parameterreste.** `Handle_Slot_Length` ist ungenutzt, Rest der verworfenen Slot-Variante. Die Beschreibungen von `Handle_Center_X` und `Handle_Slot_Length` sind veraltet, ein Update per `set_parameters` hat sie nicht geändert. Löschen geht nur in FreeCAD.
7. **Keine Griffbohrung, kein Aufhängeloch.**
8. **Material und Lebensmittelkontakt nicht geprüft.** PLA laut Druckprofil. Eignung für Lebensmittelkontakt ist nicht bewertet.
9. **Keine Toleranzen oder Schrumpfung berücksichtigt.** Keine Druckprobe.

## Werkzeug-Befunde (FreeCAD Buddy)

- **check_printability schlägt mit Kugelmulde fehl:** `[internal_error] TypeError: undefined curve type`. Reproduziert mit Slot-Griff und mit Rechteck-Griff, also mit der Kugelmulde (`PartDesign::SubtractiveSphere`). Mit der Zylindermulde (`Pocket`) läuft der Check durch. Vermutung (ungeprüft): entartete Polkante am Muldenboden. Nicht verifiziert.
- **set_parameters:** nimmt nur Zahl oder Bool. Ausdrücke werden abgelehnt: als Wert ohne Objektform mit Validierungsfehler, in Objektform mit `ParserError`.
- **Undo:** ein Tool-Aufruf entspricht einem Undo-Schritt. Die verworfenen Schritte (Kugelmulde, Slot-Griff) wurden per `undo` zurückgenommen. Das gespeicherte Dokument enthält nur den finalen Stand.

## Dateien

- `Messloeffel.FCStd`: Dokument mit Body `Messloeffel` und Parametern
- `Messloeffel.3mf`: Export, auf dem Bett platziert
- `README.md`: diese Datei
