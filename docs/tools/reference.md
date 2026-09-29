# Referenzen — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Reference]` · 4 Tools

| Tool | Zweck |
|---|---|
| [`datum_plane`](#datum_plane) | Datum plane as a stable sketch base (instead of a sketch on a solid face). |
| [`datum`](#datum) | Datum point, datum line or local coordinate system (LCS) as a stable parametric reference. |
| [`shape_binder`](#shape_binder) | Bind geometry of another body into this body (SubShapeBinder, follows its source). Use it as |
| [`select_geometry`](#select_geometry) | Preview which faces/edges a selector hits (with centre, normal, length, radius). |

## datum_plane

[Reference] Datum plane as a stable sketch base (instead of a sketch on a solid face).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `base` | string | nein | `"XY"` | XY, XZ or YZ |
| `offset` | number \| string | nein | `0` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `angle` | number \| string | nein | `0` | Number in mm/degrees or the name of a parameter (bound by expression) |
| `rotation_axis` | string | nein | `"X"` | X, Y or Z |
| `body` | string \| null | nein | `null` | Body-Label |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "base": "XY",
  "offset": "Box_Height",
  "purpose": "Top"
}
```

## datum

[Reference] Datum point, datum line or local coordinate system (LCS) as a stable parametric reference.
A datum line is an axis for revolve, helix and pattern(polar); an LCS is a sketch plane for
create_sketch; a datum point is external geometry for sketches.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `kind` | `point` \| `line` \| `lcs` | ja | `—` |  |
| `base` | string | nein | `"XY"` | Base plane XY, XZ or YZ; a line runs along its normal |
| `offset` | array<number \| string> \| null | nein | `null` | [x, y, z] in the base plane (x, y in the plane, z along the normal); numbers or parameters |
| `angle` | number \| string | nein | `0` | Tilt in degrees about rotation_axis |
| `rotation_axis` | string | nein | `"X"` | X, Y or Z |
| `body` | string \| null | nein | `null` | Body label; empty = the active/only body |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "kind": "line",
  "base": "XY",
  "offset": [
    "Hinge_X",
    0,
    0
  ],
  "purpose": "HingeAxis"
}
```

## shape_binder

[Reference] Bind geometry of another body into this body (SubShapeBinder, follows its source). Use it as
source for add_geometry type 'external' - the PartDesign way to reference across bodies.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sources` | array<string> | ja | `—` | Objects or elements of OTHER bodies: 'Object', 'Object:Element' or 'Body:Object[:Element]'; Element is EdgeN/FaceN/VertexN or g<N> of a sketch |
| `body` | string \| null | nein | `null` | Target body label |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "sources": [
    "Box:Sketch_Base"
  ],
  "body": "Lid",
  "purpose": "BoxOutline"
}
```

## select_geometry

[Reference] Preview which faces/edges a selector hits (with centre, normal, length, radius).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `selector` | string | ja | `—` | Semantic selector, e.g. edges:top, edges:vertical, edges:bottom, faces:top, faces:vertical (side walls), face:top, edges:circular,radius=2, edges:of_feature=Pocket_Cut. select_geometry previews the hits. |
| `target` | string \| null | nein | `null` | Feature label; empty = tip of the body |
| `body` | string \| null | nein | `null` | Body-Label |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "selector": "edges:parallel=X,y=Thickness,z=Thickness"
}
```
