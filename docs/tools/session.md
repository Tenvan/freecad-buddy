# Session & Dokument — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Session]` · 3 Tools

| Tool | Zweck |
|---|---|
| [`get_status`](#get_status) | Status von FreeCAD und Bridge: Version, offene Dokumente, fehlende Objekttypen. Zuerst aufrufen. |
| [`document`](#document) | Document lifecycle. new: create and activate (then set_parameters → create_body → create_sketch → |
| [`undo`](#undo) | Letzte Änderung(en) rückgängig machen. Jeder Tool-Aufruf ist genau ein Schritt. |

## get_status

[Session] Status von FreeCAD und Bridge: Version, offene Dokumente, fehlende Objekttypen. Zuerst aufrufen.

Keine Parameter.

Beispiel:

```json
{}
```

## document

[Session] Document lifecycle. new: create and activate (then set_parameters → create_body → create_sketch →
add_profile → pad/pocket → details → check_printability → export_body); open: open and activate a
.FCStd; save: save as .FCStd; close: refuses with unsaved changes unless unsaved='save'/'discard' - ask
the user before discarding; revert: discard all changes since the last save (ask the user first).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `action` | `new` \| `open` \| `save` \| `close` \| `revert` | ja | `—` | new \| open \| save \| close \| revert |
| `name` | string \| null | nein | `null` | new: name of the new document |
| `path` | string \| null | nein | `null` | open: .FCStd file; save: target path (empty = current file, new documents need one); close: target for unsaved='save' on a never-saved document |
| `unsaved` | `refuse` \| `save` \| `discard` | nein | `"refuse"` | close: unsaved changes - refuse (default, error), save first, or discard them |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "action": "new",
  "name": "Box mit Deckel"
}
```

## undo

[Session] Letzte Änderung(en) rückgängig machen. Jeder Tool-Aufruf ist genau ein Schritt.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `steps` | integer | nein | `1` | Anzahl Schritte |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "steps": 1
}
```
