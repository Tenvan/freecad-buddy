"""The FreeCAD Buddy design rulebook: single source for instructions, tool, resources and prompts.

Rules are grouped into topics. A rule may name tools it relies on (``requires``); it is only
rendered when all of them are registered, so opt-in or not-yet-built tools never leak into the
agent's guidance. Printing numbers are templates filled from the active printer profile.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

INSTRUCTIONS_BUDGET = 2000
"""Upper bound for the server instructions (characters). Clients may truncate longer texts."""

DEFAULT_PROFILE: dict[str, Any] = {
    "build_x": 256.0,
    "build_y": 256.0,
    "build_z": 256.0,
    "nozzle": 0.4,
    "layer_height": 0.2,
    "min_wall": 0.8,
    "overhang_angle": 45.0,
    "clearance_fit": 0.2,
    "press_fit": 0.05,
    "material": "PLA",
}
"""Mirror of ``buddy_core.printing.profile.PrinterProfile`` defaults, used when the bridge is offline."""


@dataclass(frozen=True)
class Rule:
    text: str
    requires: tuple[str, ...] = ()
    core: bool = False
    """Core rules are repeated in the compact server instructions."""


@dataclass(frozen=True)
class Topic:
    key: str
    title: str
    summary: str
    rules: tuple[Rule, ...]
    requires: tuple[str, ...] = ()


TOPICS: tuple[Topic, ...] = (
    Topic(
        "workflow",
        "Arbeitsablauf",
        "Reihenfolge der Schritte, Prüfen nach jedem Schritt",
        (
            Rule("Vor Änderungen get_model_tree lesen – der Nutzer arbeitet parallel in FreeCAD.", core=True),
            Rule(
                "Ansicht als erster und letzter Schritt: set_view (iso, fit) – das Bauteil ist komplett sichtbar "
                "und leicht isometrisch. Ohne offenes Dokument direkt nach new_document/open_document.",
                requires=("set_view",),
                core=True,
            ),
            Rule(
                "Reihenfolge: Maße als Parameter → create_body → Basisskizze → Basis-Feature → "
                "Detail-Features → Kanten (fillet/chamfer) → check_printability → export_body."
            ),
            Rule(
                "Nach jedem Schritt warnings, sketch.dof und valid prüfen; bei Fehlern den Hinweisen folgen "
                "oder undo – nie auf einem fehlerhaften Stand weiterbauen.",
                core=True,
            ),
            Rule(
                "Ein Tool-Aufruf ist ein Undo-Schritt: wenige sinnvolle Schritte statt vieler Kleinstschritte."
            ),
            Rule("Unklare Maße oder Funktionsanforderungen erst mit dem Nutzer klären, nicht raten."),
        ),
    ),
    Topic(
        "parameters",
        "Parameter",
        "Maße zentral im VarSet, Namen, Ausdrücke",
        (
            Rule(
                "Jedes Maß, das ein Mensch ändern würde, zuerst als Parameter anlegen (set_parameters) und per "
                "Name oder Ausdruck referenzieren (z. B. 'Box_Width - 2*Wall') – nie Zahlen doppelt eintragen.",
                core=True,
            ),
            Rule(
                "Namen englisch, ASCII, <Bauteil>_<Größe> (Box_Width, Lid_Clearance); Einheiten oder Konstanten "
                "als Name (mm, deg, pi) werden abgelehnt."
            ),
            Rule("Abgeleitete Maße als Ausdruck statt als eigene Zahl; Anzahlen als integer-Parameter."),
            Rule(
                "Druckspiel als eigenen Parameter führen (z. B. Fit_Clearance = {clearance_fit} mm), nicht einrechnen."
            ),
        ),
    ),
    Topic(
        "sketches",
        "Skizzen",
        "Vollständig bestimmte, symmetrische Profile",
        (
            Rule(
                "Profile mit add_profile zeichnen (vollständig bestimmt, symmetrisch zum Ursprung). "
                "add_geometry/add_constraints nur als Fallback; danach muss DoF 0 sein.",
                core=True,
            ),
            Rule(
                "Symmetrie statt zweier Lagemaße, Equal statt doppelter Maße, Hilfslinien als Konstruktionsgeometrie."
            ),
            Rule(
                "Keine Block- oder Lock-Constraints; fully_constrain_sketch schließt verbleibende Freiheitsgrade."
            ),
            Rule("Ein Zweck pro Skizze; keine überlappenden oder offenen Konturen."),
            Rule("analyze_sketch zeigt Konflikte, Redundanzen und Lint-Befunde – vor dem Feature beheben."),
        ),
    ),
    Topic(
        "references",
        "Referenzen",
        "Stabile Bezüge gegen das Topological Naming Problem",
        (
            Rule(
                "Ein Bauteil = ein Body. Skizzen auf XY/XZ/YZ oder datum_plane mit Offset-Parameter, nicht auf "
                "Körperflächen.",
                core=True,
            ),
            Rule(
                "Kanten und Flächen nur über semantische Selektoren wählen (select_geometry zur Vorschau), nie Edge12."
            ),
            Rule(
                "Nach Parameteränderungen das Ergebnis prüfen; gespeicherte Selektoren werden neu aufgelöst."
            ),
        ),
    ),
    Topic(
        "features",
        "Features",
        "Aufbau des Körpers, Muster, Details",
        (
            Rule("Additiv aufbauen (pad, revolve), subtraktiv detaillieren (pocket); Bohrungen mit hole."),
            Rule(
                "Wiederholungen mit pattern statt Mehrfachzeichnen; 2D-Raster mit kind='grid' – "
                "Muster auf Muster ist in PartDesign nicht möglich.",
                core=True,
            ),
            Rule(
                "Details (fillet, chamfer, shell) zuletzt, damit Änderungen an der Basis sie nicht zerstören."
            ),
            Rule("Gehäuse mit shell aus einem Vollkörper statt aus mehreren Pads."),
        ),
    ),
    Topic(
        "naming",
        "Benennung",
        "Lesbarer Modellbaum",
        (
            Rule(
                "Beschreibende purpose-Namen vergeben: Labels <Typ>_<Zweck> (Pad_Base, Pocket_ScrewHoles).",
                core=True,
            ),
            Rule(
                "Skizze, Feature und Parameter desselben Zwecks gleich benennen (Sketch_Lid → Pad_Lid, Lid_Height)."
            ),
        ),
    ),
    Topic(
        "printing",
        "3D-Druck (FDM)",
        "Wände, Überhänge, Bohrungen, Passungen – Werte aus dem Druckerprofil",
        (
            Rule(
                "Profil: {material}, Düse {nozzle} mm, Layer {layer_height} mm, Bauraum "
                "{build_x} × {build_y} × {build_z} mm (get_printer_profile)."
            ),
            Rule(
                "Wände ≥ {min_wall} mm, tragende Wände ≥ {strong_wall} mm; Details und Stege ≥ {nozzle} mm."
            ),
            Rule(
                "Überhänge ≤ {overhang_angle}° gegen die Senkrechte; steilere Unterseiten fasen statt verrunden "
                "oder Stützen einplanen. Brücken ohne Stütze ≤ 10 mm."
            ),
            Rule(
                "Bettseitige Kanten fasen ({bottom_chamfer} mm) statt verrunden – gegen Elefantenfuß und Überhang."
            ),
            Rule(
                "Durchgangsbohrungen mit Spiel: Nennmaß + 2 × {clearance_fit} mm (M3 → {m3_clearance} mm); "
                "Presspassung + {press_fit} mm. Bewegliche Teile: {clearance_fit} mm Spalt je Seite."
            ),
            Rule(
                "Horizontale Bohrungen über 8 mm oben als Tropfen oder mit Fase; senkrechte Bohrungen bevorzugen."
            ),
            Rule("Höhen möglichst als Vielfaches der Layerhöhe ({layer_height} mm)."),
            Rule("Größte ebene Fläche aufs Bett; Zuglast quer zu den Schichten vermeiden."),
            Rule(
                "Gewinde unter M6 nicht drucken: Gewindeeinsatz, Mutterfalle oder selbstschneidende Schraube vorsehen."
            ),
            Rule("Abschluss: check_printability, Befunde beheben, dann export_body (3mf).", core=True),
        ),
    ),
    Topic(
        "design_tools",
        "Design-Tools",
        "Wiederkehrende komplexe Aufgaben als Design-Tool statt Ad-hoc-Nachbau",
        (
            Rule(
                "Wiederkehrend-komplex ist eine Aufgabe, die im Projekt zum zweiten Mal vorkommt oder ≥ 5 "
                "Tool-Aufrufe braucht (z. B. Lochraster, Schraubendom, Schnapphaken). Solche Aufgaben nicht "
                "wiederholt aus Einzelschritten nachbauen: erst ein Design-Tool nutzen, dann ein fertiges Addon "
                "prüfen, sonst ein neues Design-Tool vorschlagen.",
                core=True,
            ),
            Rule("Design-Tools zuerst: hole_grid für Sieb- und Lochraster.", requires=("hole_grid",)),
            Rule("Fertige Lösungen im Addon-Katalog suchen: search_addons.", requires=("search_addons",)),
            Rule(
                "Fehlt ein Design-Tool: propose_design_tool mit Problem, Eingaben, Schritten und Beispiel "
                "aufrufen – auch wenn die Aufgabe diesmal aus Einzelschritten gelöst wird.",
                requires=("propose_design_tool",),
            ),
            Rule("Wiederkehrende Aufgaben nie per execute_python umgehen.", requires=("execute_python",)),
        ),
    ),
    Topic(
        "addons",
        "Addons",
        "Wann ein fertiges Addon, wann ein eigenes Design-Tool",
        (
            Rule(
                "Addon-Features machen das Modell abhängig: wer die Datei öffnet, braucht das Addon. "
                "Eigene Design-Tools bevorzugen, wenn beide passen."
            ),
            Rule("PartDesign-kompatible Lösungen bevorzugen; Part-Objekte im Body brechen den Workflow."),
            Rule(
                "get_addon zeigt Lizenz, Pflege und Abhängigkeiten – vor jeder Empfehlung prüfen.",
                requires=("get_addon",),
            ),
            Rule(
                "Installation nur nach Rückfrage beim Nutzer; install_addon öffnet einen Bestätigungsdialog "
                "in FreeCAD, danach ist ein FreeCAD-Neustart nötig.",
                requires=("install_addon",),
            ),
        ),
        requires=("search_addons",),
    ),
)

TOPIC_KEYS: tuple[str, ...] = tuple(topic.key for topic in TOPICS)


def profile_values(profile: Mapping[str, Any] | None) -> dict[str, str]:
    """Template values: the printer profile plus derived numbers, formatted for humans."""
    merged = {**DEFAULT_PROFILE, **(profile or {})}
    nozzle = float(merged["nozzle"])
    layer = float(merged["layer_height"])
    derived = {
        "strong_wall": 4 * nozzle,
        "bottom_chamfer": max(0.4, 2 * layer),
        "m3_clearance": 3 + 2 * float(merged["clearance_fit"]),
    }
    return {key: _fmt(value) for key, value in {**merged, **derived}.items()}


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{round(value, 3):g}"
    return str(value)


def _visible(requires: Iterable[str], available: set[str] | None) -> bool:
    return available is None or set(requires) <= available


def visible_topics(available: set[str] | None = None) -> list[Topic]:
    """Topics whose tools are registered (``available=None`` means: assume every tool exists)."""
    return [topic for topic in TOPICS if _visible(topic.requires, available)]


def _rules(topic: Topic, available: set[str] | None) -> list[Rule]:
    return [rule for rule in topic.rules if _visible(rule.requires, available)]


def render_overview(available: set[str] | None = None) -> str:
    lines = ["# FreeCAD-Buddy-Designregeln", "", "Themen (get_design_rules(topic)):"]
    lines += [f"- {topic.key}: {topic.title} – {topic.summary}" for topic in visible_topics(available)]
    return "\n".join(lines)


def render_topic(
    key: str, profile: Mapping[str, Any] | None = None, available: set[str] | None = None
) -> str:
    """One topic as Markdown. Raises ``KeyError`` for unknown or hidden topics."""
    topics = {topic.key: topic for topic in visible_topics(available)}
    topic = topics[key]
    values = profile_values(profile)
    lines = [f"## {topic.title} ({topic.key})", ""]
    lines += [f"- {rule.text.format_map(values)}" for rule in _rules(topic, available)]
    return "\n".join(lines)


def render_all(profile: Mapping[str, Any] | None = None, available: set[str] | None = None) -> str:
    parts = ["# FreeCAD-Buddy-Designregeln"]
    parts += [render_topic(topic.key, profile, available) for topic in visible_topics(available)]
    return "\n\n".join(parts)


def build_instructions(available: set[str] | None = None) -> str:
    """Compact server instructions: core rules of every topic plus a pointer to the full rulebook."""
    values = profile_values(None)
    lines = [
        "FreeCAD Buddy baut 3D-Druck-Bauteile in FreeCAD PartDesign so, wie ein erfahrener Mensch es tun würde:",
        "parametrisch, vollständig bestimmt, mit lesbarem Modellbaum – manuell weiterbearbeitbar.",
        "",
        "Kernregeln:",
    ]
    number = 0
    for topic in visible_topics(available):
        for rule in _rules(topic, available):
            if rule.core:
                number += 1
                lines.append(f"{number}. {rule.text.format_map(values)}")
    keys = ", ".join(topic.key for topic in visible_topics(available))
    lines += ["", f"Vollständiges Regelwerk mit Druckwerten: get_design_rules(topic) – Themen: {keys}."]
    return "\n".join(lines)
