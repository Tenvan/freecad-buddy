# Tool-Katalog — FreeCAD Buddy

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten.

57 Tools in 11 Gruppen nach Arbeitsphase (`execute_python` nur mit `FREECAD_BUDDY_ALLOW_PYTHON=1` bzw. `--allow-python`). Jede Tool-Beschreibung beginnt mit ihrer Kategorie, z. B. `[Sketch]`. Maße akzeptieren eine Zahl, einen Parameternamen oder einen Ausdruck über Parameter (`"Box_Width - 2*Wall"`).

| Gruppe | Kategorie | Tools |
|---|---|---|
| [Session & Dokument](tools/session.md) | `[Session]` | 3 |
| [Modell & Parameter](tools/model.md) | `[Model]` | 6 |
| [Skizze](tools/sketch.md) | `[Sketch]` | 6 |
| [Referenzen](tools/reference.md) | `[Reference]` | 4 |
| [Features](tools/feature.md) | `[Feature]` | 16 |
| [Design-Tools](tools/design.md) | `[Design tools]` | 3 |
| [Baugruppe](tools/assembly.md) | `[Assembly]` | 7 |
| [Material & Ansicht](tools/appearance.md) | `[Appearance]` | 3 |
| [3D-Druck](tools/printing.md) | `[Print]` | 4 |
| [Regelwerk & Addons](tools/rules.md) | `[Rules & addons]` | 4 |
| [Experte](tools/expert.md) | `[Expert]` | 1 |

## Session & Dokument

| Tool | Zweck |
|---|---|
| [`get_status`](tools/session.md#get_status) | Status of FreeCAD and the bridge: version, open documents, missing object types. Call first. |
| [`document`](tools/session.md#document) | Document lifecycle. new: create and activate (then set_parameters → create_body → create_sketch → |
| [`undo`](tools/session.md#undo) | Undo the last change(s). Every tool call is exactly one step. |

## Modell & Parameter

| Tool | Zweck |
|---|---|
| [`get_model_tree`](tools/model.md#get_model_tree) | Read the model tree: bodies with features in order, validity, sketch DoF, undo list and label |
| [`get_object`](tools/model.md#get_object) | Details of an object: status, expressions, the analysis for sketches, volume and size for solids. |
| [`delete_object`](tools/model.md#delete_object) | Delete an object (one undo step). |
| [`set_parameters`](tools/model.md#set_parameters) | Create/change central parameters in the VarSet 'Parameters'. Dimensions in sketches and features can use |
| [`list_parameters`](tools/model.md#list_parameters) | All parameters with type, value and expression reference. |
| [`create_body`](tools/model.md#create_body) | Create a PartDesign body for a part (one body = one printable part). |

## Skizze

| Tool | Zweck |
|---|---|
| [`create_sketch`](tools/sketch.md#create_sketch) | Create a sketch on a stable reference. Prefer origin planes with offset or a datum_plane. |
| [`add_profile`](tools/sketch.md#add_profile) | Draw a fully constrained profile like a person would: symmetric to the origin, Equal instead of |
| [`add_geometry`](tools/sketch.md#add_geometry) | Add low-level geometry or external references. Returns g<N> (own) and x<N> (external) references |
| [`add_constraints`](tools/sketch.md#add_constraints) | Add constraints. Conflicting/redundant constraints are rejected (rollback). |
| [`analyze_sketch`](tools/sketch.md#analyze_sketch) | Sketch analysis: DoF, conflicts, redundancies, closed wires, external geometry (x<N> with source) |
| [`fully_constrain_sketch`](tools/sketch.md#fully_constrain_sketch) | Find or close remaining degrees of freedom (coincidences, H/V, then named X/Y dimensions). Never Block. |

## Referenzen

| Tool | Zweck |
|---|---|
| [`datum_plane`](tools/reference.md#datum_plane) | Datum plane as a stable sketch base (instead of a sketch on a solid face). |
| [`datum`](tools/reference.md#datum) | Datum point, datum line or local coordinate system (LCS) as a stable parametric reference. |
| [`shape_binder`](tools/reference.md#shape_binder) | Bind geometry of another body into this body (SubShapeBinder, follows its source). Use it as |
| [`select_geometry`](tools/reference.md#select_geometry) | Preview which faces/edges a selector hits (with centre, normal, length, radius). |

## Features

| Tool | Zweck |
|---|---|
| [`pad`](tools/feature.md#pad) | Extrude a profile (additive). up_to_first stops at the next face of the solid. |
| [`pocket`](tools/feature.md#pocket) | Cut a pocket (subtractive). up_to_first stops at the next face of the solid. |
| [`revolve`](tools/feature.md#revolve) | Solid of revolution (Revolution) or rotational groove (Groove). |
| [`sweep`](tools/feature.md#sweep) | Sweep a cross-section along a path (PartDesign AdditivePipe/SubtractivePipe): round handles, |
| [`loft`](tools/feature.md#loft) | Loft through two or more sketches (PartDesign AdditiveLoft/SubtractiveLoft): funnels, |
| [`helix`](tools/feature.md#helix) | Sweep a profile along a helix (PartDesign AdditiveHelix/SubtractiveHelix): springs, cable |
| [`primitive`](tools/feature.md#primitive) | Additive or subtractive primitive (PartDesign Additive*/Subtractive*) placed on an origin or |
| [`hole`](tools/feature.md#hole) | Holes (Hole feature) at every circle centre of the sketch. Cuts without cut_* use ISO defaults; |
| [`fillet`](tools/feature.md#fillet) | Round edges. The selector is stored and resolved again after parameter changes. |
| [`chamfer`](tools/feature.md#chamfer) | Chamfer edges (on the bed side better than a fillet - against elephant foot). |
| [`shell`](tools/feature.md#shell) | Hollow the solid (Thickness) with a wall thickness; the selected faces become the openings. |
| [`draft`](tools/feature.md#draft) | Tilt faces (PartDesign Draft): side walls for demoulding, a slight taper so parts stack or |
| [`pattern`](tools/feature.md#pattern) | Mirror features or repeat them linearly/polar/as a raster (instead of drawing geometry several times). |
| [`boolean`](tools/feature.md#boolean) | Fuse, cut or intersect other bodies into this body (PartDesign Boolean). The tool bodies |
| [`thread`](tools/feature.md#thread) | Cut a real external metric thread (ISO 60° profile, native SubtractiveHelix) into an existing |
| [`add_gear`](tools/feature.md#add_gear) | Parametric gear from the freecad.gears workbench (needs the addon) as feature of a body; one gear per |

## Design-Tools

| Tool | Zweck |
|---|---|
| [`fill_pattern`](tools/design.md#fill_pattern) | Fill a rectangular field with cut cells in one call and one undo step: round holes (sieve, perforation, |
| [`propose_design_tool`](tools/design.md#propose_design_tool) | Propose a missing design tool (task recurs or needs >= 5 tool calls, no design tool or addon fits). |
| [`list_design_tool_proposals`](tools/design.md#list_design_tool_proposals) | All design tool proposals, most requested first (name, count, problems, inputs, steps, examples). |

## Baugruppe

| Tool | Zweck |
|---|---|
| [`create_assembly`](tools/assembly.md#create_assembly) | Create an Assembly4 assembly in the document (bodies move into a 'Parts' group). Then |
| [`add_to_assembly`](tools/assembly.md#add_to_assembly) | Insert a body into the assembly as App::Link placed by Assembly4 (LCS_Origin * AttachmentOffset). |
| [`add_fastener`](tools/assembly.md#add_fastener) | Standard parts from the Fasteners workbench (needs the addon), placed in the assembly if there |
| [`search_parts`](tools/assembly.md#search_parts) | Search the step.parts catalogue of open STEP models (boards, fans, motors, bearings, profiles, |
| [`insert_part`](tools/assembly.md#insert_part) | Download a step.parts STEP model (cached) and insert it as a plain solid, in the assembly if |
| [`explode_assembly`](tools/assembly.md#explode_assembly) | Exploded view as Assembly4 configuration: saves 'Assembled' once, moves the listed parts and |
| [`apply_configuration`](tools/assembly.md#apply_configuration) | Apply a saved Assembly4 configuration (positions of all assembly parts). |

## Material & Ansicht

| Tool | Zweck |
|---|---|
| [`set_material`](tools/appearance.md#set_material) | Assign a FreeCAD library material (density -> mass) and/or the display colour of a body. |
| [`set_view`](tools/appearance.md#set_view) | Set the live view in FreeCAD (it stays that way): default iso + fit everything. Call as the last |
| [`screenshot`](tools/appearance.md#screenshot) | Image of the 3D view for a visual check (only with a running FreeCAD GUI). |

## 3D-Druck

| Tool | Zweck |
|---|---|
| [`get_printer_profile`](tools/printing.md#get_printer_profile) | Active printer profile (build volume, nozzle, minimum wall, overhang angle, fit clearance). |
| [`set_printer_profile`](tools/printing.md#set_printer_profile) | Change the printer profile (stored permanently). |
| [`check_printability`](tools/printing.md#check_printability) | Check printability: valid solid, build volume, overhangs, wall thickness, too small details. |
| [`export_body`](tools/printing.md#export_body) | Export the part (placed on the print bed) and verify the file by re-importing it. With OrcaSlicer |

## Regelwerk & Addons

| Tool | Zweck |
|---|---|
| [`get_design_rules`](tools/rules.md#get_design_rules) | Design rulebook for FreeCAD modelling and FDM printing (values from the active printer profile). |
| [`search_addons`](tools/rules.md#search_addons) | Search the official FreeCAD addon catalogue (workbenches, macros, preference packs): hits with |
| [`get_addon`](tools/rules.md#get_addon) | Details of an addon or macro: licence, maintainer, repository, last update, |
| [`install_addon`](tools/rules.md#install_addon) | Install an addon or macro through FreeCAD's Addon Manager (needs FreeCAD's opt-in). FreeCAD shows the user |

## Experte

| Tool | Zweck |
|---|---|
| [`execute_python`](tools/expert.md#execute_python) | Escape hatch (only with FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD as one undo step. |
