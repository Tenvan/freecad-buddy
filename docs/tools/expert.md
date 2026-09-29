# Experte — Tool-Katalog

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten. Übersicht: [Tool-Katalog](../tools.md).

Kategorie-Präfix: `[Expert]` · 1 Tools

| Tool | Zweck |
|---|---|
| [`execute_python`](#execute_python) | Escape hatch (only with FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD as one undo step. |

## execute_python

[Expert] Escape hatch (only with FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD as one undo step.

| Parameter | Typ | Pflicht | Standard | Beschreibung |
|---|---|---|---|---|
| `code` | string | ja | `—` | Python code; the variable 'result' is returned |
| `document` | string \| null | nein | `null` | Document name or label; empty = active document |

Beispiel:

```json
{
  "code": "result = len(doc.Objects)"
}
```
