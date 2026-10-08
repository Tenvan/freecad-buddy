# Messlöffel für Kaffeeweißer-Pulver

```Prompt
Aufgabe: Entwirf in FreeCAD über die FreeCAD-Buddy-Tools einen Messlöffel für Kaffeeweißer-Pulver. Eine Kappe soll ungefähr einem gehäuften Standard-Teelöffel entsprechen.

Isolation (verbindlich):
- Nutze nur diesen Prompt und die FreeCAD-Tools. Öffne, lies oder durchsuche keine bestehenden Dateien oder Ordner, insbesondere nicht designs/, models/ oder Exporte früherer Läufe.
- Nutze kein Wissen aus früheren Sitzungen oder Gedächtnisnotizen.
- Lege ein neues Dokument an. Öffne kein bestehendes.

Ausgabe:
- Ordner: C:\WORKSPACE\messloeffel-test\{MODELL}_{EFFORT}\
- Dateien: Messloeffel.FCStd und Messloeffel.3mf
- README.md mit: Modell, Effort-Stufe, Maße, berechnete Füllmenge in ml, bekannte Lücken

Melde am Ende nur: Pfade, Füllmenge, Ergebnis von check_printability.
```

Becher mit Stiel, Füllmenge bis zur Kante ≈ 7,5 ml (entspricht einem gehäuften Teelöffel; gestrichen ≈ 5 ml).
Erstellt mit FreeCAD Buddy (Modell: Sonnet 5.5, Effort medium).

## Dateien

| Datei | Inhalt |
|---|---|
| `Messloeffel_sonnet_5_5_medium.FCStd` | Parametrisches FreeCAD-Modell (PartDesign, Body `Scoop`) |
| `Messloeffel_Scoop_sonnet_5_5_medium.3mf` | Druckfertiger Export (per `.gitignore` nicht versioniert; aus der FCStd neu exportierbar) |

## Maße

| Parameter | Wert | Hinweis |
|---|---|---|
| `Cup_ID` | 30 mm | Innendurchmesser |
| `Cup_Depth` | 10,6 mm | Innentiefe; π·15²·10,6 ≈ 7,5 ml. Für 5 ml gestrichen: 7,1 mm |
| `Wall` / `Floor` | 1,6 mm | Wand / Boden |
| `Cup_OD` | 33,2 mm | abgeleitet: `Cup_ID + 2·Wall`, bei Änderung von Hand nachziehen |
| `Cup_Height` | 12,2 mm | abgeleitet: `Cup_Depth + Floor`, bei Änderung von Hand nachziehen |
| `Handle_Length` / `Handle_Width` / `Handle_Thick` | 80 / 14 / 4 mm | Stiel |
| `Hang_Hole` | 6 mm | Aufhängeloch am Stielende |

Gesamtgröße ca. 106,6 × 33,1 × 12,2 mm, Volumen ≈ 6988 mm³.

## Druck

- Flach auf dem Bett, Öffnung nach oben, keine Stützen, keine Überhänge.
- 0,4-mm-Fase an der Unterkante gegen Elefantenfuß.
- Material: lebensmittelecht nur mit geeignetem Filament; FDM-Oberflächen sind porös, daher nur für trockenes Pulver und von Hand spülen.
- `check_printability` (Profil: 0,4-mm-Düse, 0,2 mm Layer, PLA): keine Befunde, dünnste Wand 1,6 mm.

## Bekannte Lücken

- Kein Innenradius am Becherboden (Fillet-Selector traf nur Seam-Kanten).
- Füllmenge rechnerisch aus Volumendifferenz, nicht per Wasserfüllung geprüft.
