# Phase 5 — 3D-Druck-Workflow

> **Ziel:** Modelle werden vor dem Export auf Druckbarkeit geprüft und in druckfertigen Formaten auf dem Druckbett platziert exportiert.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-10, AC-11. Umsetzung nur für freigegebenen Umfang. Default-Profil 256×256×256 mm, Düse 0,4 mm, Layer 0,2 mm, PLA (OF-03, entschieden 2026-09-27).

## Session-Pakete

### 📦 Session S9 — Druckerprofil, Druckbarkeits-Check, Export

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/printing/`, `config/printer-profiles/`
- **Einstiegspunkt:** #5.1 — Druckerprofil
- **Erfolgskriterium:** Fixture-Körper mit bekannten Fehlern werden korrekt gemeldet; Exporte lassen sich mit < 1 % Volumenabweichung reimportieren.
- **Architektur-Relevanz:** `core`
- **Architektur-Notiz:** Ablage und Auswahl von Druckerprofilen (Datei im Projekt vs. User-Config) festlegen.

Enthaltene Aufgaben: #5.1, #5.2, #5.3, #5.4

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #5.1 | Druckerprofil (TOML): Bauraum, Düse, Layerhöhe, Mindestwandstärke, Überhang-Grenzwinkel, Passungs-Toleranzen (Spiel/Press), Material; Tools `get_printer_profile`, `set_printer_profile`. | Geplant | `core` | Phase 4 | — | AC-10 |
| #5.2 | `check_printability(body)`: Solid gültig/geschlossen/ein Solid, Bauraum-Fit, Überhang-Analyse über Flächennormalen (Anteil + Flächenliste), Wandstärke heuristisch (Strahl-Sampling), Features kleiner als Düsendurchmesser. Ergebnis strukturiert mit Schweregrad. | Geplant | `core` | #5.1 | — | AC-10 |
| #5.3 | `export_body`: STL (Mesh-Abweichung aus Profil), 3MF, STEP; optional Ausrichtung auf größte ebene Fläche und Platzierung auf Z = 0; Dateiname `<Doc>_<Body>.<ext>`; Reimport-Validierung. | Geplant | `core` | #5.1 | — | AC-11 |
| #5.4 | Design-Helfer für Druck: Toleranz-Parameter für Passungen automatisch in VarSet, Hinweise (Fase statt Fillet an Bettkante, Bohrungs-Kompensation) als `hints` im `ToolResult`. | Geplant | `core` | #5.2 | — | AC-10 (Erweiterung) |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

GUI- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-11: Exportierte 3MF im Slicer des Nutzers öffnen → Bauteil liegt auf dem Bett, Maße stimmen | offen | ausstehend (nur Nutzer) | ausstehend |
| Optional: Probedruck eines Referenzteils | offen | ausstehend (nur Nutzer) | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 4
> - Nächste Session: S9
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/printing/`
> - Architektur-Deltas: Profil-Ablage in 98-architecture-update.md ergänzen
> - Startpunkt: #5.1
