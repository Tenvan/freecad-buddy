"""AC-10 (freecad-buddy-referenzen): fan clamp frame v3 - the hole pattern has exactly one source.

Ralf's construction: a layout sketch holds a construction line of length Mount_Diag symmetric to
the origin, the two mounting holes sit at its ends and one distance to the frame edge aligns the
line automatically. Lugs and screw-head pockets reference the hole circles as external geometry;
the holes are drilled directly from the layout sketch.
"""

import math
from typing import Any

from buddy_core import features
from buddy_core.sketch import lowlevel

from .conftest import profile, set_params, sketch_on

PARAMS = {
    "Fan_W": 50,
    "Fan_H": 12,
    "Fit": 0.15,
    "Wall": 2,
    "Rim_T": 1.2,
    "Rim_W": 1.5,
    "Mount_Diag": 70,
    "Mount_Hole_D": 3.4,
    "Head_D": 6.5,
    "Lug_D": 10,
    "Lug_Floor": 3,
}
FRAME = "Fan_W + 2 * Fit + 2 * Wall"
TOP = "Fan_H + Rim_T"


def geometry(doc: Any, sketch: Any, *items: dict[str, Any]) -> list[str]:
    return lowlevel.add_geometry(sketch.Name, list(items), doc.Name).to_dict()["geometry"]


def constraints(doc: Any, sketch: Any, *items: dict[str, Any]) -> dict[str, Any]:
    return lowlevel.add_constraints(sketch.Name, list(items), doc.Name).to_dict()["sketch"]


def mount_point(values: dict[str, float]) -> tuple[float, float]:
    x = values["Fan_W"] / 2 + values["Fit"] + 2 * values["Wall"] + values["Head_D"] / 2
    return x, math.sqrt((values["Mount_Diag"] / 2) ** 2 - x**2)


def layout(doc: Any) -> Any:
    x, y = mount_point(PARAMS)
    edge = PARAMS["Fan_W"] / 2 + PARAMS["Fit"] + PARAMS["Wall"]
    sketch = sketch_on(doc, purpose="Layout", offset=TOP)
    geometry(
        doc,
        sketch,
        {"type": "line", "start": [-x, -y], "end": [x, y], "construction": True},  # g0 mount line
        {"type": "circle", "center": [x, y], "radius": 1.7},  # g1 hole
        {"type": "circle", "center": [-x, -y], "radius": 1.7},  # g2 hole
        {"type": "line", "start": [edge, -5], "end": [edge, 5], "construction": True},  # g3 frame edge
    )
    report = constraints(
        doc,
        sketch,
        {"type": "symmetric", "a": "g0.start", "b": "g0.end", "about": "origin"},
        {"type": "distance", "a": "g0", "value": "Mount_Diag", "name": "Mount_Diag"},
        {"type": "coincident", "a": "g1.center", "b": "g0.end"},
        {"type": "coincident", "a": "g2.center", "b": "g0.start"},
        {"type": "diameter", "a": "g1", "value": "Mount_Hole_D", "name": "Mount_Hole_D"},
        {"type": "equal", "a": "g1", "b": "g2"},
        {"type": "symmetric", "a": "g3.start", "b": "g3.end", "about": "x_axis"},  # implies vertical
        {"type": "distance", "a": "g3", "value": 10, "name": "Frame_Edge_Length"},
        {"type": "distance_x", "a": "origin", "b": "g3.start", "value": "Fan_W / 2 + Fit + Wall", "name": "Frame_X"},
        {"type": "distance_x", "a": "g3.start", "b": "g1.center", "value": "Wall + Head_D / 2", "name": "Hole_To_Frame"},
    )  # fmt: skip
    assert report["dof"] == 0, report
    return sketch


def lugs(doc: Any, source: Any) -> Any:
    """Two D-shaped lugs whose arcs are centred on the layout holes (x0, x1)."""
    x, y = mount_point(PARAMS)
    r, root = PARAMS["Lug_D"] / 2, PARAMS["Fan_W"] / 2 + PARAMS["Fit"] + PARAMS["Wall"] / 2
    sketch = sketch_on(doc, purpose="Lugs")
    assert geometry(
        doc,
        sketch,
        {"type": "external", "source": source.Label, "element": "g1"},
        {"type": "external", "source": source.Label, "element": "g2"},
    ) == ["x0", "x1"]
    items: list[dict[str, Any]] = []
    for sign, (start, end) in ((1, (-90, 90)), (-1, (90, 270))):
        cx, cy = sign * x, sign * y
        items += [
            {"type": "arc", "center": [cx, cy], "radius": r, "start_angle": start, "end_angle": end},
            {"type": "line", "start": [cx, cy + sign * r], "end": [sign * root, cy + sign * r]},
            {"type": "line", "start": [sign * root, cy + sign * r], "end": [sign * root, cy - sign * r]},
            {"type": "line", "start": [sign * root, cy - sign * r], "end": [cx, cy - sign * r]},
        ]
    geometry(doc, sketch, *items)
    rules: list[dict[str, Any]] = []
    for base, ext, sign in ((0, "x0", 1), (4, "x1", -1)):
        arc, top, side, bottom = (f"g{base + i}" for i in range(4))
        rules += [
            {"type": "coincident", "a": f"{arc}.end", "b": f"{top}.start"},
            {"type": "coincident", "a": f"{top}.end", "b": f"{side}.start"},
            {"type": "coincident", "a": f"{side}.end", "b": f"{bottom}.start"},
            {"type": "coincident", "a": f"{bottom}.end", "b": f"{arc}.start"},
            {"type": "horizontal", "a": top},
            {"type": "horizontal", "a": bottom},
            {"type": "vertical", "a": side},
            {"type": "vertical", "a": f"{arc}.center", "b": f"{arc}.end"},
            {"type": "vertical", "a": f"{arc}.center", "b": f"{arc}.start"},
            {"type": "radius", "a": arc, "value": "Lug_D / 2", "name": f"Lug_R{base}"},
            {"type": "coincident", "a": f"{arc}.center", "b": f"{ext}.center"},
            {
                "type": "distance_x",
                **(
                    {"a": "origin", "b": f"{side}.start"}
                    if sign > 0
                    else {"a": f"{side}.start", "b": "origin"}
                ),
                "value": "Fan_W / 2 + Fit + Wall / 2",
                "name": f"Lug_Root{base}",
            },
        ]
    assert constraints(doc, sketch, *rules)["dof"] == 0
    return sketch


def build(doc: Any, part: Any) -> Any:
    set_params(doc, **PARAMS)
    source = layout(doc)
    frame = sketch_on(doc, purpose="Frame")
    profile(doc, frame, "rounded_rectangle", width=FRAME, height=FRAME, radius=3)
    features.pad(frame.Name, length=TOP, purpose="Frame", document=doc.Name)
    features.pad(lugs(doc, source).Name, length=TOP, purpose="Lugs", document=doc.Name)
    cavity = sketch_on(doc, purpose="FanPocket", offset=TOP)
    profile(doc, cavity, "rectangle", width="Fan_W + 2 * Fit", height="Fan_W + 2 * Fit")
    features.pocket(cavity.Name, depth="Fan_H", purpose="FanPocket", document=doc.Name)
    rim = sketch_on(doc, purpose="RimOpening", offset=TOP)
    profile(doc, rim, "rectangle", width="Fan_W + 2 * Fit - 2 * Rim_W", height="Fan_W + 2 * Fit - 2 * Rim_W")
    features.pocket(rim.Name, mode="through_all", purpose="RimOpening", document=doc.Name)
    heads = sketch_on(doc, purpose="ScrewHeads", offset=TOP)
    geometry(
        doc,
        heads,
        {"type": "external", "source": source.Label, "element": "g1"},
        {"type": "external", "source": source.Label, "element": "g2"},
        {"type": "circle", "center": [30, 10], "radius": 3},
        {"type": "circle", "center": [-30, -10], "radius": 3},
    )
    constraints(
        doc,
        heads,
        {"type": "coincident", "a": "g0.center", "b": "x0.center"},
        {"type": "coincident", "a": "g1.center", "b": "x1.center"},
        {"type": "diameter", "a": "g0", "value": "Head_D", "name": "Head_D"},
        {"type": "equal", "a": "g0", "b": "g1"},
    )
    features.pocket(heads.Name, depth="Fan_H + Rim_T - Lug_Floor", purpose="ScrewHeads", document=doc.Name)
    features.hole(source.Name, diameter="Mount_Hole_D", purpose="MountScrews", document=doc.Name)
    doc.recompute()
    return part


def hole_centers(part: Any) -> list[Any]:
    """Centres of the mounting holes at the top face (unique by x/y)."""
    centers: dict[tuple[float, float], Any] = {}
    for edge in part.Shape.Edges:
        curve = edge.Curve
        if type(curve).__name__ == "Circle" and abs(curve.Radius - 1.7) < 1e-6:
            centers[(round(curve.Location.x, 6), round(curve.Location.y, 6))] = curve.Location
    return sorted(centers.values(), key=lambda v: v.x)


def head_centers(doc: Any) -> list[Any]:
    sketch = doc.getObjectsByLabel("Sketch_ScrewHeads")[0]
    return sorted((g.Location for g in sketch.Geometry[:2]), key=lambda v: v.x)


def assert_consistent(doc: Any, part: Any, values: dict[str, float]) -> None:
    assert all(obj.isValid() for obj in part.Group), [o.Label for o in part.Group if not o.isValid()]
    assert len(part.Shape.Solids) == 1
    holes = hole_centers(part)
    assert len(holes) == 2
    x, y = mount_point(values)
    assert abs(holes[0].distanceToPoint(holes[1]) - values["Mount_Diag"]) < 1e-6  # measured, not assumed
    assert abs(holes[1].x - x) < 1e-6 and abs(holes[1].y - y) < 1e-6
    for head, hole in zip(head_centers(doc), holes, strict=True):  # pockets follow the same source
        assert abs(head.x - hole.x) < 1e-6 and abs(head.y - hole.y) < 1e-6


def test_hole_pattern_has_exactly_one_source(doc: Any, part: Any) -> None:
    build(doc, part)

    assert_consistent(doc, part, PARAMS)
    bound = [
        (obj.Label, path)
        for obj in doc.Objects
        if obj.TypeId == "Sketcher::SketchObject"
        for path, expression in obj.ExpressionEngine
        if "Mount_Diag" in expression
    ]
    assert [label for label, _ in bound] == ["Sketch_Layout"]


def test_changing_mount_distance_or_wall_moves_everything(doc: Any, part: Any) -> None:
    build(doc, part)

    set_params(doc, Mount_Diag=76)
    doc.recompute()
    assert_consistent(doc, part, {**PARAMS, "Mount_Diag": 76})

    set_params(doc, Wall=2.5)
    doc.recompute()
    assert_consistent(doc, part, {**PARAMS, "Mount_Diag": 76, "Wall": 2.5})
