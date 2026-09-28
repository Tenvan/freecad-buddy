# Sample: Referenzmodell

Mitwachsende Referenzaufgabe, mit der sich LLMs und Thinking-Stufen an FreeCAD Buddy vergleichen lassen. Das Modell wird in **Stufen** ausgebaut. Jede Stufe bringt neue Features, Parameter und Prüfungen mit, frühere Stufen bleiben unverändert. Ergebnisse derselben Stufe sind deshalb immer vergleichbar.

Die Aufgabe ist deterministisch:
- Der Prompt legt alle Maße und Parameternamen fest.
- Die Prüfung ([`referenzmodell.py`](referenzmodell.py) `check`) bewertet ausschließlich Tool-Ergebnisse.
- Einzige Quelle für Prompt, Soll-Werte und Referenzlösung ist das Skript. Dieses Dokument zeigt sie nur an, ein Test hält beides gleich.

![Referenzmodell Stufe 4, isometrisch](referenzmodell.png)

*Aktueller Stand: Stufe 4, 2026-09-28, FreeCAD 26.3.0 (Build 2026-09-22), FreeCAD Buddy 0.1.0+.*

## Stufen

| Stufe | Inhalt | Neue Parameter | Neue Feature-Typen | Soll-Volumen | Abmessungen |
|---|---|---|---|---|---|
| 1 | Grundplatte | Plate_Length, Plate_Width, Plate_Thickness | Pad | 100000.0 mm³ | 200 × 100 × 5 mm |
| 2 | Runder U-Griff mittig, Beinabstand 50 % der Länge | Handle_Diameter, Handle_Clearance, Handle_Bend_Radius | AdditivePipe (Sweep) | 112677.6 mm³ | 200 × 100 × 45 mm |
| 3 | Zweiter Body „Box“: Kasten unter dem Deckel mit 0,2 mm Spiel und vier viertelrunden Eck-Auflagen, Deckel bündig eingelegt | Box_Clearance, Box_Wall, Box_Floor, Support_Height, Support_Radius | Pocket | Platte 112677.6 mm³, Kasten 137035.6 mm³ | Kasten 206.4 × 106.4 × 28 mm, z = −23 … 5 |
| 4 | Stifte Ø 5 mm auf den Auflagen (bündig mit der Deckeloberseite), danach die passenden Bohrungen Ø 5,4 mm im Deckel | Pin_Diameter, Pin_Edge_Distance | Hole | Platte 112219.5 mm³, Kasten 137428.3 mm³ | unverändert |

Die Stufen wurden am 2026-09-28 neu geschnitten: Die Eckbohrungen der früheren Stufe 1 entfallen, an ihre Stelle treten in Stufe 4 die Stifte mit Passbohrungen. Ergebnisse vor diesem Datum sind nicht vergleichbar.

Für eine neue Stufe musst du an diesen Stellen ergänzen:
- In `referenzmodell.py`: `STAGE_PROMPTS`, `STAGE_PARAMETERS`, `STAGE_FEATURES`, die Soll-Formeln (`expected_volume`, `expected_size`, ab Stufe 3 `expected_box_*`), dazu `build` und `LATEST_STAGE`. Ändert sich Kopf oder Schluss des Prompts, kommt ein Eintrag in `PROMPT_HEADS` bzw. `PROMPT_TAILS` dazu; frühere Stufen behalten ihren Text.
- In diesem Dokument: die Zeile oben und den Prompt.

Danach den Screenshot neu erzeugen.

## Prompt der aktuellen Stufe (wörtlich verwenden)

Die Prompts früherer Stufen gibt `uv run python examples/samples/referenzmodell.py prompt --stage N` aus.

```text
Erstelle mit FreeCAD Buddy ein neues Dokument „Referenzmodell“ mit genau zwei Bodies, „Plate“ (Deckel) und „Box“ (Kasten):

1. Grundplatte 200 × 100 × 5 mm, mittig zum Ursprung auf der XY-Ebene, Länge in X.
2. Mittig ein Haltegriff als runde Stange Ø 10 mm mit gerundeten Ecken (Biegeradius 10 mm auf der Mittellinie). Beinabstand 50 % der Plattenlänge in X-Richtung, lichte Höhe 30 mm über der Plattenoberseite. Die Beine reichen durch die ganze Platte. Der Beinabstand ist ein Ausdruck von Plate_Length.
3. Unter dem Deckel ein Kasten „Box“, in den die Platte vertieft eingelegt wird: Innenmaß gleich Plattenmaß plus 0,2 mm Spiel je Seite, Wand 3 mm, Boden 3 mm. In den vier Innenecken je eine viertelrunde Auflage mit Radius 20 mm (Mittelpunkt in der Innenecke), 20 mm hoch über dem Kastenboden. Einbaulage: Die Plattenunterseite liegt bei z = 0 auf den Auflagen, die Plattenoberseite schließt bündig mit dem Kastenrand ab. Alle Kastenmaße sind Ausdrücke der Plattenmaße.
4. Auf jeder der vier Auflagen ein runder Stift Ø 5 mm nach oben, Mittelpunkt 10 mm von beiden Plattenrändern, Stiftoberkante bündig mit der Plattenoberseite. Danach in der Platte die passenden Durchgangsbohrungen: Stiftdurchmesser plus Box_Clearance Spiel je Seite, als Ausdruck.
5. Alle Maße als Parameter im VarSet „Parameters“ mit genau diesen Namen: Plate_Length, Plate_Width, Plate_Thickness, Handle_Diameter, Handle_Clearance, Handle_Bend_Radius, Box_Clearance, Box_Wall, Box_Floor, Support_Height, Support_Radius, Pin_Diameter, Pin_Edge_Distance.
6. Zum Schluss Druckbarkeit beider Bodies prüfen und Ansicht iso. Nicht speichern, nicht exportieren.
```

## Was geprüft wird

Die Aufgabe prüft, ob ein Modell den menschlichen PartDesign-Weg geht:
- Parameter zuerst anlegen.
- Vollständig bestimmte Skizzen auf Ursprungsebenen verwenden.
- Bohrungen als Hole-Feature bauen.
- Den runden Griff als Sweep bauen (Pfad plus Querschnitt).
- Maße über Ausdrücke koppeln.

`check --stage N` prüft kumulativ bis Stufe N. Volumen, Abmessungen und Parametrik gelten genau für Stufe N, ein Modell einer höheren Stufe erreicht bei `--stage 1` also keinen vollen Score:

| Prüfung | Stufe | Toleranz |
|---|---|---|
| genau ein Body (ab Stufe 3: genau die Bodies „Plate“ und „Box“), alle Features gültig, keine Label-Probleme | 1 (3) | exakt |
| alle Skizzen DoF 0 (über alle Bodies) | 1 | exakt |
| Parameter je Stufe vollständig und mit Soll-Wert | je Stufe | exakt |
| Feature-Typen je Stufe vorhanden | je Stufe | – |
| Volumen und Abmessungen der Platte | N | ± 1 mm³ / ± 0,01 mm |
| ab Stufe 3: Volumen, Abmessungen und Einbaulage (z-Bereich) des Kastens | N | ± 1 mm³ / ± 0,01 mm |
| Parametrik: `Plate_Length = 240`, das Volumen folgt (danach Undo), ab Stufe 3 auch beim Kasten | N | ± 1 mm³ |

Soll-Volumen nach der Parametrik-Probe:

| Stufe | Platte | Kasten |
|---|---|---|
| 1 | 120000.0 mm³ | – |
| 2 und 3 | 134248.4 mm³ | 155803.6 mm³ (Stufe 3) |
| 4 | 133790.3 mm³ | 156196.3 mm³ |

Herleitung:
- Platte als Quader.
- Ab Stufe 2 plus Griff nach Pappus: Kreisfläche mal Länge der Mittellinie, also `2·40 + 100 − 4·10 + π·10`.
- Davon ab die zwei Beinstücke, die in der Platte stecken.
- Kasten ab Stufe 3: Außenquader `206,4 · 106,4 · 28` minus Innenraum `200,4 · 100,4 · 25`, plus vier Viertelkreise, zusammen ein voller Kreis `π · 20² · 20`.
- Ab Stufe 4: Kasten plus vier Stifte `π · 2,5² · 5`, Platte minus vier Bohrungen `π · 2,7² · 5`.

## Ablauf eines Vergleichslaufs

1. FreeCAD neu starten, damit kein Dokument offen ist. `freecad-buddy` mit Log starten: `uv run freecad-buddy --log-file out/runs/<modell>-stufe<N>-<datum>.jsonl`.
2. Neue Claude-Code-Session (bzw. neuen Client) mit dem gewünschten Modell und der gewünschten Thinking-Stufe starten. Keine weiteren Hinweise geben.
3. Den Prompt der Stufe wörtlich einfügen und nicht eingreifen.
4. Bewerten mit `uv run python examples/samples/referenzmodell.py check --stage <N>`. Das Skript gibt JSON mit `score` aus, jede Prüfung trägt ihre Stufe. Bei vollem Score endet es mit Exit-Code 0.
5. Tool-Aufrufe zählen, also die Zeilen mit `"type": "request"` im JSONL-Log.
6. Ergebnis unten eintragen.

Referenzlösung: `… referenzmodell.py build --stage <N>`. Stufe 4 braucht 34 Tool-Aufrufe. Den Screenshot erneuerst du mit `… screenshot`, er zeigt immer die aktuelle Stufe.

## Ergebnisse

| Datum | Stufe | Modell / Thinking | Client | Score | Tool-Aufrufe | Fehler/Undo | Bemerkung |
|---|---|---|---|---|---|---|---|
| 2026-09-28 | 4 | Referenzskript | Skript (`build`) | 19/19 | 34 | 0 | Baseline |
| 2026-09-28 | 2 | Referenzskript | Skript (`build`) | 12/12 | 17 | 0 | Baseline, alter Stufenschnitt (mit Eckbohrungen), nicht mehr vergleichbar |

## Bekannte Grenzen

- `check_printability` meldet für den Griff keinen Überhang, obwohl der Querstab rund 80 mm frei spannt. Der Fehler liegt in der Prüfung, siehe Backlog-Ticket [`druckpruefung-ueberhang-kruemmung.md`](../../TODOs/1-backlog/freecad-buddy/druckpruefung-ueberhang-kruemmung.md). Die Druckprüfung fließt deshalb nicht in den Score ein.
- Der Screenshot hängt von Theme und Fenstergröße der GUI ab und dient nur der Sichtprüfung, nicht dem Score.
- Stufe 3: Zwei aufeinanderfolgende `pattern kind='mirrored'` auf dieselbe Auflage verlieren eine Kopie, weil der Body-Tip nicht weitergesetzt wird. Das Tool meldet trotzdem `ok`. Die Referenzlösung zeichnet deshalb alle vier Viertelkreise symmetrisch in einer Skizze. Modelle, die spiegeln, fallen bei Volumen und Parametrik des Kastens durch, bis der Fehler behoben ist.
