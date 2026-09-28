# Tool-Katalog — FreeCAD Buddy

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten.

39 Tools (`execute_python` nur mit `FREECAD_BUDDY_ALLOW_PYTHON=1` bzw. `--allow-python`).
Maße akzeptieren eine Zahl, einen Parameternamen oder einen Ausdruck über Parameter (`"Box_Width - 2*Wall"`).

| Tool | Zweck |
|---|---|
| [`get_status`](#get_status) | Status von FreeCAD und Bridge: Version, offene Dokumente, fehlende Objekttypen. Zuerst aufrufen. |
| [`new_document`](#new_document) | Neues FreeCAD-Dokument anlegen und aktivieren. Workflow danach: set_parameters → create_body → |
| [`open_document`](#open_document) | Vorhandenes Dokument öffnen und aktivieren. |
| [`save_document`](#save_document) | Dokument als .FCStd speichern (ohne path in die bisherige Datei; neue Dokumente brauchen path). |
| [`get_model_tree`](#get_model_tree) | Modellbaum lesen: Bodies mit Features in Reihenfolge, Gültigkeit, DoF der Skizzen, Undo-Liste und |
| [`get_object`](#get_object) | Details eines Objekts: Status, Expressions, bei Skizzen die Analyse, bei Körpern Volumen und Maße. |
| [`delete_object`](#delete_object) | Objekt löschen (ein Undo-Schritt). |
| [`undo`](#undo) | Letzte Änderung(en) rückgängig machen. Jeder Tool-Aufruf ist genau ein Schritt. |
| [`set_parameters`](#set_parameters) | Zentrale Parameter im VarSet 'Parameters' anlegen/ändern. Maße in Skizzen und Features können den |
| [`list_parameters`](#list_parameters) | Alle Parameter mit Typ, Wert und Expression-Referenz. |
| [`create_body`](#create_body) | PartDesign-Body für ein Bauteil anlegen (ein Body = ein druckbares Teil). |
| [`create_sketch`](#create_sketch) | Skizze auf stabiler Referenz anlegen. Bevorzugt Ursprungsebenen mit offset oder datum_plane. |
| [`add_profile`](#add_profile) | Vollständig bestimmtes Profil zeichnen wie ein Mensch: symmetrisch zum Ursprung, Equal statt |
| [`add_geometry`](#add_geometry) | Low-Level-Geometrie hinzufügen; Rückgabe sind Referenzen g<N> für add_constraints. |
| [`add_constraints`](#add_constraints) | Constraints hinzufügen. Widersprüchliche/redundante Constraints werden abgelehnt (Rollback). |
| [`analyze_sketch`](#analyze_sketch) | Skizzenanalyse: DoF, Konflikte, Redundanzen, geschlossene Linienzüge und Stil-Lint. |
| [`fully_constrain_sketch`](#fully_constrain_sketch) | Restliche Freiheitsgrade finden bzw. schließen (Koinzidenzen, H/V, dann benannte X/Y-Maße). Nie Block. |
| [`pad`](#pad) | Profil aufpolstern (additiv). |
| [`pocket`](#pocket) | Tasche schneiden (subtraktiv). |
| [`revolve`](#revolve) | Rotationskörper (Revolution) oder Rotationsnut (Groove). |
| [`sweep`](#sweep) | Querschnitt entlang eines Pfads ziehen (PartDesign AdditivePipe/SubtractivePipe): runde Griffe, |
| [`hole`](#hole) | Bohrungen (Hole-Feature) an allen Kreismittelpunkten der Skizze. |
| [`fillet`](#fillet) | Kanten verrunden. Der Selektor wird gespeichert und nach Parameteränderungen neu aufgelöst. |
| [`chamfer`](#chamfer) | Kanten fasen (an der Druckbett-Unterseite besser als Verrundung – gegen Elefantenfuß). |
| [`shell`](#shell) | Körper aushöhlen (Thickness) mit Wandstärke; gewählte Flächen werden zur Öffnung. |
| [`pattern`](#pattern) | Features spiegeln oder linear/polar/als Raster vervielfältigen (statt Geometrie mehrfach zu zeichnen). |
| [`datum_plane`](#datum_plane) | Bezugsebene als stabile Skizzenbasis (statt Skizze auf Körperfläche). |
| [`select_geometry`](#select_geometry) | Vorschau: welche Flächen/Kanten ein Selektor trifft (mit Mittelpunkt, Normale, Länge, Radius). |
| [`set_view`](#set_view) | Live-Ansicht in FreeCAD setzen (bleibt so stehen): Standard iso + alles einpassen. Als letzten |
| [`screenshot`](#screenshot) | Bild der 3D-Ansicht zur visuellen Kontrolle (nur mit laufender FreeCAD-GUI). |
| [`get_design_rules`](#get_design_rules) | Design-Regelwerk für FreeCAD-Konstruktion und FDM-Druck (Werte aus dem aktiven Druckerprofil). |
| [`search_addons`](#search_addons) | Offiziellen FreeCAD-Addon-Katalog durchsuchen (Workbenches, Makros, Preference Packs): Treffer mit |
| [`get_addon`](#get_addon) | Details eines Addons oder Makros: Lizenz, Maintainer, Repository, letzte Aktualisierung, |
| [`install_addon`](#install_addon) | Install an addon or macro through FreeCAD's Addon Manager (needs FreeCAD's opt-in). FreeCAD shows the user |
| [`get_printer_profile`](#get_printer_profile) | Aktives Druckerprofil (Bauraum, Düse, Mindestwand, Überhangwinkel, Passungsspiel). |
| [`set_printer_profile`](#set_printer_profile) | Druckerprofil ändern (dauerhaft gespeichert). |
| [`check_printability`](#check_printability) | Druckbarkeit prüfen: gültiger Solid, Bauraum, Überhänge, Wandstärke, zu kleine Details. |
| [`export_body`](#export_body) | Bauteil exportieren (auf das Druckbett gelegt) und die Datei per Reimport prüfen. |
| [`execute_python`](#execute_python) | Notausgang (nur mit FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD als ein Undo-Schritt. |

## get_status

Status von FreeCAD und Bridge: Version, offene Dokumente, fehlende Objekttypen. Zuerst aufrufen.

Keine Parameter.

Beispiel:

```json
{}
```

## new_document

Neues FreeCAD-Dokument anlegen und aktivieren. Workflow danach: set_parameters → create_body →
create_sketch → add_profile → pad/pocket → Details (fillet, hole, …) → check_printability → export_body.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `name` | string | ja | `—` | Name des neuen Dokuments |

Beispiel:

```json
{
  "name": "Box mit Deckel"
}
```

## open_document

Vorhandenes Dokument öffnen und aktivieren.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `path` | string | ja | `—` | Pfad zur .FCStd-Datei |

Beispiel:

```json
{
  "path": "C:/Projekte/box.FCStd"
}
```

## save_document

Dokument als .FCStd speichern (ohne path in die bisherige Datei; neue Dokumente brauchen path).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `path` | string \| null | nein | `null` | Zielpfad (.FCStd); leer = bisherige Datei |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "path": "C:/Projekte/box.FCStd"
}
```

## get_model_tree

Modellbaum lesen: Bodies mit Features in Reihenfolge, Gültigkeit, DoF der Skizzen, Undo-Liste und
Label-Probleme. Vor Änderungen aufrufen – der Nutzer kann parallel in FreeCAD arbeiten.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{}
```

## get_object

Details eines Objekts: Status, Expressions, bei Skizzen die Analyse, bei Körpern Volumen und Maße.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `ref` | string | ja | `—` | Objektname oder Label |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "ref": "Sketch_Base"
}
```

## delete_object

Objekt löschen (ein Undo-Schritt).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `ref` | string | ja | `—` | Objektname oder Label |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "ref": "Fillet_Top"
}
```

## undo

Letzte Änderung(en) rückgängig machen. Jeder Tool-Aufruf ist genau ein Schritt.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `steps` | integer | nein | `1` | Anzahl Schritte |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "steps": 1
}
```

## set_parameters

Zentrale Parameter im VarSet 'Parameters' anlegen/ändern. Maße in Skizzen und Features können den
Parameternamen statt einer Zahl nutzen – so bleibt das Modell in FreeCAD per Parameter änderbar.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `parameters` | object | ja | `—` | Name → Wert oder {value, type, description}; type: length (Standard), distance, angle, integer, float, bool. Namen englisch/ASCII, z. B. Box_Width. |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "parameters": {
    "Box_Width": 60,
    "Grip_Count": {
      "value": 12,
      "type": "integer"
    }
  }
}
```

## list_parameters

Alle Parameter mit Typ, Wert und Expression-Referenz.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{}
```

## create_body

PartDesign-Body für ein Bauteil anlegen (ein Body = ein druckbares Teil).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `label` | string | ja | `—` | Bauteilname, z. B. 'Box' oder 'Lid' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "label": "Box"
}
```

## create_sketch

Skizze auf stabiler Referenz anlegen. Bevorzugt Ursprungsebenen mit offset oder datum_plane.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `plane` | string | nein | `"XY"` | XY, XZ, YZ (Body-Ursprung), Label einer Datum-Ebene oder face:<selector> |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `offset` | number \| string | nein | `0` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `body` | string \| null | nein | `null` | Body-Label; leer bei nur einem Body |
| `reversed` | boolean | nein | `false` |  |
| `allow_face_attachment` | boolean | nein | `false` | Nur wenn nötig: Flächenbezug ist anfällig für Topologie-Änderungen |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "plane": "XY",
  "purpose": "Base",
  "offset": "Lid_Plate"
}
```

## add_profile

Vollständig bestimmtes Profil zeichnen wie ein Mensch: symmetrisch zum Ursprung, Equal statt
Doppelmaß, benannte Maße. Ergebnis enthält die Skizzenanalyse (DoF muss 0 sein).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label |
| `kind` | `rectangle` \| `rounded_rectangle` \| `slot` \| `circle` \| `polygon` \| `hole_rect` \| `polyline` \| `u_path` | ja | `—` | Profilart |
| `params` | object | ja | `—` | rectangle: width, height, [center=[x,y]], [anchor=center\|corner]; rounded_rectangle: width, height, radius, [center]; slot: length (Mittenabstand), width, [center]; circle: diameter, [center]; polygon: sides, diameter\|across_flats, [center]; hole_rect: width, height (Lochabstände), diameter, [center]; polyline: points=[[x,y],…]; u_path (offener Bügel-Pfad für sweep): length (Beinabstand), height, radius. Werte: Zahl oder Parametername. |
| `prefix` | string \| null | nein | `null` | Präfix für Maßnamen, z. B. 'Base' → Base_Width |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "sketch": "Sketch_Base",
  "kind": "rounded_rectangle",
  "params": {
    "width": "Box_Width",
    "height": "Box_Depth",
    "radius": 5
  }
}
```

## add_geometry

Low-Level-Geometrie hinzufügen; Rückgabe sind Referenzen g<N> für add_constraints.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label |
| `items` | array<object> | ja | `—` | Fallback, wenn kein Profil passt. {type: line, start, end} \| {type: circle, center, radius} \| {type: arc, center, radius, start_angle, end_angle} (Grad, gegen Uhrzeigersinn) \| {type: point, at}; optional construction: true |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "sketch": "Sketch_Base",
  "items": [
    {
      "type": "line",
      "start": [
        0,
        0
      ],
      "end": [
        20,
        0
      ]
    }
  ]
}
```

## add_constraints

Constraints hinzufügen. Widersprüchliche/redundante Constraints werden abgelehnt (Rollback).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label |
| `items` | array<object> | ja | `—` | {type, a, b?, about?, value?, name?}. Referenzen: g<N>, g<N>.start\|end\|center, origin, x_axis, y_axis. Typen: coincident, horizontal, vertical, parallel, perpendicular, equal, tangent, point_on_object, symmetric, distance, distance_x, distance_y, radius, diameter, angle (Grad). value: Zahl oder Parametername; Maße immer benennen. |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "sketch": "Sketch_Base",
  "items": [
    {
      "type": "coincident",
      "a": "g0.start",
      "b": "origin"
    },
    {
      "type": "distance",
      "a": "g0",
      "value": "Arm_Length",
      "name": "Arm_Length"
    }
  ]
}
```

## analyze_sketch

Skizzenanalyse: DoF, Konflikte, Redundanzen, geschlossene Linienzüge und Stil-Lint.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "sketch": "Sketch_Base"
}
```

## fully_constrain_sketch

Restliche Freiheitsgrade finden bzw. schließen (Koinzidenzen, H/V, dann benannte X/Y-Maße). Nie Block.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label |
| `apply` | boolean | nein | `false` | false = nur Vorschläge, true = anwenden |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "sketch": "Sketch_Base",
  "apply": false
}
```

## pad

Profil aufpolstern (additiv).

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

Tasche schneiden (subtraktiv).

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

Rotationskörper (Revolution) oder Rotationsnut (Groove).

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

Querschnitt entlang eines Pfads ziehen (PartDesign AdditivePipe/SubtractivePipe): runde Griffe,
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

Bohrungen (Hole-Feature) an allen Kreismittelpunkten der Skizze.

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

Kanten verrunden. Der Selektor wird gespeichert und nach Parameteränderungen neu aufgelöst.

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

Kanten fasen (an der Druckbett-Unterseite besser als Verrundung – gegen Elefantenfuß).

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

Körper aushöhlen (Thickness) mit Wandstärke; gewählte Flächen werden zur Öffnung.

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

Features spiegeln oder linear/polar/als Raster vervielfältigen (statt Geometrie mehrfach zu zeichnen).

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

## datum_plane

Bezugsebene als stabile Skizzenbasis (statt Skizze auf Körperfläche).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `base` | string | nein | `"XY"` | XY, XZ oder YZ |
| `offset` | number \| string | nein | `0` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `angle` | number \| string | nein | `0` | Zahl in mm/Grad oder Name eines Parameters (wird per Expression gebunden) |
| `rotation_axis` | string | nein | `"X"` | X, Y oder Z |
| `body` | string \| null | nein | `null` | Body-Label |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "base": "XY",
  "offset": "Box_Height",
  "purpose": "Top"
}
```

## select_geometry

Vorschau: welche Flächen/Kanten ein Selektor trifft (mit Mittelpunkt, Normale, Länge, Radius).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `selector` | string | ja | `—` | Semantischer Selektor, z. B. edges:top, edges:vertical, edges:bottom, faces:top, face:top, edges:circular,radius=2, edges:of_feature=Pocket_Cut. select_geometry zeigt die Treffer vorab. |
| `target` | string \| null | nein | `null` | Feature-Label; leer = Tip des Bodys |
| `body` | string \| null | nein | `null` | Body-Label |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "selector": "edges:parallel=X,y=Thickness,z=Thickness"
}
```

## set_view

Live-Ansicht in FreeCAD setzen (bleibt so stehen): Standard iso + alles einpassen. Als letzten
Schritt aufrufen; nach dem ersten Basis-Feature setzt der Server sie selbst (nur mit FreeCAD-GUI).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `view` | `iso` \| `dimetric` \| `trimetric` \| `front` \| `back` \| `top` \| `bottom` \| `left` \| `right` \| `current` | nein | `"iso"` |  |
| `fit` | boolean | nein | `true` | Alles einpassen, damit das Bauteil komplett sichtbar ist |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "view": "iso",
  "fit": true
}
```

## screenshot

Bild der 3D-Ansicht zur visuellen Kontrolle (nur mit laufender FreeCAD-GUI).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `view` | `iso` \| `dimetric` \| `trimetric` \| `front` \| `back` \| `top` \| `bottom` \| `left` \| `right` \| `current` | nein | `"iso"` |  |
| `width` | integer | nein | `800` |  |
| `height` | integer | nein | `600` |  |
| `fit` | boolean | nein | `true` |  |
| `isolate` | string \| null | nein | `null` | Nur dieses Objekt zeigen |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "view": "iso",
  "width": 800,
  "height": 600
}
```

## get_design_rules

Design-Regelwerk für FreeCAD-Konstruktion und FDM-Druck (Werte aus dem aktiven Druckerprofil).
Vor einer neuen Konstruktion die passenden Themen lesen, z. B. sketches und printing.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `topic` | string \| null | nein | `null` | Thema: workflow, parameters, sketches, references, features, naming, printing, design_tools, addons; leer = Themenübersicht |

Beispiel:

```json
{
  "topic": "printing"
}
```

## search_addons

Offiziellen FreeCAD-Addon-Katalog durchsuchen (Workbenches, Makros, Preference Packs): Treffer mit
Kompatibilität zum laufenden FreeCAD und Installationsstatus. Vor einem eigenen Design-Tool prüfen.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `query` | string | ja | `—` | Suchbegriffe, alle müssen passen, z. B. 'grid' oder 'honeycomb' |
| `kind` | `any` \| `workbench` \| `macro` \| `preference_pack` | nein | `"any"` |  |
| `limit` | integer | nein | `10` |  |
| `refresh` | boolean | nein | `false` | Katalog sofort neu laden (sonst höchstens täglich) |

Beispiel:

```json
{
  "query": "grid",
  "kind": "any"
}
```

## get_addon

Details eines Addons oder Makros: Lizenz, Maintainer, Repository, letzte Aktualisierung,
Abhängigkeiten (FreeCAD, Addons, Python), Kompatibilität, Installationsstatus und README-Auszug.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `addon_id` | string | ja | `—` | Id oder Name aus search_addons, z. B. 'lattice2' |
| `readme` | boolean | nein | `true` | README-Auszug aus dem Repository laden |

Beispiel:

```json
{
  "addon_id": "lattice2"
}
```

## install_addon

Install an addon or macro through FreeCAD's Addon Manager (needs FreeCAD's opt-in). FreeCAD shows the user
a confirmation dialog - ask in the chat first. Workbenches need a FreeCAD restart afterwards.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `addon_id` | string | ja | `—` | Id from search_addons/get_addon |
| `wait_seconds` | integer | nein | `300` | How long to wait for completion |

Beispiel:

```json
{
  "addon_id": "lattice2"
}
```

## get_printer_profile

Aktives Druckerprofil (Bauraum, Düse, Mindestwand, Überhangwinkel, Passungsspiel).

Keine Parameter.

Beispiel:

```json
{}
```

## set_printer_profile

Druckerprofil ändern (dauerhaft gespeichert).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `updates` | object | ja | `—` | Zu ändernde Profilwerte, z. B. {nozzle: 0.6} |

Beispiel:

```json
{
  "updates": {
    "nozzle": 0.6,
    "min_wall": 1.2
  }
}
```

## check_printability

Druckbarkeit prüfen: gültiger Solid, Bauraum, Überhänge, Wandstärke, zu kleine Details.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `target` | string \| null | nein | `null` | Body/Objekt; leer = einziger Body |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "target": "Box"
}
```

## export_body

Bauteil exportieren (auf das Druckbett gelegt) und die Datei per Reimport prüfen.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `format` | `stl` \| `3mf` \| `step` | nein | `"3mf"` |  |
| `target` | string \| null | nein | `null` | Body/Objekt; leer = einziger Body |
| `path` | string \| null | nein | `null` | Datei oder Ordner; leer = <Dokumentordner>/export |
| `place_on_bed` | boolean | nein | `true` |  |
| `overwrite` | boolean | nein | `false` | Vorhandene Datei überschreiben |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "format": "3mf",
  "target": "Box"
}
```

## execute_python

Notausgang (nur mit FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD als ein Undo-Schritt.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `code` | string | ja | `—` | Python-Code; Variable 'result' wird zurückgegeben |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "code": "result = len(doc.Objects)"
}
```
