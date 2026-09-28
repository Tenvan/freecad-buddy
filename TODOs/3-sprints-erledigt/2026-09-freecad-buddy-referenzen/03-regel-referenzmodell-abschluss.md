# Phase 3 — Regel, Referenzmodell, Katalog & Abschluss

> **Ziel:** Der Agent kennt die Layout-Skizzen-Regel; der Lüfterrahmen v3 belegt per Test, dass ein Lochbild genau eine Quelle hat; der Tool-Katalog ist nach Arbeitsphasen gruppiert und die Dokument-Tools sind zusammengeführt; Doku und Gesamtcheck sind aktuell, Ralf nimmt die GUI ab.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 2, Kriterien AC-09 bis AC-14.

## Session-Pakete

### 📦 Session S3 — Regel, Referenzmodell, Katalog, Doku, Abnahme

- **Kontext-Anker:** `src/buddy_server/design_rules.py`, `tests/core/test_reference_fan_frame.py`, `src/buddy_server/tools/`, `src/buddy_server/catalog.py`, `tools/gen_tool_docs.py`, `docs/architecture.md`, `docs/tools.md`, `docs/tools/`
- **Einstiegspunkt:** #3.1 — Regel Layout-Skizze
- **Erfolgskriterium:** AC-09 bis AC-11, AC-13, AC-14 grün (`uv run poe check`) — **erreicht**; AC-12 von Ralf bestätigt; Sprint abgeschlossen — **erreicht**.
- **Architektur-Relevanz:** `docs/architecture.md` — **aktualisiert**

Enthaltene Aufgaben: #3.1, #3.2, #3.3, #3.4, #3.5, #3.6, #3.7

---

## ✅ Active Tasks

*Keine – alle Aufgaben der Phase erledigt (S3/S4, 2026-09-28).*

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #3.1 | Regeln (englisch) im Thema `references`: Layout-Skizze (reale Layout-Geometrie referenzieren, Konstruktionsgeometrie nicht referenzierbar), andere Bodies über `shape_binder`, parametrische Senkungen über `hole`; Test `test_references_topic_teaches_layout_sketch_and_binder`; Instructions 1 899 ≤ 2 000 Zeichen | übernommen (architecture.md Modellierungsregeln) | 2026-09-28 |
| #3.2 | `tests/core/test_reference_fan_frame.py`: Lüfterrahmen v3 nach Ralfs Methode (70-mm-Konstruktionslinie symmetrisch zum Ursprung, Abstand Loch–Rahmen `Wall + Head_D/2`, Löcher per `hole` direkt aus der Layout-Skizze, Laschen und Kopftaschen extern referenziert); Messung Lochabstand 70 → 76 mm, `Wall` 2 → 2,5; nur `Sketch_Layout` bindet `Mount_Diag`. Zusätzlich `out/Fan_Frame_50_to_60_v3.FCStd` mit Deckel-Body über `shape_binder` für die GUI-Abnahme | keins | 2026-09-28 |
| #3.3 | `docs/architecture.md` (Repository-Layout, Modellierungsregeln, Kompatibilität, Tool-Katalog), `docs/tools.md` + `docs/tools/*.md` generiert, `uv run poe check` grün (94 + 208 + 2 Tests) | übernommen | 2026-09-28 |
| #3.6 | Katalog gruppiert (Spec-Stand 2): `src/buddy_server/tools/` mit einem Modul je Gruppe (AST-genaue Aufteilung der früheren `tools.py`), `catalog.Group`, Präfix `[<Kategorie>]` in jeder Beschreibung, Generator schreibt Index + 10 Gruppenseiten; Tests Gruppenzuordnung/Präfix/Aktualität | übernommen | 2026-09-28 |
| #3.7 | `document(action=new\|open\|save\|close\|revert)` ersetzt fünf Tools (45 Tools); Hinweistexte im Core, E2E-Test, Referenzprojekte, Samples umgestellt; Test fehlender Pflichtangaben (`test_document_tool.py`) | übernommen | 2026-09-28 |
| #3.4 | GUI-Abnahme AC-12a–c durch Ralf bestätigt (Chat 2026-09-28: „GUI-Prüfung ok“) | keins | 2026-09-28 |
| #3.5 | Sprint-Abschluss: Nachweise vollständig, Session-Log S4, Sprint nach `3-sprints-erledigt/2026-09-freecad-buddy-referenzen/`, `master-todo.md` aktualisiert | keins | 2026-09-28 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-12a: `out/Fan_Frame_50_to_60_v3.FCStd` in der FreeCAD-GUI öffnen → `Sketch_ScrewHeads` bearbeiten: externe Geometrie (lila) aus `Sketch_Layout` sichtbar, die Kreise hängen daran, DoF 0 | vom Nutzer bestätigt | Ralf im Chat, 2026-09-28: „GUI-Prüfung ok“ (Umfang a–c) | bestanden – Nutzerprüfung, kein Agententest; Session-Log S4 |
| AC-12b: Im VarSet `Parameters` `Mount_Diag` auf z. B. 76 setzen → Löcher, Laschen und Kopftaschen folgen, Modell bleibt gültig | vom Nutzer bestätigt | Ralf im Chat, 2026-09-28: „GUI-Prüfung ok“ (Umfang a–c) | bestanden – Nutzerprüfung, kein Agententest; Session-Log S4 |
| AC-12c: Body `Lid`: `Binder_FrameOutline` im Baum, `Wall` ändern → Binder und Deckelkontur folgen | vom Nutzer bestätigt | Ralf im Chat, 2026-09-28: „GUI-Prüfung ok“ (Umfang a–c) | bestanden – Nutzerprüfung, kein Agententest; Session-Log S4 |

## 🔄 Nächste Session

> Phase und Sprint abgeschlossen (2026-09-28). Keine offenen Aufgaben.
