# 3D-Druck — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Print]` · 4 Tools

| Tool | Zweck |
|---|---|
| [`get_printer_profile`](#get_printer_profile) | Aktives Druckerprofil (Bauraum, Düse, Mindestwand, Überhangwinkel, Passungsspiel). |
| [`set_printer_profile`](#set_printer_profile) | Druckerprofil ändern (dauerhaft gespeichert). |
| [`check_printability`](#check_printability) | Druckbarkeit prüfen: gültiger Solid, Bauraum, Überhänge, Wandstärke, zu kleine Details. |
| [`export_body`](#export_body) | Bauteil exportieren (auf das Druckbett gelegt) und die Datei per Reimport prüfen. |

## get_printer_profile

[Print] Aktives Druckerprofil (Bauraum, Düse, Mindestwand, Überhangwinkel, Passungsspiel).

Keine Parameter.

Beispiel:

```json
{}
```

## set_printer_profile

[Print] Druckerprofil ändern (dauerhaft gespeichert).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `updates` | object | ja | `—` | Zu ändernde Profilwerte, z. B. {nozzle: 0.6} |

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

[Print] Druckbarkeit prüfen: gültiger Solid, Bauraum, Überhänge, Wandstärke, zu kleine Details.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `target` | string \| null | nein | `null` | Body/Objekt; leer = einziger Body |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "target": "Box"
}
```

## export_body

[Print] Bauteil exportieren (auf das Druckbett gelegt) und die Datei per Reimport prüfen.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `format` | `stl` \| `3mf` \| `step` | nein | `"3mf"` |  |
| `target` | string \| null | nein | `null` | Body/Objekt; leer = einziger Body |
| `path` | string \| null | nein | `null` | Datei oder Ordner; leer = <Dokumentordner>/export |
| `place_on_bed` | boolean | nein | `true` |  |
| `overwrite` | boolean | nein | `false` | Vorhandene Datei überschreiben |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "format": "3mf",
  "target": "Box"
}
```
