# Session & Dokument — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Session]` · 6 Tools

| Tool | Zweck |
|---|---|
| [`get_status`](#get_status) | Status of FreeCAD and the bridge: version, open documents, missing object types. Call first. |
| [`storepoint`](#storepoint) | Mark a milestone in the design stream: a marker in the group 'Storepoints' linked to the current |
| [`list_storepoints`](#list_storepoints) | Storepoints of the document with position, timestamp, steps since the previous one and the |
| [`replay`](#replay) | Rebuild the design from its recorded stream up to a storepoint in a new document, over the same |
| [`document`](#document) | Document lifecycle. new: create and activate (then set_parameters → create_body → create_sketch → |
| [`undo`](#undo) | Undo the last change(s). Every tool call is exactly one step. |

## get_status

[Session] Status of FreeCAD and the bridge: version, open documents, missing object types. Call first.

Keine Parameter.

Beispiel:

```json
{}
```

## storepoint

[Session] Mark a milestone in the design stream: a marker in the group 'Storepoints' linked to the current
feature plus the description 'Storepoint n: name' on that feature. replay rebuilds the design up to
a storepoint in a new document.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `name` | string | ja | `—` | Unique name of the milestone, e.g. 'Base body' |
| `snapshot` | boolean | nein | `false` | Also save a copy of the document next to its file (needs a saved document) |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "name": "Base body"
}
```

## list_storepoints

[Session] Storepoints of the document with position, timestamp, steps since the previous one and the
linked feature; also the number of recorded steps and detected manual edits.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{}
```

## replay

[Session] Rebuild the design from its recorded stream up to a storepoint in a new document, over the same
tools and without changes: recover a broken model, rebuild after a FreeCAD update or branch a
variant. Python execution and addon installation are skipped and reported; manual GUI edits in the
original are not part of the stream (warning).

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `storepoint` | string | ja | `—` | Storepoint to rebuild up to (inclusive) |
| `into` | string | ja | `—` | Name of the new document (must not exist yet) |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "storepoint": "Base body",
  "into": "Box_Variant"
}
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
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "action": "new",
  "name": "Box mit Deckel"
}
```

## undo

[Session] Undo the last change(s). Every tool call is exactly one step.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `steps` | integer | nein | `1` | Number of steps |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "steps": 1
}
```
