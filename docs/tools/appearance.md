# Material & Ansicht — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Appearance]` · 3 Tools

| Tool | Zweck |
|---|---|
| [`set_material`](#set_material) | Assign a FreeCAD library material (density -> mass) and/or the display colour of a body. |
| [`set_view`](#set_view) | Set the live view in FreeCAD (it stays that way): default iso + fit everything. Call as the last |
| [`screenshot`](#screenshot) | Image of the 3D view for a visual check (only with a running FreeCAD GUI). |

## set_material

[Appearance] Assign a FreeCAD library material (density -> mass) and/or the display colour of a body.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `target` | string | ja | `—` | Body, part or link label |
| `material` | string \| null | nein | `null` | Library material: 'PLA' or 'ABS' (no PETG in the library), a full name or UUID |
| `color` | string \| array<number> \| null | nein | `null` | Display colour: name (red, yellow, ...), '#RRGGBB' or [r,g,b] |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "target": "Lid",
  "material": "ABS",
  "color": "red"
}
```

## set_view

[Appearance] Set the live view in FreeCAD (it stays that way): default iso + fit everything. Call as the last
step; after the first base feature the server sets it itself (FreeCAD GUI only).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `view` | `iso` \| `dimetric` \| `trimetric` \| `front` \| `back` \| `top` \| `bottom` \| `left` \| `right` \| `current` | nein | `"iso"` |  |
| `fit` | boolean | nein | `true` | Fit everything so the whole part is visible |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "view": "iso",
  "fit": true
}
```

## screenshot

[Appearance] Image of the 3D view for a visual check (only with a running FreeCAD GUI).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `view` | `iso` \| `dimetric` \| `trimetric` \| `front` \| `back` \| `top` \| `bottom` \| `left` \| `right` \| `current` | nein | `"iso"` |  |
| `width` | integer | nein | `800` |  |
| `height` | integer | nein | `600` |  |
| `fit` | boolean | nein | `true` |  |
| `isolate` | string \| null | nein | `null` | Nur dieses Objekt zeigen |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "view": "iso",
  "width": 800,
  "height": 600
}
```
