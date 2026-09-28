# Referenzen — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Reference]` · 3 Tools

| Tool | Zweck |
|---|---|
| [`datum_plane`](#datum_plane) | Bezugsebene als stabile Skizzenbasis (statt Skizze auf Körperfläche). |
| [`shape_binder`](#shape_binder) | Bind geometry of another body into this body (SubShapeBinder, follows its source). Use it as |
| [`select_geometry`](#select_geometry) | Vorschau: welche Flächen/Kanten ein Selektor trifft (mit Mittelpunkt, Normale, Länge, Radius). |

## datum_plane

[Reference] Bezugsebene als stabile Skizzenbasis (statt Skizze auf Körperfläche).

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

## shape_binder

[Reference] Bind geometry of another body into this body (SubShapeBinder, follows its source). Use it as
source for add_geometry type 'external' - the PartDesign way to reference across bodies.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `sources` | array<string> | ja | `—` | Objects or elements of OTHER bodies: 'Object', 'Object:Element' or 'Body:Object[:Element]'; Element is EdgeN/FaceN/VertexN or g<N> of a sketch |
| `body` | string \| null | nein | `null` | Target body label |
| `purpose` | string \| null | nein | `null` | Zweck für das Label, z. B. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

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

[Reference] Vorschau: welche Flächen/Kanten ein Selektor trifft (mit Mittelpunkt, Normale, Länge, Radius).

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
