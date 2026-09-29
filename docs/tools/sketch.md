# Skizze — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Sketch]` · 6 Tools

| Tool | Zweck |
|---|---|
| [`create_sketch`](#create_sketch) | Create a sketch on a stable reference. Prefer origin planes with offset or a datum_plane. |
| [`add_profile`](#add_profile) | Draw a fully constrained profile like a person would: symmetric to the origin, Equal instead of |
| [`add_geometry`](#add_geometry) | Add low-level geometry or external references. Returns g<N> (own) and x<N> (external) references |
| [`add_constraints`](#add_constraints) | Add constraints. Conflicting/redundant constraints are rejected (rollback). |
| [`analyze_sketch`](#analyze_sketch) | Sketch analysis: DoF, conflicts, redundancies, closed wires, external geometry (x<N> with source) |
| [`fully_constrain_sketch`](#fully_constrain_sketch) | Find or close remaining degrees of freedom (coincidences, H/V, then named X/Y dimensions). Never Block. |

## create_sketch

[Sketch] Create a sketch on a stable reference. Prefer origin planes with offset or a datum_plane.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `plane` | string | nein | `"XY"` | XY, XZ, YZ (body origin), label of a datum plane or face:<selector> |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `offset` | number \| string | nein | `0` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `body` | string \| null | nein | `null` | Body label; empty when there is only one body |
| `reversed` | boolean | nein | `false` |  |
| `allow_face_attachment` | boolean | nein | `false` | Only if needed: face references are prone to topology changes |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "plane": "XY",
  "purpose": "Base",
  "offset": "Lid_Plate"
}
```

## add_profile

[Sketch] Draw a fully constrained profile like a person would: symmetric to the origin, Equal instead of
duplicate dimensions, named dimensions. The result contains the sketch analysis (DoF must be 0).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label |
| `kind` | `rectangle` \| `rounded_rectangle` \| `slot` \| `circle` \| `polygon` \| `hole_rect` \| `polyline` \| `u_path` | ja | `—` | Profilart |
| `params` | object | ja | `—` | rectangle: width, height, [center=[x,y]], [anchor=center\|corner]; rounded_rectangle: width, height, radius, [center]; slot: length (centre distance), width, [center]; circle: diameter, [center]; polygon: sides, diameter\|across_flats, [center], [orientation=flat\|pointy]; hole_rect: width, height (hole distances), diameter, [center]; polyline: points=[[x,y],…]; u_path (open bracket path for sweep): length (leg distance), height, radius. Values: number or parameter name. |
| `prefix` | string \| null | nein | `null` | Prefix for dimension names, e.g. 'Base' → Base_Width |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

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

[Sketch] Add low-level geometry or external references. Returns g<N> (own) and x<N> (external) references
for add_constraints. Define hole patterns once in a layout sketch and reference them here.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Sketch label |
| `items` | array<object> | ja | `—` | {type: line, start, end} \| {type: circle, center, radius} \| {type: arc, center, radius, start_angle, end_angle} (degrees, counter-clockwise) \| {type: point, at}; optional construction: true. External geometry: {type: external, source, element, defining?, allow_face_reference?} - source is an earlier sketch, datum or shape_binder in the same body; element is g<N>[.start\|end\|center] of a source sketch (real geometry, not construction) or EdgeN/VertexN/edge selector otherwise; defining: true makes the edge part of the profile |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

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

[Sketch] Add constraints. Conflicting/redundant constraints are rejected (rollback).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Sketch label |
| `items` | array<object> | ja | `—` | {type, a, b?, about?, value?, name?}. References: g<N> (own), x<N> (external), each with .start\|end\|center, origin, x_axis, y_axis. Types: coincident, horizontal, vertical, parallel, perpendicular, equal, tangent, point_on_object, symmetric, distance, distance_x, distance_y, radius, diameter, angle (degrees). value: number, parameter name or expression; always name dimensions. |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

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

[Sketch] Sketch analysis: DoF, conflicts, redundancies, closed wires, external geometry (x<N> with source)
and style lint (incl. broken external references).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Sketch label |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "sketch": "Sketch_Base"
}
```

## fully_constrain_sketch

[Sketch] Find or close remaining degrees of freedom (coincidences, H/V, then named X/Y dimensions). Never Block.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sketch` | string | ja | `—` | Skizzen-Label |
| `apply` | boolean | nein | `false` | false = suggestions only, true = apply |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "sketch": "Sketch_Base",
  "apply": false
}
```
