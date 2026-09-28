# Material & Ansicht — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Appearance]` · 3 Tools

| Tool | Zweck |
|---|---|
| [`set_material`](#set_material) | Assign a FreeCAD library material (density -> mass) and/or the display colour of a body. |
| [`set_view`](#set_view) | Live-Ansicht in FreeCAD setzen (bleibt so stehen): Standard iso + alles einpassen. Als letzten |
| [`screenshot`](#screenshot) | Bild der 3D-Ansicht zur visuellen Kontrolle (nur mit laufender FreeCAD-GUI). |

## set_material

[Appearance] Assign a FreeCAD library material (density -> mass) and/or the display colour of a body.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `target` | string | ja | `—` | Body, part or link label |
| `material` | string \| null | nein | `null` | Library material: 'PLA', 'ABS', 'PETG', a full name or UUID |
| `color` | string \| array<number> \| null | nein | `null` | Display colour: name (red, yellow, ...), '#RRGGBB' or [r,g,b] |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "target": "Lid",
  "material": "ABS",
  "color": "red"
}
```

## set_view

[Appearance] Live-Ansicht in FreeCAD setzen (bleibt so stehen): Standard iso + alles einpassen. Als letzten
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

[Appearance] Bild der 3D-Ansicht zur visuellen Kontrolle (nur mit laufender FreeCAD-GUI).

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
