# Baugruppe — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Assembly]` · 7 Tools

| Tool | Zweck |
|---|---|
| [`create_assembly`](#create_assembly) | Create an Assembly4 assembly in the document (bodies move into a 'Parts' group). Then |
| [`add_to_assembly`](#add_to_assembly) | Insert a body into the assembly as App::Link placed by Assembly4 (LCS_Origin * AttachmentOffset). |
| [`add_fastener`](#add_fastener) | Standard parts from the Fasteners workbench (needs the addon), placed in the assembly if there |
| [`search_parts`](#search_parts) | Search the step.parts catalogue of open STEP models (boards, fans, motors, bearings, profiles, |
| [`insert_part`](#insert_part) | Download a step.parts STEP model (cached) and insert it as a plain solid, in the assembly if |
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

## search_parts

[Assembly] Search the step.parts catalogue of open STEP models (boards, fans, motors, bearings, profiles,
fasteners): reference geometry for fits and cut-outs. Insert a hit with insert_part.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `query` | string | ja | `—` | Search terms, all must match, e.g. 'raspberry pi 5' or '608 bearing' |
| `category` | string \| null | nein | `null` | e.g. fastener, electronics, bearing, motion, thermal, power-transmission |
| `limit` | integer | nein | `10` |  |

Beispiel:

```json
{
  "query": "raspberry pi 5",
  "category": "electronics"
}
```

## insert_part

[Assembly] Download a step.parts STEP model (cached) and insert it as a plain solid, in the assembly if
there is one. Reference only: model own parts around it, do not print it.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `part_id` | string | ja | `—` | id from search_parts, e.g. 'raspberry_pi_5' |
| `position` | array<number> \| null | nein | `null` | [x, y, z]; empty = origin |
| `purpose` | string \| null | nein | `null` | Purpose for the label, e.g. 'Base' → 'Pad_Base' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "part_id": "raspberry_pi_5",
  "position": [
    0,
    0,
    3
  ],
  "purpose": "Pi"
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
