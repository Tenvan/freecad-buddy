# Tool-Katalog — FreeCAD Buddy

> Generiert mit `uv run python tools/gen_tool_docs.py` – nicht von Hand bearbeiten.

45 Tools in 10 Gruppen nach Arbeitsphase (`execute_python` nur mit `FREECAD_BUDDY_ALLOW_PYTHON=1` bzw. `--allow-python`). Jede Tool-Beschreibung beginnt mit ihrer Kategorie, z. B. `[Sketch]`. Maße akzeptieren eine Zahl, einen Parameternamen oder einen Ausdruck über Parameter (`"Box_Width - 2*Wall"`).

| Gruppe | Kategorie | Tools |
|---|---|---|
| [Session & Dokument](tools/session.md) | `[Session]` | 3 |
| [Modell & Parameter](tools/model.md) | `[Model]` | 6 |
| [Skizze](tools/sketch.md) | `[Sketch]` | 6 |
| [Referenzen](tools/reference.md) | `[Reference]` | 3 |
| [Features](tools/feature.md) | `[Feature]` | 10 |
| [Baugruppe](tools/assembly.md) | `[Assembly]` | 5 |
| [Material & Ansicht](tools/appearance.md) | `[Appearance]` | 3 |
| [3D-Druck](tools/printing.md) | `[Print]` | 4 |
| [Regelwerk & Addons](tools/rules.md) | `[Rules & addons]` | 4 |
| [Experte](tools/expert.md) | `[Expert]` | 1 |

## Session & Dokument

| Tool | Zweck |
|---|---|
| [`get_status`](tools/session.md#get_status) | Status von FreeCAD und Bridge: Version, offene Dokumente, fehlende Objekttypen. Zuerst aufrufen. |
| [`document`](tools/session.md#document) | Document lifecycle. new: create and activate (then set_parameters → create_body → create_sketch → |
| [`undo`](tools/session.md#undo) | Letzte Änderung(en) rückgängig machen. Jeder Tool-Aufruf ist genau ein Schritt. |

## Modell & Parameter

| Tool | Zweck |
|---|---|
| [`get_model_tree`](tools/model.md#get_model_tree) | Modellbaum lesen: Bodies mit Features in Reihenfolge, Gültigkeit, DoF der Skizzen, Undo-Liste und |
| [`get_object`](tools/model.md#get_object) | Details eines Objekts: Status, Expressions, bei Skizzen die Analyse, bei Körpern Volumen und Maße. |
| [`delete_object`](tools/model.md#delete_object) | Objekt löschen (ein Undo-Schritt). |
| [`set_parameters`](tools/model.md#set_parameters) | Zentrale Parameter im VarSet 'Parameters' anlegen/ändern. Maße in Skizzen und Features können den |
| [`list_parameters`](tools/model.md#list_parameters) | Alle Parameter mit Typ, Wert und Expression-Referenz. |
| [`create_body`](tools/model.md#create_body) | PartDesign-Body für ein Bauteil anlegen (ein Body = ein druckbares Teil). |

## Skizze

| Tool | Zweck |
|---|---|
| [`create_sketch`](tools/sketch.md#create_sketch) | Skizze auf stabiler Referenz anlegen. Bevorzugt Ursprungsebenen mit offset oder datum_plane. |
| [`add_profile`](tools/sketch.md#add_profile) | Vollständig bestimmtes Profil zeichnen wie ein Mensch: symmetrisch zum Ursprung, Equal statt |
| [`add_geometry`](tools/sketch.md#add_geometry) | Add low-level geometry or external references. Returns g<N> (own) and x<N> (external) references |
| [`add_constraints`](tools/sketch.md#add_constraints) | Add constraints. Conflicting/redundant constraints are rejected (rollback). |
| [`analyze_sketch`](tools/sketch.md#analyze_sketch) | Sketch analysis: DoF, conflicts, redundancies, closed wires, external geometry (x<N> with source) |
| [`fully_constrain_sketch`](tools/sketch.md#fully_constrain_sketch) | Restliche Freiheitsgrade finden bzw. schließen (Koinzidenzen, H/V, dann benannte X/Y-Maße). Nie Block. |

## Referenzen

| Tool | Zweck |
|---|---|
| [`datum_plane`](tools/reference.md#datum_plane) | Bezugsebene als stabile Skizzenbasis (statt Skizze auf Körperfläche). |
| [`shape_binder`](tools/reference.md#shape_binder) | Bind geometry of another body into this body (SubShapeBinder, follows its source). Use it as |
| [`select_geometry`](tools/reference.md#select_geometry) | Vorschau: welche Flächen/Kanten ein Selektor trifft (mit Mittelpunkt, Normale, Länge, Radius). |

## Features

| Tool | Zweck |
|---|---|
| [`pad`](tools/feature.md#pad) | Profil aufpolstern (additiv). |
| [`pocket`](tools/feature.md#pocket) | Tasche schneiden (subtraktiv). |
| [`revolve`](tools/feature.md#revolve) | Rotationskörper (Revolution) oder Rotationsnut (Groove). |
| [`sweep`](tools/feature.md#sweep) | Querschnitt entlang eines Pfads ziehen (PartDesign AdditivePipe/SubtractivePipe): runde Griffe, |
| [`hole`](tools/feature.md#hole) | Holes (Hole feature) at every circle centre of the sketch. Cuts without cut_* use ISO defaults; |
| [`fillet`](tools/feature.md#fillet) | Kanten verrunden. Der Selektor wird gespeichert und nach Parameteränderungen neu aufgelöst. |
| [`chamfer`](tools/feature.md#chamfer) | Kanten fasen (an der Druckbett-Unterseite besser als Verrundung – gegen Elefantenfuß). |
| [`shell`](tools/feature.md#shell) | Körper aushöhlen (Thickness) mit Wandstärke; gewählte Flächen werden zur Öffnung. |
| [`pattern`](tools/feature.md#pattern) | Features spiegeln oder linear/polar/als Raster vervielfältigen (statt Geometrie mehrfach zu zeichnen). |
| [`thread`](tools/feature.md#thread) | Cut a real external metric thread (ISO 60° profile, native SubtractiveHelix) into an existing |

## Baugruppe

| Tool | Zweck |
|---|---|
| [`create_assembly`](tools/assembly.md#create_assembly) | Create an Assembly4 assembly in the document (bodies move into a 'Parts' group). Then |
| [`add_to_assembly`](tools/assembly.md#add_to_assembly) | Insert a body into the assembly as App::Link placed by Assembly4 (LCS_Origin * AttachmentOffset). |
| [`add_fastener`](tools/assembly.md#add_fastener) | Standard parts from the Fasteners workbench (needs the addon), placed in the assembly if there |
| [`explode_assembly`](tools/assembly.md#explode_assembly) | Exploded view as Assembly4 configuration: saves 'Assembled' once, moves the listed parts and |
| [`apply_configuration`](tools/assembly.md#apply_configuration) | Apply a saved Assembly4 configuration (positions of all assembly parts). |

## Material & Ansicht

| Tool | Zweck |
|---|---|
| [`set_material`](tools/appearance.md#set_material) | Assign a FreeCAD library material (density -> mass) and/or the display colour of a body. |
| [`set_view`](tools/appearance.md#set_view) | Live-Ansicht in FreeCAD setzen (bleibt so stehen): Standard iso + alles einpassen. Als letzten |
| [`screenshot`](tools/appearance.md#screenshot) | Bild der 3D-Ansicht zur visuellen Kontrolle (nur mit laufender FreeCAD-GUI). |

## 3D-Druck

| Tool | Zweck |
|---|---|
| [`get_printer_profile`](tools/printing.md#get_printer_profile) | Aktives Druckerprofil (Bauraum, Düse, Mindestwand, Überhangwinkel, Passungsspiel). |
| [`set_printer_profile`](tools/printing.md#set_printer_profile) | Druckerprofil ändern (dauerhaft gespeichert). |
| [`check_printability`](tools/printing.md#check_printability) | Druckbarkeit prüfen: gültiger Solid, Bauraum, Überhänge, Wandstärke, zu kleine Details. |
| [`export_body`](tools/printing.md#export_body) | Bauteil exportieren (auf das Druckbett gelegt) und die Datei per Reimport prüfen. |

## Regelwerk & Addons

| Tool | Zweck |
|---|---|
| [`get_design_rules`](tools/rules.md#get_design_rules) | Design-Regelwerk für FreeCAD-Konstruktion und FDM-Druck (Werte aus dem aktiven Druckerprofil). |
| [`search_addons`](tools/rules.md#search_addons) | Offiziellen FreeCAD-Addon-Katalog durchsuchen (Workbenches, Makros, Preference Packs): Treffer mit |
| [`get_addon`](tools/rules.md#get_addon) | Details eines Addons oder Makros: Lizenz, Maintainer, Repository, letzte Aktualisierung, |
| [`install_addon`](tools/rules.md#install_addon) | Install an addon or macro through FreeCAD's Addon Manager (needs FreeCAD's opt-in). FreeCAD shows the user |

## Experte

| Tool | Zweck |
|---|---|
| [`execute_python`](tools/expert.md#execute_python) | Notausgang (nur mit FREECAD_BUDDY_ALLOW_PYTHON=1): Python in FreeCAD als ein Undo-Schritt. |
