"""Design tools: recurring multi-step tasks as one call and one undo step.

A design tool only composes existing features (parameters, sketch, pocket, pattern) inside one
transaction; its parameters land in the VarSet, so the result stays editable in the GUI.
"""

from __future__ import annotations

import math
import re
from typing import Any

from buddy_core import features, parameters, values
from buddy_core.documents import resolve_document
from buddy_core.errors import validation
from buddy_core.result import ToolResult
from buddy_core.sketch import model, profiles
from buddy_core.sketch.builder import SketchBuilder
from buddy_core.transaction import transaction

_AXES = {"XY": ("X", "Y"), "XZ": ("X", "Z"), "YZ": ("Y", "Z")}
"""Body directions of the sketch's horizontal and vertical axis on each origin plane."""
_ROW = {"rect": 1.0, "hex": math.sqrt(3) / 2}
"""Row distance as a fraction of the pitch; hex rows are offset by half a pitch."""
_HEIGHT = {"round": 1.0, "hex": 2 / math.sqrt(3)}
"""Cell height as a fraction of its size (hex cells stand on a corner, size = across flats)."""
_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
_EPS = 1e-6


def _fits(extent: float, margin: float, cell: float, pitch: float, extra: float) -> int:
    return math.floor((extent - 2 * margin - cell - extra) / pitch + _EPS) + 1


def _counts(
    cell: str,
    layout: str,
    size: float,
    pitch: float,
    count: list[int] | None,
    field: list[float] | None,
    margin: float,
) -> tuple[int, int]:
    if (count is None) == (field is None):
        raise validation("fill_pattern needs either count=[x, y] or field=[width, height]")
    row = pitch * _ROW[layout]
    height = size * _HEIGHT[cell]
    if count is not None:
        if len(count) != 2 or any(not isinstance(n, int) or isinstance(n, bool) for n in count):
            raise validation("count must be [x, y] with whole numbers")
        nx, ny = count
    else:
        if field is None or len(field) != 2 or min(field) <= 0:
            raise validation("field must be [width, height] > 0")
        nx = _fits(field[0], margin, size, pitch, pitch / 2 if layout == "hex" else 0)
        ny = _fits(field[1], margin, height, row, 0)
        if layout == "hex":
            ny -= ny % 2
    need_rows = 4 if layout == "hex" else 2
    if nx < 2 or ny < need_rows:
        extra = " + pitch/2" if layout == "hex" else ""
        need_w = 2 * margin + size + pitch + (pitch / 2 if layout == "hex" else 0)
        need_h = 2 * margin + height + (need_rows - 1) * row
        raise validation(
            f"Pattern {nx} x {ny} is too small: needs >= 2 cells per row and >= {need_rows} rows. "
            f"Width = 2*margin + size + (count_x - 1)*pitch{extra}, "
            f"so the field needs at least {need_w:.2f} x {need_h:.2f} mm; enlarge the field or reduce the pitch"
        )
    if layout == "hex" and ny % 2:
        raise validation(f"layout 'hex' needs an even row count (pairs of offset rows), got {ny}")
    return nx, ny


def _count_expression(cell: str, layout: str, e: dict[str, str], vertical: bool) -> str:
    """FreeCAD expression that derives a cell count from the field size (follows parameter changes)."""
    extent = e["Height"] if vertical else e["Width"]
    step = f"{e['Pitch']} * {_ROW[layout]:.12g}" if vertical else e["Pitch"]
    cell_extent = f"{e['Size']} * {_HEIGHT[cell]:.12g}" if vertical else e["Size"]
    extra = f" - {e['Pitch']} / 2" if layout == "hex" and not vertical else ""
    fits = f"floor(({extent} - 2 * {e['Margin']} - {cell_extent}{extra}) / ({step}) + {_EPS}) + 1"
    return f"2 * floor(({fits}) / 2)" if layout == "hex" and vertical else fits


def fill_pattern(
    size: float,
    pitch: float,
    cell: str = "round",
    count: list[int] | None = None,
    field: list[values.ValueSpec] | None = None,
    margin: float = 0,
    center: list[values.ValueSpec] | None = None,
    plane: str = "XY",
    offset: values.ValueSpec = 0,
    depth: float | None = None,
    layout: str | None = None,
    name: str = "Fill",
    body: str | None = None,
    document: str | None = None,
) -> ToolResult:
    """Fill a rectangular field with cut cells: ``cell`` ``round`` (sieve, perforation, vent) or ``hex``
    (honeycomb, ``size`` = across flats). Built natively from parameters, one start-cell sketch, a pocket
    and one grid pattern (MultiTransform): fast, parametric, no addon needed to open the file.

    ``count`` fixes the cells per direction, ``field`` derives them from the field size minus ``margin``.
    ``layout`` ``hex`` offsets every second row by half a pitch (default for hex cells: honeycomb with an
    even web of ``pitch - size``), ``rect`` is a square raster (default for round cells).
    """
    doc = resolve_document(document)
    if cell not in _HEIGHT:
        raise validation("cell must be 'round' or 'hex'")
    layout = layout or ("hex" if cell == "hex" else "rect")
    if layout not in _ROW:
        raise validation("layout must be 'rect' or 'hex'")
    if plane.upper() not in _AXES:
        raise validation("fill_pattern needs an origin plane XY, XZ or YZ (use offset for the height)")
    if not _NAME.match(name):
        raise validation(f"name '{name}' must be letters and digits, starting with a letter (e.g. Sieve)")
    if size <= 0 or pitch <= 0 or margin < 0 or (depth is not None and depth <= 0):
        raise validation("size, pitch and depth must be > 0, margin >= 0")
    if size >= pitch:
        raise validation(
            f"size {size:g} must be smaller than pitch {pitch:g} (web = pitch - size); "
            f"e.g. pitch {size + 0.8:g} leaves a 0.8 mm web"
        )
    bound: list[values.Value] = []
    if field is not None:
        if len(field) != 2:
            raise validation("field must be [width, height] > 0")
        bound = [values.resolve(doc, spec, "field") for spec in field]  # numbers, parameters or expressions
    numbers = [value.number for value in bound] if field is not None else None
    nx, ny = _counts(cell, layout, size, pitch, count, numbers, margin)
    p = {
        key: f"{name}_{key}"
        for key in ("Size", "Pitch", "Count_X", "Count_Y", "Width", "Height", "Margin", "Depth")
    }
    what = "hole diameter" if cell == "round" else "cell size across flats"
    specs: dict[str, Any] = {
        p["Size"]: {"value": size, "description": f"{name}: {what}"},
        p["Pitch"]: {"value": pitch, "description": f"{name}: cell distance (web = pitch - size)"},
        p["Count_X"]: {"value": nx, "type": "integer", "description": f"{name}: cells per row"},
        p["Count_Y"]: {"value": ny, "type": "integer", "description": f"{name}: rows"},
    }
    if field is not None:
        specs[p["Width"]] = {"value": bound[0].number, "description": f"{name}: field width"}
        specs[p["Height"]] = {"value": bound[1].number, "description": f"{name}: field height"}
        specs[p["Margin"]] = {"value": margin, "description": f"{name}: free border inside the field"}
    if depth is not None:
        specs[p["Depth"]] = {"value": depth, "description": f"{name}: cut depth"}
    taken = sorted(set(specs) & {entry["name"] for entry in parameters.list_parameters(doc)})
    if taken:
        raise validation(f"Parameters {', '.join(taken)} already exist; choose another name for this fill")

    row = _ROW[layout]
    cx, cy = center or [0, 0]
    span_x = f"({p['Count_X']} - 1) * {p['Pitch']}" + (f" + {p['Pitch']} / 2" if layout == "hex" else "")
    span_y = f"({p['Count_Y']} - 1) * {p['Pitch']} * {row:.12g}"
    x0, y0 = f"({cx}) - ({span_x}) / 2", f"({cy}) - ({span_y}) / 2"
    starts = [[x0, y0]]
    if layout == "hex":
        starts.append([f"{x0} + {p['Pitch']} / 2", f"{y0} + {p['Pitch']} * {row:.12g}"])
    horizontal, vertical = _AXES[plane.upper()]
    rows_per_step = 2 if layout == "hex" else 1

    def draw(doc: Any, sk: Any, _: ToolResult) -> None:
        builder = SketchBuilder(sk, name)
        for start in starts:
            if cell == "round":
                profiles.circle(builder, doc, {"diameter": p["Size"], "center": start})
            else:
                hexagon = {"sides": 6, "across_flats": p["Size"], "center": start, "orientation": "pointy"}
                profiles.polygon(builder, doc, hexagon)

    result = ToolResult()
    with transaction(doc, f"Fill pattern: {name}"):
        steps = [parameters.set_parameters(doc, specs)]
        if field is not None:
            varset = parameters.find_varset(doc)
            assert varset is not None  # set_parameters just created it
            for key, value in zip(("Width", "Height"), bound, strict=True):
                if value.expression:  # e.g. Plate_Width - 2*Rim_Width: the field follows the part
                    varset.setExpression(p[key], value.expression)
            e = {key: parameters.expression(param) for key, param in p.items()}
            varset.setExpression(p["Count_X"], _count_expression(cell, layout, e, vertical=False))
            varset.setExpression(p["Count_Y"], _count_expression(cell, layout, e, vertical=True))
        created = model.create_sketch(
            plane.upper(), purpose=name, offset=offset, body=body, document=doc.Name
        )
        sketch = created.data["sketch"]["name"]
        steps += [created, model.sketch_edit(sketch, doc.Name, "Fill pattern start cells", draw)]
        pocket = features.pocket(
            sketch, depth=p["Depth"] if depth is not None else 5,
            mode="through_all" if depth is None else "length", purpose=name, document=doc.Name,
        )  # fmt: skip
        grid = features.pattern(
            [pocket.data["feature"]["name"]], "grid", direction=horizontal, length=f"({p['Count_X']} - 1) * {p['Pitch']}",
            count=p["Count_X"], direction2=vertical,
            length2=f"({p['Count_Y']} / {rows_per_step} - 1) * {p['Pitch']} * {row * rows_per_step:.12g}",
            count2=p["Count_Y"] if rows_per_step == 1 else f"{p['Count_Y']} / 2", purpose=name, document=doc.Name,
        )  # fmt: skip
        steps += [pocket, grid]
    for step in steps:
        result.created += [entry for entry in step.created if entry not in result.created]
        result.warnings += step.warnings
    result.data.update(
        feature=grid.data["feature"], volume=grid.data["volume"], cell=cell, layout=layout, count=[nx, ny],
        cells=nx * ny, parameters=list(specs),
    )  # fmt: skip
    follow = (
        "the counts follow the field size" if field is not None else f"change {p['Count_X']}/{p['Count_Y']}"
    )
    result.hints.append(f"Edit {p['Pitch']} or {p['Size']} with set_parameters; {follow}.")
    return result
