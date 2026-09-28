# Sample: Referenzmodell

Mitwachsende Referenzaufgabe, mit der sich LLMs und Thinking-Stufen an FreeCAD Buddy vergleichen lassen. Das Modell wird in **Stufen** ausgebaut. Jede Stufe bringt neue Features, Parameter und Prüfungen mit, frühere Stufen bleiben unverändert. Ergebnisse derselben Stufe sind deshalb immer vergleichbar.

Die Aufgabe ist deterministisch:
- Der Prompt legt alle Maße und Parameternamen fest.
- Die Prüfung ([`referenzmodell.py`](referenzmodell.py) `check`) bewertet ausschließlich Tool-Ergebnisse.
- Einzige Quelle für Prompt, Soll-Werte und Referenzlösung ist das Skript. Dieses Dokument zeigt sie nur an, ein Test hält beides gleich.

![Referenzmodell Stufe 2, isometrisch](referenzmodell.png)

*Aktueller Stand: Stufe 2, 2026-09-28, FreeCAD 26.3.0 (Build 2026-09-22), FreeCAD Buddy 0.1.0+.*

## Stufen

| Stufe | Inhalt | Neue Parameter | Neue Feature-Typen | Soll-Volumen | Abmessungen |
|---|---|---|---|---|---|
| 1 | Grundplatte mit vier Eckbohrungen | Plate_Length, Plate_Width, Plate_Thickness, Hole_Diameter, Hole_Edge_Distance | Pad, Hole | 98994.7 mm³ | 200 × 100 × 5 mm |
| 2 | Runder U-Griff mittig, Beinabstand 50 % der Länge | Handle_Diameter, Handle_Clearance, Handle_Bend_Radius | AdditivePipe (Sweep) | 111672.3 mm³ | 200 × 100 × 45 mm |

Für eine neue Stufe musst du an diesen Stellen ergänzen:
- In `referenzmodell.py`: `STAGE_PROMPTS`, `STAGE_PARAMETERS`, `STAGE_FEATURES`, die Formel in `expected_volume` bzw. `expected_size`, dazu `build` und `LATEST_STAGE`.
- In diesem Dokument: die Zeile oben und den Prompt.

Danach den Screenshot neu erzeugen.

## Prompt der aktuellen Stufe (wörtlich verwenden)

Die Prompts früherer Stufen gibt `uv run python examples/samples/referenzmodell.py prompt --stage N` aus.

```text
Erstelle mit FreeCAD Buddy ein neues Dokument „Referenzmodell“ mit genau einem Body „Plate“:

1. Grundplatte 200 × 100 × 5 mm, mittig zum Ursprung auf der XY-Ebene, Länge in X.
2. In den vier Ecken je eine Durchgangsbohrung Ø 8 mm, Mittelpunkt 10 mm von beiden Rändern.
3. Mittig ein Haltegriff als runde Stange Ø 10 mm mit gerundeten Ecken (Biegeradius 10 mm auf der Mittellinie). Beinabstand 50 % der Plattenlänge in X-Richtung, lichte Höhe 30 mm über der Plattenoberseite. Die Beine reichen durch die ganze Platte. Der Beinabstand ist ein Ausdruck von Plate_Length.
4. Alle Maße als Parameter im VarSet „Parameters“ mit genau diesen Namen: Plate_Length, Plate_Width, Plate_Thickness, Hole_Diameter, Hole_Edge_Distance, Handle_Diameter, Handle_Clearance, Handle_Bend_Radius.
5. Zum Schluss Druckbarkeit prüfen und Ansicht iso. Nicht speichern, nicht exportieren.
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
| genau ein Body, alle Features gültig, keine Label-Probleme | 1 | exakt |
| alle Skizzen DoF 0 | 1 | exakt |
| Parameter je Stufe vollständig und mit Soll-Wert | je Stufe | exakt |
| Feature-Typen je Stufe vorhanden | je Stufe | – |
| Volumen und Abmessungen der Stufe | N | ± 1 mm³ / ± 0,01 mm |
| Parametrik: `Plate_Length = 240`, das Volumen folgt (danach Undo) | N | ± 1 mm³ |

Soll-Volumen nach der Parametrik-Probe: Stufe 1 118994.7 mm³, Stufe 2 133243.1 mm³.

Herleitung:
- Platte minus vier Bohrungen.
- Ab Stufe 2 plus Griff nach Pappus: Kreisfläche mal Länge der Mittellinie, also `2·40 + 100 − 4·10 + π·10`.
- Davon ab die zwei Beinstücke, die in der Platte stecken.

## Ablauf eines Vergleichslaufs

1. FreeCAD neu starten, damit kein Dokument offen ist. `freecad-buddy` mit Log starten: `uv run freecad-buddy --log-file out/runs/<modell>-stufe<N>-<datum>.jsonl`.
2. Neue Claude-Code-Session (bzw. neuen Client) mit dem gewünschten Modell und der gewünschten Thinking-Stufe starten. Keine weiteren Hinweise geben.
3. Den Prompt der Stufe wörtlich einfügen und nicht eingreifen.
4. Bewerten mit `uv run python examples/samples/referenzmodell.py check --stage <N>`. Das Skript gibt JSON mit `score` aus, jede Prüfung trägt ihre Stufe. Bei vollem Score endet es mit Exit-Code 0.
5. Tool-Aufrufe zählen, also die Zeilen mit `"type": "request"` im JSONL-Log.
6. Ergebnis unten eintragen.

Referenzlösung: `… referenzmodell.py build --stage <N>`. Stufe 2 braucht 17 Tool-Aufrufe. Den Screenshot erneuerst du mit `… screenshot`, er zeigt immer die aktuelle Stufe.

## Ergebnisse

| Datum | Stufe | Modell / Thinking | Client | Score | Tool-Aufrufe | Fehler/Undo | Bemerkung |
|---|---|---|---|---|---|---|---|
| 2026-09-28 | 2 | Referenzskript | Skript (`build`) | 12/12 | 17 | 0 | Baseline |

## Bekannte Grenzen

- `check_printability` meldet für den Griff keinen Überhang, obwohl der Querstab rund 80 mm frei spannt. Der Fehler liegt in der Prüfung, siehe Backlog-Ticket [`druckpruefung-ueberhang-kruemmung.md`](../../TODOs/1-backlog/freecad-buddy/druckpruefung-ueberhang-kruemmung.md). Die Druckprüfung fließt deshalb nicht in den Score ein.
- Der Screenshot hängt von Theme und Fenstergröße der GUI ab und dient nur der Sichtprüfung, nicht dem Score.
