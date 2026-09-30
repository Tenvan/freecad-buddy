# PartDesign-Vollständigkeit: Loft, Helix, Primitive, Boolean, Draft, Datum

> Erstellt: 2026-09-29 │ Status: ✅ Umgesetzt im Sprint [`freecad-buddy-partdesign`](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md) │ Priorität: hoch │ Architektur-Impact: mehrere

## Spezifikation

> Spec-Stand: 1 │ Spec-Status: Freigegeben │ Freigabe: Ralf im Chat, 2026-09-29 („starte sprint“), inklusive der Annahmen OF-01 bis OF-04 als Entscheidungen; Umsetzung und Nachweise im Sprint

## Ausgangslage

Der Tool-Katalog (Stand 0.2.0, 51 Tools, [`docs/tools.md`](../../../docs/tools.md)) deckt die skizzenbasierten PartDesign-Features vollständig und mit Core-Tests ab: Pad, Pocket, Revolution, Groove, Additive/Subtractive Pipe, Hole, Fillet, Chamfer, Thickness, Mirrored, Linear/Polar Pattern, MultiTransform, Datum Plane, SubShapeBinder. Der Abgleich mit der PartDesign-Werkzeugleiste am 2026-09-29 zeigt sechs Werkzeuggruppen ohne Tool:

- Loft (additiv/subtraktiv) – kein Ersatz.
- Helix allgemein – nur das ISO-Außengewinde über `thread`. `hole(threaded=true)` setzt `Threaded`, aber nicht `ModelThread`; ein Innengewinde wird deshalb nicht als Geometrie geschnitten (vermutet, ungeprüft in 26.3).
- Primitive (Box, Zylinder, Kugel, Kegel, Ellipsoid, Torus, Prisma, Keil, jeweils additiv/subtraktiv).
- Boolean zwischen Bodies – heute nur der Umweg `shape_binder` + `pocket`/`pad`.
- Draft (Dress-up).
- Datum Point, Datum Line, LCS – `PartDesign::Line` wird nur als externe Referenz akzeptiert, es gibt kein Tool zum Anlegen.

Dazu kleinere Lücken in bestehenden Tools: `pad`/`pocket` ohne Taper-Winkel und ohne `up_to_first`, `hole` ohne modelliertes Innengewinde.

## Ziel

Jedes Standard-Werkzeug der PartDesign-Werkzeugleiste (Stand FreeCAD 26.3) ist über ein Tool erreichbar, parametrisch und mit Headless-Core-Test belegt. Ausgenommen sind die in den Nicht-Zielen genannten Nischenwerkzeuge. Das Tool-Budget bleibt unter 100 (Planung: 51 → 57).

## Beteiligte und Zielgruppen

- **Ralf:** modelliert über Claude Code und bearbeitet die Ergebnisse in der GUI weiter; entscheidet die offenen Fragen.
- **Agent:** setzt Core, Bridge, Server, Regelwerk, Doku und Tests um.

## Anforderungen

- **A-01 `loft`:** Additiver oder subtraktiver Loft über mindestens zwei Skizzen (Reihenfolge = Übergang), Optionen `ruled` und `closed`. Skizzen liegen auf Ursprungsebenen oder `datum_plane` mit Offset-Parameter.
- **A-02 `helix`:** Additive oder subtraktive Helix aus einer Profilskizze um eine Achse (Skizzenachse, Body-Achse oder Datum Line). Eingaben: Steigung (`pitch`), Höhe oder Windungen, Kegelwinkel, Drehsinn. `thread` bleibt als Intent-Tool bestehen und nutzt intern denselben Weg.
- **A-03 `primitive`:** Additives oder subtraktives Primitiv mit `kind` = `box` | `cylinder` | `sphere` | `cone` | `torus` | `ellipsoid` | `prism` | `wedge`. Alle Maße sind Parameter oder Ausdrücke; Lage über Ebene (XY/XZ/YZ oder Datum) plus Mittelpunkt/Offset, nie über Solid-Flächen.
- **A-04 `boolean`:** `op` = `fuse` | `cut` | `common` mit einem oder mehreren anderen Bodies desselben Dokuments. Das Ergebnis liegt im Ziel-Body; der Modellbaum bleibt lesbar (Beschriftung `Boolean_<Zweck>`).
- **A-05 `draft`:** Schräge auf Flächen per Selektor (z. B. `faces:vertical`), Winkel als Parameter, neutrale Ebene und Zugrichtung wählbar; Selektor wird wie bei `fillet` gespeichert und nach Parameteränderung neu aufgelöst.
- **A-06 `datum`:** `kind` = `point` | `line` | `lcs` mit Lage aus Parametern (Offset, Winkel) relativ zum Ursprung oder zu einer Datum-Ebene. `revolve` und `pattern` akzeptieren eine Datum Line als Achse, `create_sketch` einen LCS als Basis.
- **A-07 `pad`/`pocket`:** optionaler Taper-Winkel (`taper`, Parameter) und Modus `up_to_first`.
- **A-08 `hole`:** Option `model_thread` schneidet das Innengewinde als Geometrie (FreeCAD `ModelThread`); die Gewindegröße kommt aus dem vorhandenen `thread_size`.
- **A-09 Regelwerk und Doku:** Themen `features` und `references` in `get_design_rules` nennen die neuen Tools mit Einsatzregel (Loft für Übergänge, Helix für Federn und Sondergewinde, Primitive nur wo eine Skizze keinen Vorteil bringt, Boolean nur zwischen Bodies desselben Bauteils). `docs/tools.md` wird neu generiert, `REQUIRED_TYPES` in `compat.py` um die neuen Typen ergänzt.
- **A-10 Qualität:** Jedes neue Tool ist genau ein Undo-Schritt, alle Maße sind über Parameter änderbar, `uv run poe check` bleibt grün, alle MCP-Ausgaben englisch.

## Nicht-Ziele

- Scaled außerhalb von MultiTransform, Clone, Sprocket, Shaft Wizard, das eingebaute Involute Gear (`add_gear` deckt Zahnräder über das Addon ab).
- `up_to_face`/Skizzen auf Solid-Flächen (bleibt Nicht-Ziel des Projekts, Face-Referenzen sind instabil).
- Sketcher-Erweiterungen (Ellipse, B-Spline) – eigenes Ticket bei Bedarf.
- Feature-Verwaltung (Tip setzen, Umsortieren, Suppress) – eigenes Ticket bei Bedarf.
- Slicer-genaue Prüfung der Druckbarkeit von Gewinden.

## Regeln und Einschränkungen

- Bestehende Verträge bleiben: Tool = eine Transaktion mit Rollback, Werte als Zahl/Parametername/Ausdruck, Namenskonvention `<Typ>_<Zweck>`, Selektoren statt Topologie-Namen, englische MCP-Ausgaben (Doku und Chat deutsch).
- Neue Bridge-Methoden werden in `methods.py` registriert; `test_server_tools_only_use_registered_bridge_methods` bleibt grün.
- Tool-Budget ≤ 100; jedes neue Tool braucht Beschreibung, Schema, Beispiel im generierten Katalog.
- `boolean` darf die Regel „ein Body = ein druckbares Bauteil“ nicht unterlaufen: verbundene Bodies gehören zum selben Bauteil. Das Regelwerk sagt das ausdrücklich.
- Kein neuer Addon-Bedarf; alles nativ über PartDesign-Typen.

## Beispiele

- Trichter: Kreis Ø 40 auf XY, Kreis Ø 12 auf `datum_plane` mit `Funnel_Height` → `loft` additiv → ein Solid, Parameteränderung `Funnel_Height` 30 → 50 aktualisiert die Höhe.
- Druckfeder: Kreisprofil Ø 2 neben der Z-Achse → `helix` additiv mit `Spring_Pitch` 4 und `Spring_Height` 30 → Feder mit 7,5 Windungen; `Spring_Pitch` 5 → 6 Windungen.
- Kugelknauf: `primitive kind=sphere diameter=Knob_Diameter` auf einem Zylinder-Pad → ein Solid, Kugel folgt dem Parameter.
- Gehäuse aus zwei Hälften: Body `Shell_Top`, Body `Rib_Insert` → `boolean fuse` in `Shell_Top` → ein Solid, `check_printability` und `export_body` arbeiten mit dem Ergebnis.
- Innengewinde M6: `hole` mit `threaded=true, model_thread=true` → Gewindegänge sichtbar im Modell, `get_object` meldet gültigen Solid.
- Schräge Seitenwände: `draft faces:vertical angle=Draft_Angle` → alle Seitenflächen um 3° geneigt, Parameter 3 → 5 folgt.

## Ausnahme- und Fehlerfälle

- `loft` mit nur einer Skizze oder Skizzen in derselben Ebene ohne Offset → `validation` mit Hinweis.
- `helix` mit Steigung ≤ 0 oder Profil, das die Achse schneidet → `validation`; der Body bleibt unverändert (Rollback).
- `primitive` subtraktiv, das nichts schneidet → Warnung wie bei `pocket` (`_ensure_cuts`).
- `boolean` mit einem Body aus einer Assembly-`Parts`-Gruppe oder mit sich selbst → `validation`.
- `draft` mit Selektor ohne Treffer oder mit Flächen, die keinen gültigen Solid ergeben → Fehler mit Selektor-Vorschau, Rollback.
- `model_thread` in einem FreeCAD-Build ohne `ModelThread`-Eigenschaft → `unsupported` mit Versionshinweis; ohne `threaded=true` → `validation`.

## Akzeptanzkriterien

AC-01 bis AC-11 sind erfüllt laut [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis); dort stehen Nachweis und Prüfebene. Der Wortlaut unten bleibt der Stand der Spezifikation.

- [x] AC-01: Trichter aus zwei Kreisskizzen per `loft` ergibt einen gültigen Solid; die Höhe folgt dem Parameter der Datum-Ebene; subtraktiver Loft schneidet aus einem Pad heraus.
- [x] AC-02: `helix` erzeugt additiv eine Feder und subtraktiv eine Nut mit parametrischer Steigung; Windungszahl folgt `pitch`/`height`. `thread` liefert weiterhin das bisherige Ergebnis (bestehende Tests grün).
- [x] AC-03: Alle acht `primitive`-Arten entstehen additiv und subtraktiv mit Maßen aus Parametern; Volumen stimmt je Art mit der Formel auf 1 % überein.
- [x] AC-04: `boolean` mit `fuse`, `cut`, `common` zwischen zwei Bodies ergibt jeweils den erwarteten Solid (Volumenprüfung); ungültige Kombinationen werden abgelehnt.
- [x] AC-05: `draft` neigt die selektierten Flächen um den Parameterwinkel; nach Parameteränderung und Recompute bleibt der Solid gültig und der Selektor trifft dieselben Flächen.
- [x] AC-06: `datum` legt Point, Line und LCS parametrisch an; `revolve` um eine Datum Line und `pattern kind=polar` um eine Datum Line liefern dasselbe Ergebnis wie um die Body-Achse bei gleicher Lage.
- [x] AC-07: `pad`/`pocket` mit `taper` erzeugen geneigte Wände (Kontrolle über Volumen); `up_to_first` stoppt an der nächsten Fläche.
- [x] AC-08: `hole` mit `model_thread=true` erzeugt Gewindegeometrie (Volumen kleiner als ohne, Solid gültig); ohne die Eigenschaft im Build kommt `unsupported`.
- [x] AC-09: `get_design_rules("features")` und `("references")` nennen alle neuen Tools; `test_rules_only_name_registered_tools` und `test_every_topic_of_r03_is_covered` sind grün. `docs/tools.md` ist regeneriert, Tool-Zahl ≤ 100.
- [x] AC-10: Jedes neue Tool ist ein Undo-Schritt, der Modellbaum zeigt sprechende Labels, `uv run poe check` ist grün, `test_language.py` findet keine deutschen Texte.
- [x] AC-11 (GUI, Nutzerabnahme): Loft, Helix und Primitiv aus AC-01 bis AC-03 sind in der GUI weiterbearbeitbar (Feature öffnen, Parameter ändern, Recompute ohne Fehler).

## Offene Fragen

| ID | Frage | Betroffen | Annahme bis Klärung | Verantwortlich |
|---|---|---|---|---|
| OF-01 | Soll `draft` aufgenommen werden? Für FDM bringt es wenig (Entformungsschrägen sind Guss/Spritzguss). | A-05, AC-05 | Ja, wegen „jedes Standard-Werkzeug“; niedrigste Priorität im Sprint | Ralf |
| OF-02 | `PartDesign::Boolean` zieht die beteiligten Bodies in seine Gruppe (vermutet, ungeprüft). Verträgt sich das mit `get_model_tree`, Assembly4-`Parts` und „ein Body = ein Bauteil“? | A-04, AC-04 | ✅ Geklärt (Spike S1, 2026-09-29): Bodies wandern in die Boolean-Gruppe, `get_model_tree` listet sie weiter; fuse/cut/common voll umgesetzt, Bodies aus Assembly-`Parts` abgelehnt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#offene-fragen) | Agent (Spike), Entscheidung Ralf |
| OF-03 | Ist `ModelThread` in FreeCAD 26.3 vorhanden und ist das Ergebnis mit 0,4-mm-Düse druckbar? | A-08, AC-08 | ✅ Geklärt (Spike S1, 2026-09-29): Eigenschaft in 26.3 vorhanden, Solids gültig; Druckbarkeit mit 0,4-mm-Düse bleibt ungeprüft (Probedruck offen), siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#offene-fragen) | Agent (Spike) |
| OF-04 | Ein Sprint oder zwei (Features / Referenzen und Kleinigkeiten)? | Sprint-Planung | Ein Sprint mit fünf Phasen | Ralf |

## Umsetzung und Nachweis

| Kriterium | Geplante Aufgabe / Schritte | Prüfebene und erwartetes Ergebnis | Nachweis / Status |
|---|---|---|---|
| AC-01 | `features.loft` (Additive/SubtractiveLoft), Bridge-Methode `feature.loft`, Server-Tool | Headless-Core-Test: Trichter, Parameterfolge, subtraktiv | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-02 | `features.helix` (Additive/SubtractiveHelix), `thread.py` auf den gemeinsamen Kern umstellen | Headless-Core-Test Feder/Nut; bestehende `thread`-Tests | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-03 | `features.primitive` mit Typ-Tabelle `kind → (Additive*, Subtractive*)`, Lage über Attachment an Ebene | Headless-Core-Test: 8 Arten × 2, Volumenformeln | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-04 | Spike OF-02, dann `features.boolean` (PartDesign::Boolean) | Headless-Core-Test fuse/cut/common, Ablehnungsfälle | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-05 | `features.draft` über `_dress_up` mit Face-Selektor | Headless-Core-Test inkl. Re-Resolve nach Parameteränderung | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-06 | `features.datum` (Point/Line/CoordinateSystem), `_revolve_axis` und `pattern` um Datum-Line-Achse erweitern, `create_sketch` auf LCS | Headless-Core-Test Achsvergleich | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-07 | `pad`/`pocket`: `TaperAngle`, Modus `up_to_first` | Headless-Core-Test Volumen | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-08 | Spike OF-03, `hole`: `model_thread` → `ModelThread` | Headless-Core-Test Volumen/Gültigkeit; `unsupported`-Pfad mit Fake | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-09 | `design_rules.py` Themen `features`/`references`, `compat.REQUIRED_TYPES`, `python tools/gen_tool_docs.py` | Unit-Tests Regelwerk, Tool-Doku-Test | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-10 | Labels, Undo, Sprache je Tool | `uv run poe check` | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |
| AC-11 | GUI-Abnahme durch Ralf nach Freigabe | Nutzerprüfung GUI | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-partdesign/00-index.md#umsetzung-und-nachweis) |

Umsetzung folgt dem freigegebenen Spec-Stand. Browser-/manuelle Prüfungen zusätzlich nach der [Abnahmefreigabe](../../README.md#browser--und-manuelle-abnahmeprüfungen) behandeln; Spec-Freigabe ist keine Testfreigabe.

## Architektur-Impact

| Bereich | Einschätzung |
|---|---|
| `docs/architecture.md` | prüfen: Abschnitte Tool-Katalog und Modellierungsregeln (Primitive als Ausnahme von „Skizze zuerst“, Boolean-Regel, Datum-Referenzen) |

Relevante Architekturfragen (Schichten core / bridge / server, RPC-Vertrag, Modellierungsregeln):

- Core: sechs neue Funktionen in `features.py` bzw. ein neues Modul `primitives.py`, wenn `features.py` zu groß wird; `thread.py` wird Aufrufer von `helix`.
- Bridge: sechs neue Einträge in `methods.py`, keine Protokolländerung.
- Server: neue Tools in `tools/feature.py` und `tools/reference.py`; Tool-Budget 51 → 57.
- Modellierungsregel „Skizzen nur auf Ursprungs-/Datum-Ebenen“ gilt auch für Primitive und Loft-Profile.
- Kompatibilität: neue `REQUIRED_TYPES`; `get_status` meldet fehlende Typen weiterhin vorab.

## Relevante Dateien / Module

- `addon/FreeCADBuddy/buddy_core/features.py` (`pad`, `pocket`, `_revolve_axis`, `hole`, `_dress_up`, `pattern`, `datum_plane`)
- `addon/FreeCADBuddy/buddy_core/thread.py`
- `addon/FreeCADBuddy/buddy_core/compat.py` (`REQUIRED_TYPES`)
- `addon/FreeCADBuddy/buddy_bridge/methods.py`
- `src/buddy_server/tools/feature.py`, `src/buddy_server/tools/reference.py`
- `src/buddy_server/design_rules.py`
- `tools/gen_tool_docs.py`, `docs/tools.md`
- `tests/core/test_features.py`, `tests/core/test_binder_hole.py`, `tests/core/test_assembly_material_thread.py`
- `tests/tools/test_tool_contract.py`, `tests/server/test_design_rules.py`, `tests/server/test_language.py`

## Abhängigkeiten

- keine Tickets; FreeCAD 26.3 headless für die Core-Tests (`uv run poe check`).
- OF-02 und OF-03 als Spikes vor der jeweiligen Umsetzung.

## Notizen

AUTO-RESUME START

**Start-Prompt:** Setze das Ticket `partdesign-vollstaendigkeit` um. Beginne mit den Spikes OF-02 (Boolean-Gruppe im Modellbaum) und OF-03 (`ModelThread` in 26.3) und halte die Ergebnisse im Ticket fest. Danach in dieser Reihenfolge: `loft`, `helix` (mit `thread`-Umstellung), `primitive`, `datum`, Taper/`up_to_first`, `model_thread`, `boolean`, `draft`. Jedes Tool mit Headless-Core-Test, Bridge-Registrierung, Server-Tool und Regelwerk-Eintrag, dann `docs/tools.md` regenerieren. GUI-Prüfung AC-11 nur nach ausdrücklicher Freigabe durch Ralf.

**Lies zuerst:**

- dieses Ticket, Abschnitt Akzeptanzkriterien und Offene Fragen
- `addon/FreeCADBuddy/buddy_core/features.py` (`_new`, `_finish`, `_ensure_cuts`, `_dress_up` als Muster)
- `addon/FreeCADBuddy/buddy_core/thread.py` (bestehende SubtractiveHelix)
- `docs/architecture.md`, Abschnitte Modellierungsregeln und Tool-Katalog
- `tests/core/test_features.py` (Teststil, Fixtures)

AUTO-RESUME ENDE

**Umsetzungshinweise (ungeprüft, im Sprint verifizieren):**

- Loft: `PartDesign::AdditiveLoft`/`SubtractiveLoft` mit `Profile` (erste Skizze) und `Sections` (weitere), `Ruled`, `Closed`.
- Helix: `PartDesign::AdditiveHelix`/`SubtractiveHelix` mit `Profile`, `ReferenceAxis`, `Mode` (`pitch-height-angle` | `pitch-turns-angle` | `height-turns-angle`), `Pitch`, `Height`, `Turns`, `Angle`, `LeftHanded`, `Reversed`. `thread.py` setzt heute schon `SubtractiveHelix`; Kern extrahieren.
- Primitive: `PartDesign::AdditiveBox` … `SubtractiveWedge`; Lage über `AttachmentSupport`/`MapMode` an Ursprungs- oder Datum-Ebene plus `AttachmentOffset` mit Ausdrücken, damit die Lage parametrisch bleibt.
- Boolean: `PartDesign::Boolean` mit `Type` (`Fuse` | `Cut` | `Common`) und `Group` = andere Bodies. Verhalten im Baum ist OF-02.
- Draft: `PartDesign::Draft` mit `Base` (Flächen), `Angle`, `NeutralPlane`, `PullDirection`, `Reversed`; Selektor-Speicherung wie `fillet` (`BuddySelector`).
- Datum: `PartDesign::Point`, `PartDesign::Line`, `PartDesign::CoordinateSystem` mit `AttachmentOffset` aus Parametern; `_revolve_axis` um Datum-Line-Fall erweitern.
- Taper: `Pad.TaperAngle`/`Pocket.TaperAngle` (bei `two_sides` zusätzlich `TaperAngle2`); Modus `up_to_first` = `Type = UpToFirst`.
- Regelwerk-Ergänzung (Thema `features`): Primitive nur für Kugel, Torus, Ellipsoid, Keil und schnelle Hilfskörper; Box/Zylinder/Prisma weiterhin Skizze + Pad, weil in der GUI besser editierbar.

**Release-Änderungen (Sprint-Session-Log):** je Tool `[feature][core|server]`, Regelwerk `[doc][server]`, Doku `[doc][docs]`.

## Übergabe an Sprint-Planung

- Architektur-Update-Artefakt nötig: ja (`98-architecture-update.md`, Modellierungsregeln und Tool-Katalog)
- Vermutete Ziel-Dokumente: `docs/architecture.md`, `docs/tools.md`
- Offene Klärungen vor Umsetzung: OF-01 (Draft ja/nein), OF-04 (ein oder zwei Sprints); OF-02 und OF-03 als Spikes im Sprint
