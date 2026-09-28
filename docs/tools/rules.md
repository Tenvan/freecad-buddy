# Regelwerk & Addons — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Rules & addons]` · 4 Tools

| Tool | Zweck |
|---|---|
| [`get_design_rules`](#get_design_rules) | Design-Regelwerk für FreeCAD-Konstruktion und FDM-Druck (Werte aus dem aktiven Druckerprofil). |
| [`search_addons`](#search_addons) | Offiziellen FreeCAD-Addon-Katalog durchsuchen (Workbenches, Makros, Preference Packs): Treffer mit |
| [`get_addon`](#get_addon) | Details eines Addons oder Makros: Lizenz, Maintainer, Repository, letzte Aktualisierung, |
| [`install_addon`](#install_addon) | Install an addon or macro through FreeCAD's Addon Manager (needs FreeCAD's opt-in). FreeCAD shows the user |

## get_design_rules

[Rules & addons] Design-Regelwerk für FreeCAD-Konstruktion und FDM-Druck (Werte aus dem aktiven Druckerprofil).
Vor einer neuen Konstruktion die passenden Themen lesen, z. B. sketches und printing.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `topic` | string \| null | nein | `null` | Thema: workflow, parameters, sketches, references, features, assembly, naming, printing, design_tools, addons; leer = Themenübersicht |

Beispiel:

```json
{
  "topic": "printing"
}
```

## search_addons

[Rules & addons] Offiziellen FreeCAD-Addon-Katalog durchsuchen (Workbenches, Makros, Preference Packs): Treffer mit
Kompatibilität zum laufenden FreeCAD und Installationsstatus. Vor einem eigenen Design-Tool prüfen.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `query` | string | ja | `—` | Suchbegriffe, alle müssen passen, z. B. 'grid' oder 'honeycomb' |
| `kind` | `any` \| `workbench` \| `macro` \| `preference_pack` | nein | `"any"` |  |
| `limit` | integer | nein | `10` |  |
| `refresh` | boolean | nein | `false` | Katalog sofort neu laden (sonst höchstens täglich) |

Beispiel:

```json
{
  "query": "grid",
  "kind": "any"
}
```

## get_addon

[Rules & addons] Details eines Addons oder Makros: Lizenz, Maintainer, Repository, letzte Aktualisierung,
Abhängigkeiten (FreeCAD, Addons, Python), Kompatibilität, Installationsstatus und README-Auszug.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `addon_id` | string | ja | `—` | Id oder Name aus search_addons, z. B. 'lattice2' |
| `readme` | boolean | nein | `true` | README-Auszug aus dem Repository laden |

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
