# Features — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Feature]` · 14 Tools

| Tool | Zweck |
|---|---|
| [`pad`](#pad) | Extrude a profile (additive). up_to_first stops at the next face of the solid. |
| [`pocket`](#pocket) | Cut a pocket (subtractive). up_to_first stops at the next face of the solid. |
| [`revolve`](#revolve) | Solid of revolution (Revolution) or rotational groove (Groove). |
| [`sweep`](#sweep) | Sweep a cross-section along a path (PartDesign AdditivePipe/SubtractivePipe): round handles, |
| [`loft`](#loft) | Loft through two or more sketches (PartDesign AdditiveLoft/SubtractiveLoft): funnels, |
| [`helix`](#helix) | Sweep a profile along a helix (PartDesign AdditiveHelix/SubtractiveHelix): springs, cable |
| [`primitive`](#primitive) | Additive or subtractive primitive (PartDesign Additive*/Subtractive*) placed on an origin or |
| [`hole`](#hole) | Holes (Hole feature) at every circle centre of the sketch. Cuts without cut_* use ISO defaults; |
| [`fillet`](#fillet) | Round edges. The selector is stored and resolved again after parameter changes. |
| [`chamfer`](#chamfer) | Chamfer edges (on the bed side better than a fillet - against elephant foot). |
| [`shell`](#shell) | Hollow the solid (Thickness) with a wall thickness; the selected faces become the openings. |
| [`pattern`](#pattern) | Mirror features or repeat them linearly/polar/as a raster (instead of drawing geometry several times). |
| [`thread`](#thread) | Cut a real external metric thread (ISO 60° profile, native SubtractiveHelix) into an existing |
| [`add_gear`](#add_gear) | Parametric gear from the freecad.gears workbench (needs the addon) as feature of a body; one gear per |

## pad

[Feature] Extrude a profile (additive). up_to_first stops at the next face of the solid.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Sketch label with a closed profile |
| `length` | number \| string | nein | `10` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `mode` | `length` \| `symmetric` \| `two_sides` \| `up_to_last` \| `up_to_first` | nein | `"length"` |  |
| `length2` | number \| string \| null | nein | `null` |  |
| `reversed` | boolean | nein | `false` |  |
| `taper` | number \| string | nein | `0` | Taper angle of the side walls in degrees (0 = straight, positive = wider at the end) |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "sketch": "Sketch_Base",
  "length": "Box_Height",
  "purpose": "Base"
}
```

## pocket

[Feature] Cut a pocket (subtractive). up_to_first stops at the next face of the solid.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Sketch label with a closed profile |
| `depth` | number \| string | nein | `5` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `mode` | `length` \| `symmetric` \| `through_all` \| `up_to_first` | nein | `"length"` |  |
| `reversed` | boolean | nein | `false` | Direction; reversed automatically if nothing is cut |
| `taper` | number \| string | nein | `0` | Taper angle of the side walls in degrees (0 = straight) |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "sketch": "Sketch_Cutout",
  "mode": "through_all",
  "purpose": "Cutout"
}
```

## revolve

[Feature] Solid of revolution (Revolution) or rotational groove (Groove).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label |
| `axis` | string | nein | `"V_Axis"` | V_Axis/H_Axis (sketch axis), X/Y/Z (body axis) or a datum line label |
| `angle` | number \| string | nein | `360` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `subtractive` | boolean | nein | `false` | true = Nut (Groove) |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "sketch": "Sketch_Profile",
  "axis": "V_Axis",
  "angle": 360
}
```

## sweep

[Feature] Sweep a cross-section along a path (PartDesign AdditivePipe/SubtractivePipe): round handles,
brackets, cable ducts. Place the cross-section perpendicular to the path start
(path starts vertically → circle on XY).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `profile` | string | ja | `—` | Sketch with a closed cross-section at the path start, e.g. a circle |
| `path` | string | ja | `—` | Path sketch, e.g. add_profile kind='u_path' |
| `subtractive` | boolean | nein | `false` | true = remove material along the path |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "profile": "Sketch_HandleSection",
  "path": "Sketch_HandlePath",
  "purpose": "Handle"
}
```

## loft

[Feature] Loft through two or more sketches (PartDesign AdditiveLoft/SubtractiveLoft): funnels,
adapters, transitions between cross-sections. Put every section on its own plane
(origin plane or datum_plane with an offset parameter).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketches` | array<string> | ja | `—` | Two or more sketches in transition order, each on its own plane (e.g. circle on XY, smaller circle on a datum_plane at Funnel_Height) |
| `subtractive` | boolean | nein | `false` | true = remove material through the sections |
| `ruled` | boolean | nein | `false` | Straight surfaces between sections instead of smooth |
| `closed` | boolean | nein | `false` | Close the loft back to the first sketch |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "sketches": [
    "Sketch_FunnelBottom",
    "Sketch_FunnelTop"
  ],
  "purpose": "Funnel"
}
```

## helix

[Feature] Sweep a profile along a helix (PartDesign AdditiveHelix/SubtractiveHelix): springs, cable
guides, custom grooves and threads. For ISO external threads on a cylinder use thread.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Profile sketch beside the axis, in a plane that contains the axis (e.g. a circle at x = Spring_Radius on XZ for a spring around Z) |
| `pitch` | number \| string | ja | `—` | Axial distance per turn |
| `height` | number \| string \| null | nein | `null` | Length along the axis (or give turns) |
| `turns` | number \| string \| null | nein | `null` | Number of turns (or give height) |
| `axis` | string | nein | `"V_Axis"` | V_Axis/H_Axis (sketch axis), X/Y/Z (body axis) or a datum line label |
| `angle` | number \| string | nein | `0` | Taper angle in degrees, 0 = cylindrical |
| `left_handed` | boolean | nein | `false` |  |
| `subtractive` | boolean | nein | `false` | true = cut a helical groove |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "sketch": "Sketch_SpringWire",
  "pitch": "Spring_Pitch",
  "height": "Spring_Height",
  "purpose": "Spring"
}
```

## primitive

[Feature] Additive or subtractive primitive (PartDesign Additive*/Subtractive*) placed on an origin or
datum plane with parametric sizes. Use it for spheres, tori, ellipsoids, wedges and quick helper
volumes; boxes, cylinders and prisms are usually better as a sketch plus pad (editable profile).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `kind` | `box` \| `cylinder` \| `sphere` \| `cone` \| `ellipsoid` \| `torus` \| `prism` \| `wedge` | ja | `—` |  |
| `dims` | object | ja | `—` | box: length, width, height; cylinder: diameter, height; sphere: diameter; cone: diameter, top_diameter, height; ellipsoid: length, width, height; torus: diameter (centre line), tube_diameter; prism: sides, diameter (circumscribed), height; wedge: length, width, height, top_length, top_width. Numbers or parameter names |
| `plane` | string | nein | `"XY"` | XY, XZ, YZ or a datum plane label |
| `center` | array<number \| string> \| null | nein | `null` | [x, y] of the reference point on the plane (default [0, 0]): footprint centre of box/wedge, base centre of cylinder/cone/prism, centre of sphere/ellipsoid/torus |
| `offset` | number \| string | nein | `0` | Distance of the reference point along the plane normal |
| `subtractive` | boolean | nein | `false` | true = remove the primitive's volume |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `body` | string \| null | nein | `null` | Body label; empty = the active/only body |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "kind": "sphere",
  "dims": {
    "diameter": "Knob_Diameter"
  },
  "offset": "Knob_Height",
  "purpose": "Knob"
}
```

## hole

[Feature] Holes (Hole feature) at every circle centre of the sketch. Cuts without cut_* use ISO defaults;
cut_diameter/cut_depth/countersink_angle set custom, parametric values.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Sketch with circles at the hole positions (e.g. hole_rect) |
| `size` | string | nein | `"M3"` | ISO-Metrisch, z. B. M3, M4 |
| `cut` | `none` \| `countersink` \| `counterbore` | nein | `"none"` |  |
| `depth` | number \| string \| null | nein | `null` | empty = through all |
| `threaded` | boolean | nein | `false` |  |
| `diameter` | number \| string \| null | nein | `null` | Diameter override, e.g. 3.4 for M3 clearance |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |
| `cut_diameter` | number \| string \| null | nein | `null` | Custom counterbore/countersink diameter (number, parameter or expression) |
| `cut_depth` | number \| string \| null | nein | `null` | Custom counterbore depth (counterbore only) |
| `countersink_angle` | number \| string \| null | nein | `null` | Custom countersink angle in degrees (countersink only) |
| `model_thread` | boolean | nein | `false` | Cut the real thread geometry of a threaded hole (about 1.5 s and 60-90 faces per hole - single tapped holes only, never for rasters) |

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

[Feature] Round edges. The selector is stored and resolved again after parameter changes.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `selector` | string | nein | `"edges:top"` | Semantic selector, e.g. edges:top, edges:vertical, edges:bottom, faces:top, face:top, edges:circular,radius=2, edges:of_feature=Pocket_Cut. select_geometry previews the hits. |
| `radius` | number \| string | nein | `1` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `body` | string \| null | nein | `null` | Body-Label |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "selector": "edges:vertical",
  "radius": "Corner_Radius"
}
```

## chamfer

[Feature] Chamfer edges (on the bed side better than a fillet - against elephant foot).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `selector` | string | nein | `"edges:bottom"` | Semantic selector, e.g. edges:top, edges:vertical, edges:bottom, faces:top, face:top, edges:circular,radius=2, edges:of_feature=Pocket_Cut. select_geometry previews the hits. |
| `size` | number \| string | nein | `0.5` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `body` | string \| null | nein | `null` | Body-Label |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "selector": "edges:bottom",
  "size": 0.4
}
```

## shell

[Feature] Hollow the solid (Thickness) with a wall thickness; the selected faces become the openings.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `selector` | string | nein | `"face:top"` | Opening face(s), e.g. face:top |
| `thickness` | number \| string | nein | `2` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `outward` | boolean | nein | `false` |  |
| `body` | string \| null | nein | `null` | Body-Label |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "selector": "face:top",
  "thickness": "Wall"
}
```

## pattern

[Feature] Mirror features or repeat them linearly/polar/as a raster (instead of drawing geometry several times).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `features` | array<string> | ja | `—` | Labels of the features to repeat |
| `kind` | `mirrored` \| `linear` \| `polar` \| `grid` | ja | `—` | grid = 2D raster (MultiTransform); PartDesign cannot pattern a pattern |
| `plane` | string | nein | `"YZ"` | mirrored: XY/XZ/YZ |
| `direction` | string | nein | `"X"` | linear/grid: X/Y/Z |
| `axis` | string | nein | `"Z"` | polar: X/Y/Z or a datum line label |
| `length` | number \| string | nein | `20` | linear/grid: total length (mm, parameter, expression) |
| `angle` | number \| string | nein | `360` | polar: total angle in degrees |
| `count` | integer \| string | nein | `2` | Count (linear/polar/grid), number or integer parameter |
| `direction2` | string | nein | `"Y"` | grid: second direction X/Y/Z |
| `length2` | number \| string | nein | `20` | grid: total length of the second direction |
| `count2` | integer \| string | nein | `2` | grid: count in the second direction |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

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
| `length` | number \| string | ja | `—` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `z_start` | number \| string | nein | `0` | Height where the thread starts |
| `left_handed` | boolean | nein | `false` |  |
| `body` | string \| null | nein | `null` | Body label; empty when there is only one body |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

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

## add_gear

[Feature] Parametric gear from the freecad.gears workbench (needs the addon) as feature of a body; one gear per
body. Values accept parameter names/expressions. Returns pitch/addendum/root diameter.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `kind` | `involute` \| `internal` \| `rack` \| `cycloid` \| `bevel` \| `worm` \| `timing` | nein | `"involute"` |  |
| `teeth` | integer \| string | nein | `15` | Number of teeth (number or integer parameter) |
| `module` | number \| string \| null | nein | `null` | Module in mm; empty = addon default |
| `height` | number \| string \| null | nein | `null` | Gear width in mm; empty = addon default |
| `properties` | object \| null | nein | `null` | Further gear properties, e.g. {pressure_angle: 20, backlash: 0.1, axle_hole: true, axle_holesize: 5, helix_angle: 15} |
| `body` | string \| null | nein | `null` | Body label; empty when there is only one body |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "kind": "involute",
  "teeth": "Gear_Teeth",
  "module": 1.5,
  "height": 8,
  "properties": {
    "backlash": 0.1
  },
  "purpose": "Drive"
}
```
