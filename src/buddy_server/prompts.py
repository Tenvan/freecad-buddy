"""Server instructions and MCP prompts that steer the agent towards human-style models."""

from __future__ import annotations

from mcp.server import MCPServer

INSTRUCTIONS = """\
FreeCAD Buddy baut 3D-Druck-Bauteile in FreeCAD PartDesign so, wie ein erfahrener Mensch es tun würde.
Der Nutzer arbeitet parallel in FreeCAD – Modellbaum vor Änderungen lesen (get_model_tree).

Regeln:
1. Zentrale Maße zuerst als Parameter (set_parameters, englische ASCII-Namen wie Box_Width) und in
   Skizzen/Features per Name referenzieren – nie Zahlen doppelt eintragen.
2. Ein Bauteil = ein Body (create_body). Skizzen auf XY/XZ/YZ oder Datum-Ebenen, nicht auf Körperflächen.
3. Profile mit add_profile zeichnen (vollständig bestimmt, symmetrisch zum Ursprung). Low-Level
   (add_geometry/add_constraints) nur als Fallback; danach muss DoF 0 sein.
4. Wiederholungen mit pattern statt Mehrfachzeichnen; Bohrungen mit hole; Kanten mit fillet/chamfer über
   semantische Selektoren (select_geometry zur Vorschau).
5. Nach jedem Schritt Ergebnis prüfen (warnings, sketch.dof); bei Fehlern Hinweise befolgen oder undo.
6. Abschluss: check_printability, dann export_body (3mf). Beschreibende purpose-Namen vergeben.
"""

HUMAN_MODELING_GUIDE = """\
# Human Modeling Guide (FreeCAD Buddy)

- Parameter: Maße in 'Parameters' (VarSet); Skizzenmaße und Feature-Längen verweisen darauf.
- Skizzen: am Ursprung verankert, Symmetrie statt zweier Lagemaße, Equal statt doppelter Maße,
  Hilfslinien als Konstruktionsgeometrie, jedes Maß benannt. Keine Block-Constraints.
- Referenzen: Ursprungsebenen oder Datum-Ebenen; Face-Attachment nur in Ausnahmefällen.
- Features: Pad/Pocket/Revolution/Groove/Hole; Details (Fillet, Chamfer, Shell) zuletzt; Muster statt Kopien.
- Labels: <Typ>_<Zweck> (Pad_Base, Pocket_ScrewHoles) – der Mensch soll den Baum lesen können.
- 3D-Druck: Unterseite fasen statt verrunden, Überhänge < 45°, Mindestwand 2 × Düse,
  Durchgangsbohrungen mit Spiel (M3 → 3.4 mm), Passungen mit clearance_fit aus dem Druckerprofil.
"""


def register_prompts(mcp: MCPServer) -> None:
    @mcp.prompt()
    def human_modeling_guide() -> str:
        """Regeln für menschlich wirkende, parametrische PartDesign-Modelle."""
        return HUMAN_MODELING_GUIDE

    @mcp.prompt()
    def design_part(description: str) -> str:
        """Workflow-Prompt: Bauteil aus einer Beschreibung Schritt für Schritt konstruieren."""
        return (
            f"Konstruiere mit FreeCAD Buddy: {description}\n\n"
            "Vorgehen:\n"
            "1. get_status und get_model_tree lesen.\n"
            "2. Maße klären und als Parameter anlegen (set_parameters).\n"
            "3. create_body, dann Basisskizze (create_sketch + add_profile) und pad.\n"
            "4. Weitere Features (pocket, hole, pattern, revolve), danach fillet/chamfer/shell.\n"
            "5. Nach jedem Schritt warnings und DoF prüfen; bei Fehlern Hinweise befolgen oder undo.\n"
            "6. check_printability ausführen, Befunde beheben, export_body (3mf).\n"
            "7. Zusammenfassung: Parameter, Features, Druckhinweise.\n\n" + HUMAN_MODELING_GUIDE
        )
