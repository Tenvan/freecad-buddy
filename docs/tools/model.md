# Modell & Parameter — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Model]` · 6 Tools

| Tool | Zweck |
|---|---|
| [`get_model_tree`](#get_model_tree) | Read the model tree: bodies with features in order, validity, sketch DoF, undo list and label |
| [`get_object`](#get_object) | Details of an object: status, expressions, the analysis for sketches, volume and size for solids. |
| [`delete_object`](#delete_object) | Delete an object (one undo step). |
| [`set_parameters`](#set_parameters) | Create/change central parameters in the VarSet 'Parameters'. Dimensions in sketches and features can use |
| [`list_parameters`](#list_parameters) | All parameters with type, value and expression reference. |
| [`create_body`](#create_body) | Create a PartDesign body for a part (one body = one printable part). |

## get_model_tree

[Model] Read the model tree: bodies with features in order, validity, sketch DoF, undo list and label
issues. Call before changes - the user may work in FreeCAD at the same time.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{}
```

## get_object

[Model] Details of an object: status, expressions, the analysis for sketches, volume and size for solids.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `ref` | string | ja | `—` | Object name or label |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "ref": "Sketch_Base"
}
```

## delete_object

[Model] Delete an object (one undo step).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `ref` | string | ja | `—` | Object name or label |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "ref": "Fillet_Top"
}
```

## set_parameters

[Model] Create/change central parameters in the VarSet 'Parameters'. Dimensions in sketches and features can use
the parameter name instead of a number - so the model stays editable by parameter in FreeCAD.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `parameters` | object | ja | `—` | Name → value or {value, type, description}; type: length (default), distance, angle, integer, float, bool. Names in English/ASCII, e.g. Box_Width. |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "parameters": {
    "Box_Width": 60,
    "Grip_Count": {
      "value": 12,
      "type": "integer"
    }
  }
}
```

## list_parameters

[Model] All parameters with type, value and expression reference.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{}
```

## create_body

[Model] Create a PartDesign body for a part (one body = one printable part).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `label` | string | ja | `—` | Part name, e.g. 'Box' or 'Lid' |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "label": "Box"
}
```
