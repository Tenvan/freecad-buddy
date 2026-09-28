# Experte — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Expert]` · 1 Tools

| Tool | Zweck |
|---|---|
| [`execute_python`](#execute_python) | Notausgang (nur mit FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD als ein Undo-Schritt. |

## execute_python

[Expert] Notausgang (nur mit FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD als ein Undo-Schritt.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `code` | string | ja | `—` | Python-Code; Variable 'result' wird zurückgegeben |
| `document` | string \| null | nein | `null` | Dokumentname oder -label; leer = aktives Dokument |

Beispiel:

```json
{
  "code": "result = len(doc.Objects)"
}
```
