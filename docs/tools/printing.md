# 3D-Druck — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Print]` · 4 Tools

| Tool | Zweck |
|---|---|
| [`get_printer_profile`](#get_printer_profile) | Active printer profile (build volume, nozzle, minimum wall, overhang angle, fit clearance). |
| [`set_printer_profile`](#set_printer_profile) | Change the printer profile (stored permanently). |
| [`check_printability`](#check_printability) | Check printability: valid solid, build volume, overhangs, wall thickness, too small details. |
| [`export_body`](#export_body) | Export the part (placed on the print bed) and verify the file by re-importing it. With OrcaSlicer |

## get_printer_profile

[Print] Active printer profile (build volume, nozzle, minimum wall, overhang angle, fit clearance).

Keine Parameter.

Beispiel:

```json
{}
```

## set_printer_profile

[Print] Change the printer profile (stored permanently).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `updates` | object | ja | `—` | Profile values to change, e.g. {nozzle: 0.6} |

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

[Print] Check printability: valid solid, build volume, overhangs, wall thickness, too small details.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `target` | string \| null | nein | `null` | Body/object; empty = the only body |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "target": "Box"
}
```

## export_body

[Print] Export the part (placed on the print bed) and verify the file by re-importing it. With OrcaSlicer
installed, stl/3mf are sliced too: print time and filament in 'slice'.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `format` | `stl` \| `3mf` \| `step` | nein | `"3mf"` |  |
| `target` | string \| null | nein | `null` | Body/object; empty = the only body |
| `path` | string \| null | nein | `null` | File or folder; empty = <document folder>/export |
| `place_on_bed` | boolean | nein | `true` |  |
| `overwrite` | boolean | nein | `false` | Overwrite an existing file |
| `slice` | boolean \| null | nein | `null` | Slice with the OrcaSlicer CLI; empty = only if OrcaSlicer is installed |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "format": "3mf",
  "target": "Box"
}
```
