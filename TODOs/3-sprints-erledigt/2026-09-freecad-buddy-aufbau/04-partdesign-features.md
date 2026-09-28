# Phase 4 — PartDesign-Features & Robustheit

> **Ziel:** Die für 3D-Druck relevanten PartDesign-Features sind per Tool nutzbar; Kanten und Flächen werden semantisch ausgewählt, sodass Parameteränderungen keine falschen Referenzen erzeugen.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 2, Kriterien AC-05, AC-06, AC-07.

## Session-Pakete

### 📦 Session S7 — PartDesign-Features ✅

Enthaltene Aufgaben: #4.1, #4.2, #4.3, #4.4

### 📦 Session S8 — Semantische Selektoren, TNP-Robustheit, Fehlerkatalog ✅

Enthaltene Aufgaben: #4.5, #4.6, #4.7

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | Alle Aufgaben umgesetzt | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #4.1 | `features.py`: pad (length/symmetric/two_sides/up_to_last), pocket (length/symmetric/through_all), revolve (Revolution/Groove); subtraktive Features drehen sich automatisch um, wenn sie nichts schneiden | Auto-Flip mit Warnung | 2026-09-27 |
| #4.2 | hole (ISO metrisch, countersink/counterbore, Tiefe/durch, Durchmesser-Override), datum_plane (Offset/Winkel, parametrisierbar) | — | 2026-09-27 |
| #4.3 | fillet, chamfer, shell (Thickness) über Selektoren | — | 2026-09-27 |
| #4.4 | pattern: mirrored, linear, polar; Anzahl als Integer-Parameter bindbar | — | 2026-09-27 |
| #4.5 | `select.py` Selektor-Grammatik inkl. `x=/y=/z=` mit Parametern/Ausdrücken, `of_feature`, `select_geometry`-Vorschau, `BuddySelector` + `refresh_references` | Grammatik in `docs/architecture.md` | 2026-09-27 |
| #4.6 | Robustheitstests `tests/core/test_robustness.py`, `test_values_select.py` (Parameter-Varianten, Topologie-Verschiebung, Innenkante folgt `Thickness`) | — | 2026-09-27 |
| #4.7 | `diagnostics.py` Fehlerkatalog → `hints` bei `recompute_failed`; getrennte Körper und wirkungslose Schnitte mit eigener Meldung | — | 2026-09-27 |

## Geplante Abnahmeprüfungen

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| Teil von G5 / AC-07: in der GUI Parameter ändern, Verrundung bleibt an den gemeinten Kanten | offen | ausstehend (nur Nutzer) | headless belegt (`tests/core/test_robustness.py`) |

## 🔄 Nächste Session

> **Einstieg:** Phase umgesetzt. Offen: Teil von G5 (`docs/acceptance.md`).
