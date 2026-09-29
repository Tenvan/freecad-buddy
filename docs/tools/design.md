# Design-Tools — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Design tools]` · 3 Tools

| Tool | Zweck |
|---|---|
| [`fill_pattern`](#fill_pattern) | Fill a rectangular field with cut cells in one call and one undo step: round holes (sieve, perforation, |
| [`propose_design_tool`](#propose_design_tool) | Propose a missing design tool (task recurs or needs >= 5 tool calls, no design tool or addon fits). |
| [`list_design_tool_proposals`](#list_design_tool_proposals) | All design tool proposals, most requested first (name, count, problems, inputs, steps, examples). |

## fill_pattern

[Design tools] Fill a rectangular field with cut cells in one call and one undo step: round holes (sieve, perforation,
vent, speaker grille) or hex cells (honeycomb). Native and parametric: parameters <name>_Size/_Pitch/_Count_X/
_Count_Y, a fully constrained start-cell sketch, a pocket and one grid pattern; no addon needed.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `size` | number | ja | `—` | Cell size in mm: hole diameter (round) or across flats (hex) |
| `pitch` | number | ja | `—` | Centre distance of neighbouring cells in mm; web = pitch - size |
| `cell` | `round` \| `hex` | nein | `"round"` | round = holes (sieve, vent), hex = honeycomb cells |
| `count` | array<integer> \| null | nein | `null` | [cells per row, rows]; alternatively field |
| `field` | array<number \| string> \| null | nein | `null` | [width, height] of the field: mm, parameters or expressions (e.g. 'Plate_Width - 2*Rim_Width'); the counts follow changes |
| `margin` | number | nein | `0` | field: free border inside the field in mm |
| `center` | array<number \| string> \| null | nein | `null` | [x, y] of the field centre (numbers or parameters) |
| `plane` | `XY` \| `XZ` \| `YZ` | nein | `"XY"` |  |
| `offset` | number \| string | nein | `0` | Sketch plane offset, e.g. the plate thickness for the top face |
| `depth` | number \| null | nein | `null` | Cut depth in mm; empty = through all |
| `layout` | `rect` \| `hex` \| null | nein | `null` | hex offsets every second row by half a pitch; empty = hex for hex cells, else rect |
| `name` | string | nein | `"Fill"` | Prefix of parameters and labels, e.g. Sieve → Sieve_Pitch, Grid_Sieve |
| `body` | string \| null | nein | `null` | Body label; empty when there is only one body |
| `document` | string \| null | nein | `null` | Document name or label; empty = active |

Beispiel:

```json
{
  "size": 5,
  "pitch": 6,
  "cell": "hex",
  "field": [
    100,
    80
  ],
  "margin": 3,
  "offset": "Plate_Thickness",
  "name": "Honey"
}
```

## propose_design_tool

[Design tools] Propose a missing design tool (task recurs or needs >= 5 tool calls, no design tool or addon fits).
Proposals with the same name are merged and counted; a developer builds them as Buddy tools.
Still solve the current task with single steps.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `name` | string | ja | `—` | snake_case name of the missing tool, e.g. screw_boss |
| `problem` | string | ja | `—` | Which recurring task it solves |
| `inputs` | array<string> | ja | `—` | Inputs, e.g. ['outer_diameter', 'screw_size'] |
| `steps` | array<string> | ja | `—` | Tool calls it replaces, in order |
| `example` | string | ja | `—` | Concrete call as it would look, e.g. from this project |

Beispiel:

```json
{
  "name": "screw_boss",
  "problem": "Screw bosses with a pilot hole recur in every housing",
  "inputs": [
    "outer_diameter",
    "height",
    "screw_size"
  ],
  "steps": [
    "create_sketch",
    "add_profile circle",
    "pad",
    "create_sketch",
    "add_profile circle",
    "pocket"
  ],
  "example": "screw_boss(center=[10, 10], outer_diameter=7, height=12, screw_size='M3')"
}
```

## list_design_tool_proposals

[Design tools] All design tool proposals, most requested first (name, count, problems, inputs, steps, examples).

Keine Parameter.

Beispiel:

```json
{}
```
