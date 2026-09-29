# Regelwerk & Addons — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Rules & addons]` · 4 Tools

| Tool | Zweck |
|---|---|
| [`get_design_rules`](#get_design_rules) | Design rulebook for FreeCAD modelling and FDM printing (values from the active printer profile). |
| [`search_addons`](#search_addons) | Search the official FreeCAD addon catalogue (workbenches, macros, preference packs): hits with |
| [`get_addon`](#get_addon) | Details of an addon or macro: licence, maintainer, repository, last update, |
| [`install_addon`](#install_addon) | Install an addon or macro through FreeCAD's Addon Manager (needs FreeCAD's opt-in). FreeCAD shows the user |

## get_design_rules

[Rules & addons] Design rulebook for FreeCAD modelling and FDM printing (values from the active printer profile).
Read the matching topics before a new design, e.g. sketches and printing.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `topic` | string \| null | nein | `null` | Topic: workflow, parameters, sketches, references, features, assembly, naming, printing, design_tools, addons; empty = topic overview |

Beispiel:

```json
{
  "topic": "printing"
}
```

## search_addons

[Rules & addons] Search the official FreeCAD addon catalogue (workbenches, macros, preference packs): hits with
compatibility to the running FreeCAD and install status. Check before proposing an own design tool.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `query` | string | ja | `—` | Search terms, all must match, e.g. 'grid' or 'honeycomb' |
| `kind` | `any` \| `workbench` \| `macro` \| `preference_pack` | nein | `"any"` |  |
| `limit` | integer | nein | `10` |  |
| `refresh` | boolean | nein | `false` | Reload the catalogue now (otherwise at most daily) |

Beispiel:

```json
{
  "query": "grid",
  "kind": "any"
}
```

## get_addon

[Rules & addons] Details of an addon or macro: licence, maintainer, repository, last update,
dependencies (FreeCAD, addons, Python), compatibility, install status and README excerpt.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `addon_id` | string | ja | `—` | Id or name from search_addons, e.g. 'lattice2' |
| `readme` | boolean | nein | `true` | Load a README excerpt from the repository |

Beispiel:

```json
{
  "addon_id": "lattice2"
}
```

## install_addon

[Rules & addons] Install an addon or macro through FreeCAD's Addon Manager (needs FreeCAD's opt-in). FreeCAD shows the user
a confirmation dialog - ask in the chat first. Workbenches need a FreeCAD restart afterwards.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `addon_id` | string | ja | `—` | Id from search_addons/get_addon |
| `wait_seconds` | integer | nein | `300` | How long to wait for completion |

Beispiel:

```json
{
  "addon_id": "lattice2"
}
```
