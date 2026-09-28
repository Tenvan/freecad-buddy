# Features — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Feature]` · 10 Tools

| Tool | Zweck |
|---|---|
| [`pad`](#pad) | Profil aufpolstern (additiv). |
| [`pocket`](#pocket) | Tasche schneiden (subtraktiv). |
| [`revolve`](#revolve) | Rotationskörper (Revolution) oder Rotationsnut (Groove). |
| [`sweep`](#sweep) | Querschnitt entlang eines Pfads ziehen (PartDesign AdditivePipe/SubtractivePipe): runde Griffe, |
| [`hole`](#hole) | Holes (Hole feature) at every circle centre of the sketch. Cuts without cut_* use ISO defaults; |
| [`fillet`](#fillet) | Kanten verrunden. Der Selektor wird gespeichert und nach Parameteränderungen neu aufgelöst. |
| [`chamfer`](#chamfer) | Kanten fasen (an der Druckbett-Unterseite besser als Verrundung – gegen Elefantenfuß). |
| [`shell`](#shell) | Körper aushöhlen (Thickness) mit Wandstärke; gewählte Flächen werden zur Öffnung. |
| [`pattern`](#pattern) | Features spiegeln oder linear/polar/als Raster vervielfältigen (statt Geometrie mehrfach zu zeichnen). |
| [`thread`](#thread) | Cut a real external metric thread (ISO 60° profile, native SubtractiveHelix) into an existing |

## pad

[Feature] Profil aufpolstern (additiv).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label mit geschlossenem Profil |
| `length` | number \| string | nein | `10` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `mode` | `length` \| `symmetric` \| `two_sides` \| `up_to_last` | nein | `"length"` |  |
| `length2` | number \| string \| null | nein | `null` |  |
| `reversed` | boolean | nein | `false` |  |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "sketch": "Sketch_Base",
  "length": "Box_Height",
  "purpose": "Base"
}
```

## pocket

[Feature] Tasche schneiden (subtraktiv).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label mit geschlossenem Profil |
| `depth` | number \| string | nein | `5` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `mode` | `length` \| `symmetric` \| `through_all` | nein | `"length"` |  |
| `reversed` | boolean | nein | `false` | Richtung; wird automatisch umgekehrt, falls nichts geschnitten |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "sketch": "Sketch_Cutout",
  "mode": "through_all",
  "purpose": "Cutout"
}
```

## revolve

[Feature] Rotationskörper (Revolution) oder Rotationsnut (Groove).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label |
| `axis` | string | nein | `"V_Axis"` | V_Axis/H_Axis (Skizzenachse) oder X/Y/Z (Body-Achse) |
| `angle` | number \| string | nein | `360` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `subtractive` | boolean | nein | `false` | true = Nut (Groove) |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "sketch": "Sketch_Profile",
  "axis": "V_Axis",
  "angle": 360
}
```

## sweep

[Feature] Querschnitt entlang eines Pfads ziehen (PartDesign AdditivePipe/SubtractivePipe): runde Griffe,
Bügel, Kabelkanäle. Querschnitt senkrecht zum Pfadanfang legen (Pfad startet vertikal → Kreis auf XY).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `profile` | string | ja | `—` | Skizze mit geschlossenem Querschnitt am Pfadanfang, z. B. Kreis |
| `path` | string | ja | `—` | Pfad-Skizze, z. B. add_profile kind='u_path' |
| `subtractive` | boolean | nein | `false` | true = Material entlang des Pfads entfernen |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "profile": "Sketch_HandleSection",
  "path": "Sketch_HandlePath",
  "purpose": "Handle"
}
```

## hole

[Feature] Holes (Hole feature) at every circle centre of the sketch. Cuts without cut_* use ISO defaults;
cut_diameter/cut_depth/countersink_angle set custom, parametric values.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizze mit Kreisen an den Bohrungspositionen (z. B. hole_rect) |
| `size` | string | nein | `"M3"` | ISO-Metrisch, z. B. M3, M4 |
| `cut` | `none` \| `countersink` \| `counterbore` | nein | `"none"` |  |
| `depth` | number \| string \| null | nein | `null` | leer = durch alles |
| `threaded` | boolean | nein | `false` |  |
| `diameter` | number \| string \| null | nein | `null` | Durchmesser-Override, z. B. 3.4 für M3-Spiel |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |
| `cut_diameter` | number \| string \| null | nein | `null` | Custom counterbore/countersink diameter (number, parameter or expression) |
| `cut_depth` | number \| string \| null | nein | `null` | Custom counterbore depth (counterbore only) |
| `countersink_angle` | number \| string \| null | nein | `null` | Custom countersink angle in degrees (countersink only) |

Beispiel:

```json
{
  "sketch": "Sketch_ScrewHoles",
  "size": "M4",
  "cut": "countersink",
  "diameter": 4.4
}
```

## fillet

[Feature] Kanten verrunden. Der Selektor wird gespeichert und nach Parameteränderungen neu aufgelöst.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `selector` | string | nein | `"edges:top"` | Semantischer Selektor, z. B. edges:top, edges:vertical, edges:bottom, faces:top, face:top, edges:circular,radius=2, edges:of_feature=Pocket_Cut. select_geometry zeigt die Treffer vorab. |
| `radius` | number \| string | nein | `1` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `body` | string \| null | nein | `null` | Body-Label |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "selector": "edges:vertical",
  "radius": "Corner_Radius"
}
```

## chamfer

[Feature] Kanten fasen (an der Druckbett-Unterseite besser als Verrundung – gegen Elefantenfuß).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `selector` | string | nein | `"edges:bottom"` | Semantischer Selektor, z. B. edges:top, edges:vertical, edges:bottom, faces:top, face:top, edges:circular,radius=2, edges:of_feature=Pocket_Cut. select_geometry zeigt die Treffer vorab. |
| `size` | number \| string | nein | `0.5` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `body` | string \| null | nein | `null` | Body-Label |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "selector": "edges:bottom",
  "size": 0.4
}
```

## shell

[Feature] Körper aushöhlen (Thickness) mit Wandstärke; gewählte Flächen werden zur Öffnung.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `selector` | string | nein | `"face:top"` | Öffnungsfläche(n), z. B. face:top |
| `thickness` | number \| string | nein | `2` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `outward` | boolean | nein | `false` |  |
| `body` | string \| null | nein | `null` | Body-Label |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "selector": "face:top",
  "thickness": "Wall"
}
```

## pattern

[Feature] Features spiegeln oder linear/polar/als Raster vervielfältigen (statt Geometrie mehrfach zu zeichnen).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `features` | array<string> | ja | `—` | Labels der zu vervielfältigenden Features |
| `kind` | `mirrored` \| `linear` \| `polar` \| `grid` | ja | `—` | grid = 2D-Raster (MultiTransform); Muster auf Muster ist in PartDesign nicht möglich |
| `plane` | string | nein | `"YZ"` | mirrored: XY/XZ/YZ |
| `direction` | string | nein | `"X"` | linear/grid: X/Y/Z |
| `axis` | string | nein | `"Z"` | polar: X/Y/Z |
| `length` | number \| string | nein | `20` | linear/grid: Gesamtlänge (mm, Parameter, Ausdruck) |
| `angle` | number \| string | nein | `360` | polar: Gesamtwinkel |
| `count` | integer \| string | nein | `2` | Anzahl (linear/polar/grid), Zahl oder Integer-Parameter |
| `direction2` | string | nein | `"Y"` | grid: zweite Richtung X/Y/Z |
| `length2` | number \| string | nein | `20` | grid: Gesamtlänge der zweiten Richtung |
| `count2` | integer \| string | nein | `2` | grid: Anzahl in der zweiten Richtung |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "features": [
    "Pocket_SieveHole"
  ],
  "kind": "grid",
  "length": "(Sieve_Count_X - 1) * Sieve_Pitch",
  "count": "Sieve_Count_X",
  "length2": "(Sieve_Count_Y - 1) * Sieve_Pitch",
  "count2": "Sieve_Count_Y"
}
```

## thread

[Feature] Cut a real external metric thread (ISO 60° profile, native SubtractiveHelix) into an existing
vertical cylinder of the body. Fully constrained and parametric; repeat it with pattern.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `center` | array<number \| string> | ja | `—` | [x, y] of the vertical cylinder axis (numbers or parameters) |
| `diameter` | number \| string | ja | `—` | Major diameter, e.g. 10 for M10 or 'Pin_Diameter' |
| `pitch` | number \| string | ja | `—` | Thread pitch, ISO coarse: M3 0.5, M5 0.8, M10 1.5 |
| `length` | number \| string | ja | `—` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `z_start` | number \| string | nein | `0` | Height where the thread starts |
| `left_handed` | boolean | nein | `false` |  |
| `body` | string \| null | nein | `null` | Body label; empty when there is only one body |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "center": [
    85,
    35
  ],
  "diameter": "Pin_Diameter",
  "pitch": 1.5,
  "length": 15,
  "z_start": 5
}
```
