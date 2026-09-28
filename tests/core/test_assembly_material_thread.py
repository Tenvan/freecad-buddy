from typing import Any

import pytest

from buddy_core import appearance, assembly, body, features, thread
from buddy_core.errors import NOT_FOUND, VALIDATION, CoreError

from .conftest import profile, set_params, sketch_on


def _box(doc: Any, label: str, z: float = 0, size: float = 40) -> Any:
    body.create_body(label, document=doc.Name)
    sketch = sketch_on(doc, purpose=label, body=label, offset=z)
    profile(doc, sketch, "rectangle", width=size, height=size)
    features.pad(sketch.Label, length=5, purpose=label, document=doc.Name)
    return doc.getObjectsByLabel(label)[0]


def _pin(doc: Any, part: Any) -> Any:
    set_params(doc, Pin_X=20, Pin_Diameter=10)
    sketch = sketch_on(doc, purpose="Pin")
    profile(doc, sketch, "circle", diameter="Pin_Diameter", center=["Pin_X", 10])
    features.pad(sketch.Label, length=20, purpose="Pin", document=doc.Name)
    return part.Tip


# --- material & appearance -----------------------------------------------------------------------
def test_material_by_short_name_gives_density_and_mass(doc: Any) -> None:
    box = _box(doc, "Box")

    result = appearance.set_material("Box", material="PLA", document=doc.Name).to_dict()

    assert result["material"]["name"] == "PLA-Generic"
    assert result["material"]["density_g_cm3"] == pytest.approx(1.24, rel=1e-3)
    assert result["material"]["mass_g"] == pytest.approx(40 * 40 * 5 / 1000 * 1.24, rel=1e-3)
    assert box.ShapeMaterial.Name == "PLA-Generic"


def test_unknown_material_lists_candidates(doc: Any) -> None:
    _box(doc, "Box")

    with pytest.raises(CoreError) as info:
        appearance.set_material("Box", material="Unobtainium", document=doc.Name)

    assert info.value.name == NOT_FOUND


def test_colours_parse_names_hex_and_rgb() -> None:
    assert appearance.parse_color("red") == appearance.COLORS["red"]
    assert appearance.parse_color("#FF0000") == (1.0, 0.0, 0.0)
    assert appearance.parse_color([255, 128, 0]) == pytest.approx((1.0, 128 / 255, 0.0))
    with pytest.raises(CoreError):
        appearance.parse_color("sparkly")


# --- thread ---------------------------------------------------------------------------------------
def test_thread_cuts_a_fully_constrained_parametric_helix(doc: Any, part: Any) -> None:
    pin = _pin(doc, part)
    before = pin.Shape.Volume

    result = thread.thread(["Pin_X", 10], "Pin_Diameter", 1.5, 15, z_start=5, document=doc.Name).to_dict()

    helix = doc.getObject(result["feature"]["name"])
    assert helix.isValid() and part.Tip == helix
    assert 0 < before - helix.Shape.Volume < before * 0.2
    assert result["thread"]["core_diameter"] == pytest.approx(10 - 2 * 0.6134 * 1.5, abs=1e-3)
    removed = before - helix.Shape.Volume

    set_params(doc, Pin_X=25)  # the thread follows the pin
    doc.recompute()
    assert helix.isValid()
    assert before - helix.Shape.Volume == pytest.approx(removed, rel=1e-3)


def test_thread_rejects_a_pitch_larger_than_the_radius(doc: Any, part: Any) -> None:
    _pin(doc, part)

    with pytest.raises(CoreError) as info:
        thread.thread([20, 10], 10, 6, 15, document=doc.Name)

    assert info.value.name == VALIDATION


# --- assembly ------------------------------------------------------------------------------------
def _assembled(doc: Any) -> Any:
    _box(doc, "Box")
    _box(doc, "Lid", z=5)
    assembly.create_assembly(document=doc.Name)
    assembly.add_to_assembly("Box", document=doc.Name)
    assembly.add_to_assembly("Lid", label="Lid_Link", document=doc.Name)
    return doc.getObject(assembly.ASSEMBLY)


def test_assembly_follows_the_assembly4_convention(doc: Any) -> None:
    assy = _assembled(doc)

    assert assy.Type == "Assembly" and assy.AssemblyType == "Part::Link"
    assert doc.getObject(assembly.ORIGIN_LCS) is not None
    link = doc.getObjectsByLabel("Lid_Link")[0]
    assert link.LinkedObject.Label == "Lid" and link.SolverId == "Asm4EE"
    assert doc.getObjectsByLabel("Link_Box")[0].LinkedObject.Label == "Box"  # default link label
    assert ("Placement", assembly.PLACEMENT_EXPRESSION) in link.ExpressionEngine
    assert [o.Label for o in doc.getObject("Parts").Group] == ["Box", "Lid"]


def test_second_assembly_is_refused(doc: Any) -> None:
    _assembled(doc)

    with pytest.raises(CoreError):
        assembly.create_assembly(document=doc.Name)


def test_exploded_configuration_and_back(doc: Any) -> None:
    _assembled(doc)
    link = doc.getObjectsByLabel("Lid_Link")[0]

    result = assembly.explode_assembly({"Lid_Link": [0, 0, 60]}, document=doc.Name).to_dict()
    assert link.Placement.Base.z == pytest.approx(60)
    assert set(result["configurations"]) == {"Assembled", "Exploded"}

    assembly.explode_assembly({"Lid": [0, 0, 80]}, document=doc.Name)  # body -> its link, idempotent base
    assert link.Placement.Base.z == pytest.approx(80)

    assembly.apply_configuration("Assembled", document=doc.Name)
    assert link.Placement.Base.z == pytest.approx(0)
    sheet = doc.getObject("Exploded")
    assert sheet.get(assembly.HEADER_CELL) == assembly.CONFIG_TYPE


def test_unknown_configuration_lists_the_saved_ones(doc: Any) -> None:
    _assembled(doc)
    assembly.explode_assembly({"Lid_Link": [0, 0, 60]}, document=doc.Name)

    with pytest.raises(CoreError) as info:
        assembly.apply_configuration("Nope", document=doc.Name)

    assert info.value.name == NOT_FOUND


def test_fasteners_are_placed_in_the_assembly(doc: Any) -> None:
    pytest.importorskip("FastenersCmd")
    _assembled(doc)

    result = assembly.add_fastener("ISO4032", "M10", [[10, 10, 5], [-10, 10, 5]], document=doc.Name).to_dict()

    nuts = [doc.getObject(f["name"]) for f in result["fasteners"]]
    assert len(nuts) == 2 and all(n.Shape.isValid() and n.Shape.Volume > 0 for n in nuts)
    assert nuts[0].Placement.Base.z == pytest.approx(5)
    assert nuts[0].SolverId == "Asm4EE"


def test_unknown_fastener_diameter_is_rejected(doc: Any) -> None:
    pytest.importorskip("FastenersCmd")
    _assembled(doc)

    with pytest.raises(CoreError) as info:
        assembly.add_fastener("ISO4032", "M7.5", [[0, 0, 0]], document=doc.Name)

    assert info.value.name == VALIDATION


def test_get_object_reports_material_link_and_fastener(doc: Any) -> None:
    from buddy_core import documents

    _assembled(doc)
    appearance.set_material("Box", material="PLA", document=doc.Name)

    assert documents.get_object("Box", doc.Name)["material"] == "PLA-Generic"
    link = documents.get_object("Lid_Link", doc.Name)
    assert link["linked_object"]["label"] == "Lid" and link["attachment"]["solver"] == "Asm4EE"
    assert {c["label"] for c in documents.get_object("Assembly", doc.Name)["group"]} >= {
        "Link_Box",
        "Lid_Link",
    }
