# Phase 4 — PartDesign-Features & Robustheit

> **Ziel:** Die für 3D-Druck relevanten PartDesign-Features sind per Tool nutzbar; Kanten und Flächen werden semantisch ausgewählt, sodass Parameteränderungen keine falschen Referenzen erzeugen.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-05, AC-06, AC-07. Umsetzung nur für freigegebenen Umfang.

## Session-Pakete

### 📦 Session S7 — PartDesign-Features

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/features/`, PartDesign-API von FreeCAD 26.3
- **Einstiegspunkt:** #4.1 — Pad/Pocket/Revolution/Groove
- **Erfolgskriterium:** Jedes Feature hat einen Headless-Test, der einen gültigen Solid im Body und einen korrekten Tip belegt.
- **Architektur-Relevanz:** `core`
- **Architektur-Notiz:** Einheitliche Feature-Signatur (Profil-Referenz, Typ, Maß/Parameter, Richtung) festhalten.

Enthaltene Aufgaben: #4.1, #4.2, #4.3, #4.4

### 📦 Session S8 — Semantische Selektoren, TNP-Robustheit, Fehlerkatalog

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_core/select/`, `tests/core/test_robustness.py`
- **Einstiegspunkt:** #4.5 — Selektor-Sprache
- **Erfolgskriterium:** Robustheitstest variiert Parameter, Recompute bleibt fehlerfrei und Fillets/Chamfers sitzen weiterhin an den gemeinten Kanten.
- **Architektur-Relevanz:** `core`
- **Architektur-Notiz:** Selektor-Grammatik und Auflösungsstrategie (Geometrie-Eigenschaften + Feature-Herkunft, ggf. FreeCAD-TNP-Mapping) dokumentieren.

Enthaltene Aufgaben: #4.5, #4.6, #4.7

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #4.1 | `pad`, `pocket` (Länge, symmetrisch, zwei Längen, durch alles, bis Fläche), `revolution`, `groove`; Maße optional an Parameter gebunden; Label nach Konvention. | Geplant | `core` | Phase 3 | — | AC-05, AC-06 |
| #4.2 | `hole` (ISO-Metrik, Senkung/Senkkopf, kosmetisches Gewinde, Tiefe/durch alles) auf Skizzenpunkten; `datum_plane`/`datum_axis` (Offset, Winkel, durch Punkte). | Geplant | `core` | #4.1 | — | AC-06 |
| #4.3 | `fillet`, `chamfer`, `thickness` (Schale) – Kanten/Flächen ausschließlich über Selektoren aus #4.5 (Interim: einfache Selektoren, in S8 vollständig). | Geplant | `core` | #4.1 | — | AC-06, AC-07 |
| #4.4 | Muster: `mirrored`, `linear_pattern`, `polar_pattern` (inkl. MultiTransform), Anzahl/Abstand parametrisierbar. | Geplant | `core` | #4.1 | — | AC-06 |
| #4.5 | Semantische Selektoren, z. B. `face:top`, `face:normal=+Z,max_z`, `edges:vertical`, `edges:of_face(top)`, `edges:created_by(Pocket_Slot)`, `edges:circular,radius=2`; Mehrdeutigkeit → Fehler mit Kandidaten. Auflösung zur Laufzeit, Speicherung der Absicht als Objekt-Property für Re-Resolve. | Geplant | `core` | #4.3 | — | AC-07 |
| #4.6 | Robustheitstest-Suite: Parameter-Varianten für Referenzprojekte → Recompute ohne Fehler, Volumen-/Kantenanzahl-Plausibilität, Selektor-Treffer unverändert. | Geplant | `core` | #4.5 | — | AC-05, AC-07 |
| #4.7 | Fehlerkatalog: typische Recompute-/Solver-Fehler (Profil offen, Pocket schneidet nichts, Fillet zu groß, Multiple Solids) → verständliche Meldung + Lösungshinweis im `ToolResult`. | Geplant | `core` | #4.1 | — | AC-06 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

GUI- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-07: Testmodell mit Fillet an Deckkanten; in der GUI einen Parameter ändern, der die Topologie verschiebt → Fillet sitzt weiterhin an den Deckkanten | offen | ausstehend | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 7
> - Nächste Session: S7
> - Relevante Dateien: `addon/FreeCADBuddy/buddy_core/features/`, `addon/FreeCADBuddy/buddy_core/select/`
> - Architektur-Deltas: Feature-Signatur und Selektor-Grammatik in 98-architecture-update.md ergänzen
> - Startpunkt: #4.1
