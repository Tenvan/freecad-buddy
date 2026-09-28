# Phase 5 — 3D-Druck-Workflow

> **Ziel:** Modelle werden vor dem Export auf Druckbarkeit geprüft und in druckfertigen Formaten auf dem Druckbett platziert exportiert.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 2, Kriterien AC-10, AC-11. Default-Profil 256×256×256 mm, Düse 0,4 mm, Layer 0,2 mm, PLA (OF-03).

## Session-Pakete

### 📦 Session S9 — Druckerprofil, Druckbarkeits-Check, Export ✅

Enthaltene Aufgaben: #5.1, #5.2, #5.3, #5.4 (umgesetzt vom `fixer`, #5.4-Hinweise ergänzt)

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | Alle Aufgaben umgesetzt; offen sind Slicer-Sichtung und optionaler Probedruck | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #5.1 | `printing/profile.py` (TOML unter `%APPDATA%\FreeCADBuddy\printer-profile.toml`, validiert) | Profil in User-Config | 2026-09-27 |
| #5.2 | `printing/check.py`: invalid/no/multiple solids, not_closed, build_volume, overhang, thin_wall (Strahl-Sampling), small_feature | — | 2026-09-27 |
| #5.3 | `printing/export.py`: STL, 3MF, STEP; Druckbett-Platzierung auf Kopie; Reimport-Abweichung | 3MF in 26.3 unterstützt | 2026-09-27 |
| #5.4 | `design_hints` in der Druckprüfung (Fase statt Verrundung, Wandstärke, Passungsspiel/Bohrungszugabe aus Profil); Hole-Hinweis für Spiel; Referenzprojekt Box übernimmt `clearance_fit` als Parameter | — | 2026-09-27 |

## Geplante Abnahmeprüfungen

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G6 / AC-11: 3MF im Slicer: Teil liegt auf dem Bett, Maße stimmen | offen | ausstehend (nur Nutzer) | Reimport-Abweichung < 1 % automatisiert belegt |
| G8 (optional): Probedruck Box mit Deckel | offen | ausstehend (nur Nutzer) | — |

## 🔄 Nächste Session

> **Einstieg:** Phase umgesetzt. Offen: G6, G8 (`docs/acceptance.md`).
