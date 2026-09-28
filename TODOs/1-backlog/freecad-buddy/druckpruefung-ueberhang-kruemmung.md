# Druckprüfung: Überhänge an gekrümmten Flächen und freie Brücken erkennen

> Erstellt: 2026-09-28 │ Status: 🟡 Folgetask │ Priorität: hoch │ Architektur-Impact: core

## Spezifikation

> Spec-Stand: 1 │ Spec-Status: Entwurf │ Freigabe: ausstehend

## Ausgangslage

Beim Live-Test am 2026-09-28 (Testplatte mit Griff: `sweep` eines Ø-10-mm-Stabs, Querstab rund 80 mm frei in 35 mm Höhe) meldete `check_printability` **keinen** Überhang, obwohl die runde Unterseite des Querstabs ohne Stütze nicht druckbar ist.

Ursache (im Code bestätigt): `_check_overhang` in `addon/FreeCADBuddy/buddy_core/printing/check.py` wertet pro Fläche nur **eine** Normale in der Parametermitte `(u, v) = (0.5, 0.5)` aus. Bei gekrümmten Flächen (Zylinder, Torus, Sweep, Verrundungen) zeigt dieser Punkt beliebig zur Seite oder nach oben. Die überhängenden Bereiche derselben Fläche fallen dann durch. Freie Brücken (waagrechte Unterseiten ohne Auflage) prüft die Funktion gar nicht.

## Ziel

`check_printability` erkennt Überhänge unabhängig davon, ob die Fläche eben oder gekrümmt ist, und meldet freie Brücken mit ihrer Spannweite. Damit ist die Prüfung auch für mit `sweep`, `revolve` und `fillet` erzeugte Geometrie verlässlich.

## Beteiligte und Zielgruppen

- **Ralf:** verlässt sich auf die Prüfung vor dem Slicen.
- **Agent:** nutzt die Befunde, um Fasen, Stützen oder eine geänderte Orientierung vorzuschlagen.

## Anforderungen

- Überhänge werden flächenanteilig bewertet, etwa über die Tessellierung (Dreiecksnormalen und -flächen) oder ein Normalen-Raster je Fläche. Gemeldet werden die betroffene Fläche in mm², der Anteil an der Oberfläche und die Faces.
- Selbsttragende Bereiche nahe der Grenze (z. B. die obere Hälfte eines liegenden Zylinders) werden nicht als Überhang gemeldet.
- Bettkontakt bleibt ausgenommen.
- Freie Brücken: Waagrechte oder überhängende Unterseiten, die über eine Spannweite von mehr als dem Grenzwert (Regelwerk: 10 mm) nichts unter sich haben, erzeugen einen eigenen Befund `bridge` mit Spannweite und Höhe.
- Die Laufzeit bleibt bei den Referenzprojekten unter dem bisherigen Timeout (Bridge 120 s).

## Nicht-Ziele

- Automatisches Erzeugen von Stützstrukturen oder Umorientieren des Bauteils.
- Slicer-genaue Simulation.

## Regeln und Einschränkungen

- Die Prüfung ist rein lesend, das Dokument bleibt unverändert.
- Grenzwerte kommen aus dem Druckerprofil (`overhang_angle`) bzw. aus dem Regelwerk (Brückenlänge, gegebenenfalls als neuer Profilwert).

## Beispiele

- Testplatte mit Griff (Stab Ø 10 mm, Querstab 80 mm frei) → `overhang` für die untere Stabhälfte und `bridge` mit rund 80 mm Spannweite in rund 35 mm Höhe.
- Liegender Zylinder direkt auf dem Bett → kein `bridge`, der Überhang nur für den unteren Bereich knapp über dem Bett (Grenzwinkel).
- Quader mit 45°-Fase unten → kein Befund.

## Ausnahme- und Fehlerfälle

- Tessellierung schlägt fehl oder dauert zu lange → Fallback auf das Normalen-Raster und ein Hinweis im Ergebnis.

## Akzeptanzkriterien

- [ ] AC-01: Die Testplatte mit Griff meldet `overhang` (Fläche > 0) für den Griff.
- [ ] AC-02: Die Testplatte mit Griff meldet `bridge` mit einer Spannweite von 80 ± 5 mm.
- [ ] AC-03: Ein flacher Quader, ein Quader mit 45°-Fase unten und ein Zylinder stehend auf dem Bett melden keinen Überhang (keine Fehlalarme).
- [ ] AC-04: Die bestehenden Tests in `tests/core/test_printing_check.py` bleiben grün, die Referenzprojekte liegen im Timeout.

## Offene Fragen

- Soll die Brückengrenze ein Profilwert werden (`max_bridge`, Standard 10 mm)? Verantwortlich: Ralf.

## Umsetzung und Nachweis

| Kriterium | Geplante Aufgabe / Schritte | Prüfebene und erwartetes Ergebnis | Nachweis / Status |
|---|---|---|---|
| AC-01 | Überhang über Tessellierung bzw. Normalen-Raster | Headless-Core-Test mit Griff-Fixture | offen |
| AC-02 | Brückenerkennung (Unterseiten ohne Auflage, Spannweite) | Headless-Core-Test | offen |
| AC-03 | Fehlalarm-Fixtures | Headless-Core-Test | offen |
| AC-04 | Regression und Laufzeit | `uv run poe check` | offen |

Umsetzung folgt dem freigegebenen Spec-Stand. Browser-/manuelle Prüfungen zusätzlich nach der [Abnahmefreigabe](../../README.md#browser--und-manuelle-abnahmeprüfungen) behandeln; Spec-Freigabe ist keine Testfreigabe.

## Architektur-Impact

| Bereich | Einschätzung |
|---|---|
| `docs/architecture.md` | nicht betroffen (Befundcodes in `docs/tools.md` ergänzen) |

## Relevante Dateien / Module

- `addon/FreeCADBuddy/buddy_core/printing/check.py` (`_check_overhang`, `_face_point_normal`)
- `tests/core/test_printing_check.py`
- `src/buddy_server/design_rules.py` (Thema `printing`, Brückenlänge)

## Abhängigkeiten

- keine

## Notizen

- Ansatz vermutet und ungeprüft: `shape.tessellate(tolerance)` liefert Punkte und Dreiecke, Normalen und Flächen lassen sich daraus direkt berechnen. Brücken per Strahltest von überhängenden Dreiecken nach unten (`-Z`) gegen den Körper, die Spannweite aus der Ausdehnung zusammenhängender Bereiche ohne Treffer.

## Übergabe an Sprint-Planung

- Architektur-Update-Artefakt nötig: nein
- Vermutete Ziel-Dokumente: `docs/tools.md`
- Offene Klärungen vor Umsetzung: Profilwert `max_bridge`
