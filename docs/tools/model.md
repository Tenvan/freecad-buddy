# Modell & Parameter — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Model]` · 6 Tools

| Tool | Zweck |
|---|---|
| [`get_model_tree`](#get_model_tree) | Modellbaum lesen: Bodies mit Features in Reihenfolge, Gültigkeit, DoF der Skizzen, Undo-Liste und |
| [`get_object`](#get_object) | Details eines Objekts: Status, Expressions, bei Skizzen die Analyse, bei Körpern Volumen und Maße. |
| [`delete_object`](#delete_object) | Objekt löschen (ein Undo-Schritt). |
| [`set_parameters`](#set_parameters) | Zentrale Parameter im VarSet 'Parameters' anlegen/ändern. Maße in Skizzen und Features können den |
| [`list_parameters`](#list_parameters) | Alle Parameter mit Typ, Wert und Expression-Referenz. |
| [`create_body`](#create_body) | PartDesign-Body für ein Bauteil anlegen (ein Body = ein druckbares Teil). |

## get_model_tree

[Model] Modellbaum lesen: Bodies mit Features in Reihenfolge, Gültigkeit, DoF der Skizzen, Undo-Liste und
Label-Probleme. Vor Änderungen aufrufen – der Nutzer kann parallel in FreeCAD arbeiten.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{}
```

## get_object

[Model] Details eines Objekts: Status, Expressions, bei Skizzen die Analyse, bei Körpern Volumen und Maße.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `ref` | string | ja | `—` | Objektname oder Label |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "ref": "Sketch_Base"
}
```

## delete_object

[Model] Objekt löschen (ein Undo-Schritt).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `ref` | string | ja | `—` | Objektname oder Label |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "ref": "Fillet_Top"
}
```

## set_parameters

[Model] Zentrale Parameter im VarSet 'Parameters' anlegen/ändern. Maße in Skizzen und Features können den
Parameternamen statt einer Zahl nutzen – so bleibt das Modell in FreeCAD per Parameter änderbar.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `parameters` | object | ja | `—` | Name → Wert oder {value, type, description}; type: length (Standard), distance, angle, integer, float, bool. Namen englisch/ASCII, z. B. Box_Width. |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

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

[Model] Alle Parameter mit Typ, Wert und Expression-Referenz.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{}
```

## create_body

[Model] PartDesign-Body für ein Bauteil anlegen (ein Body = ein druckbares Teil).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `label` | string | ja | `—` | Bauteilname, z. B. 'Box' oder 'Lid' |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "label": "Box"
}
```
