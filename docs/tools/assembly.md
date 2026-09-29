# Baugruppe — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Assembly]` · 5 Tools

| Tool | Zweck |
|---|---|
| [`create_assembly`](#create_assembly) | Create an Assembly4 assembly in the document (bodies move into a 'Parts' group). Then |
| [`add_to_assembly`](#add_to_assembly) | Insert a body into the assembly as App::Link placed by Assembly4 (LCS_Origin * AttachmentOffset). |
| [`add_fastener`](#add_fastener) | Standard parts from the Fasteners workbench (needs the addon), placed in the assembly if there |
| [`explode_assembly`](#explode_assembly) | Exploded view as Assembly4 configuration: saves 'Assembled' once, moves the listed parts and |
| [`apply_configuration`](#apply_configuration) | Apply a saved Assembly4 configuration (positions of all assembly parts). |

## create_assembly

[Assembly] Create an Assembly4 assembly in the document (bodies move into a 'Parts' group). Then
add_to_assembly for each body, add_fastener for standard parts, explode_assembly for an exploded view.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `label` | string | nein | `"Assembly"` | Assembly label |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{}
```

## add_to_assembly

[Assembly] Insert a body into the assembly as App::Link placed by Assembly4 (LCS_Origin * AttachmentOffset).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `part` | string | ja | `—` | Body or App::Part label |
| `label` | string \| null | nein | `null` | Link label; empty = part label |
| `offset` | array<number> \| null | nein | `null` | [x, y, z] from the modelled position; empty = in place |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "part": "Box"
}
```

## add_fastener

[Assembly] Standard parts from the Fasteners workbench (needs the addon), placed in the assembly if there
is one. Stack e.g. a washer on the plate and the nut on top of the washer.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `type` | string | ja | `—` | Fasteners type, e.g. ISO4032 (hex nut), ISO7089 (washer), ISO4762 (screw) |
| `diameter` | string | ja | `—` | Size, e.g. 'M10' |
| `positions` | array<array<number>> | ja | `—` | One [x, y, z] per fastener (bottom face) |
| `thread` | boolean | nein | `false` | Model the real thread (slower) |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "type": "ISO4032",
  "diameter": "M10",
  "positions": [
    [
      85,
      35,
      7
    ]
  ]
}
```

## explode_assembly

[Assembly] Exploded view as Assembly4 configuration: saves 'Assembled' once, moves the listed parts and
saves the result. Switch back and forth with apply_configuration.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `moves` | object | ja | `—` | Label -> [dx, dy, dz] from the assembled position |
| `name` | string | nein | `"Exploded"` | Configuration name |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "moves": {
    "Lid": [
      0,
      0,
      60
    ]
  }
}
```

## apply_configuration

[Assembly] Apply a saved Assembly4 configuration (positions of all assembly parts).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `name` | string | ja | `—` | Configuration, e.g. 'Assembled' or 'Exploded' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "name": "Assembled"
}
```
