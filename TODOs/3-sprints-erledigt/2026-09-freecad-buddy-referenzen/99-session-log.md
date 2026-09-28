# 📓 Session-Log

Chronologisches Protokoll aller Arbeitssessions. Nach jeder Session einen neuen Eintrag oben anlegen.
`Release-Änderungen` in derselben Session pflegen; sie bilden später die Grundlage für CHANGELOG/Release-Notes. Interne Änderungen bewusst mit `skip` markieren.

---

## Session 4 — 2026-09-28 (Abnahme und Abschluss)

**Ziel:** GUI-Abnahme dokumentieren, Sprint abschließen, committen.

**Erledigt:**
- #3.4 AC-12a–c von Ralf in der FreeCAD-GUI geprüft und im Chat bestätigt („GUI-Prüfung ok“)
- #3.5 Nachweise, Architektur-Update und Definition of Done abgeschlossen; Sprint nach `3-sprints-erledigt/2026-09-freecad-buddy-referenzen/` verschoben, `master-todo.md` aktualisiert

**Release-Änderungen:**
- `[skip][todos]` Sprint-Abschluss, keine Produktänderung

**Blocker:**
- keine

**Erkenntnisse:**
- Folgeaufgabe für den Regelwerk-Sprint: Die Gruppe „Design-Tools“ entsteht mit `hole_grid` als eigenes Modul in `src/buddy_server/tools/` (R-10 dort).

**Architektur-Erkenntnisse:**
- Betroffene Skills: keine weiteren
- Doku-Delta: keins (in S3 übernommen)
- Nicht übernehmen: —

**Validierung:**
- Browser-/manuelle Abnahme: AC-12a–c durch Ralf bestätigt (Nutzerprüfung, kein Agententest)
- Automatisierte Nachweise aus S1–S3 unverändert gültig (keine Codeänderung seit dem letzten `poe check`)

**Nächste Session:**
- keine – Sprint abgeschlossen

---

## Session 3 — 2026-09-28

**Ziel:** Regel Layout-Skizze, Referenzmodell v3, Doku; dazu Spec-Stand 2 (gruppierter Katalog, `document`-Tool, Aufteilung in Dateien).

**Erledigt:**
- #3.1 Regeln im Thema `references` (englisch) + Test
- #3.2 Referenzmodell Lüfterrahmen v3 als Core-Test; `out/Fan_Frame_50_to_60_v3.FCStd` (mit Binder-Deckel) für die GUI-Abnahme
- #3.6 `src/buddy_server/tools/` (10 Gruppenmodule + `base.py`), `catalog.Group`, Kategorie-Präfix, `docs/tools.md` als Index + `docs/tools/<gruppe>.md`
- #3.7 `document(action=…)` statt fünf Dokument-Tools; Verweise umgestellt
- #3.3 `docs/architecture.md` aktualisiert, `poe check` grün

**Release-Änderungen:**
- `[feature][rules]` Regelwerk `references`: Layout-Skizze, `shape_binder`, parametrische Senkungen
- `[removal][tools]` **Breaking:** `new_document`, `open_document`, `save_document`, `close_document`, `revert_document` entfallen – ersetzt durch `document(action=new|open|save|close|revert)`
- `[feature][tools]` Tool-Beschreibungen tragen ein Kategorie-Präfix (`[Sketch]`, `[Feature]`, …); Katalog nach Arbeitsphasen gruppiert (`docs/tools.md` + `docs/tools/`)
- `[misc][server]` Server-Tools in ein Paket mit einem Modul je Gruppe aufgeteilt
- `[doc][architecture]` Referenzmodell, Kompatibilität externe Geometrie, Tool-Katalog

**Blocker:**
- keine; AC-12 wartet auf Ralfs GUI-Abnahme

**Erkenntnisse:**
- Regel-Test lässt in Regeltexten nur Tool-Namen als snake_case zu – Parameternamen umschreiben.
- Die Aufteilung per AST (Funktions-Quelltext 1:1) vermeidet Abschreibfehler; `ruff --fix` bereinigt die Imports.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: übernommen (Layout, Modellierungsregeln, Kompatibilität, Tool-Katalog)
- Nicht übernehmen: Split-Skript (Scratchpad)

**Validierung:**
- `uv run poe check`: Lint/Format/Pyright sauber, 94 Server-/Tool- + 208 Core-/Bridge-Tests, danach 2 weitere Server-Tests (`test_document_tool.py`) grün
- Browser-/manuelle Abnahme: AC-12 offen, Freigabe/Durchführung durch Ralf ausstehend

**Nächste Session:**
- #3.4 GUI-Abnahme (Ralf), danach #3.5 Sprint-Abschluss
- Hinweis: laufende FreeCAD- und MCP-Server-Instanz vor der Abnahme neu starten

---

## Session 2 — 2026-09-28

**Ziel:** `shape_binder` und parametrische Senkungen bei `hole` (Phase 2).

**Erledigt:**
- #2.1 `buddy_core/binder.py`, `compat`/`naming` ergänzt
- #2.2 Bridge-Methode, Server-Tool `shape_binder`, Doku-Beispiel, `docs/tools.md` (49 Tools), Budget-Test ≤ 100
- #2.3 `hole` mit `cut_diameter`, `cut_depth`, `countersink_angle`
- #2.4 12 Core-Tests

**Release-Änderungen:**
- `[feature][features]` Neues Tool `shape_binder`: bindet Geometrie eines anderen Bodys synchron ein; Quelle für externe Geometrie
- `[feature][features]` `hole`: Senkungsdurchmesser, -tiefe und Senkwinkel als Zahl, Parameter oder Ausdruck
- `[misc][tests]` Tool-Budget-Test auf ≤ 100 Tools angehoben

**Blocker:**
- keine

**Erkenntnisse:**
- `resolve_object` meldet noch deutsch (Bestand, #5.4 des Regelwerk-Sprints); Tests prüfen dort den Fehlercode.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: Binder-Regel, neues Modul `binder.py`, `compat`-Typ → 98
- Nicht übernehmen: —

**Validierung:**
- `uv run poe test`: 91 + 206 passed; `ruff check`, `ruff format --check`, `pyright` sauber
- Browser-/manuelle Abnahme: keine in dieser Session

**Nächste Session:**
- S3: #3.1 Regel, #3.2 Referenzmodell Lüfterrahmen v3, #3.3 Doku, #3.4 GUI-Abnahme (Ralf)

---

## Session 1 — 2026-09-28

**Ziel:** Spike FreeCAD 26.3 und externe Geometrie (`x<N>`) im Core (Phase 1).

**Erledigt:**
- #1.1 Spike (Ergebnisse in 01 und 98; OF-02 geklärt: Konstruktionsgeometrie nicht referenzierbar)
- #1.2 `refs` mit `x<N>`
- #1.3 `buddy_core/sketch/external.py`, `add_geometry` Typ `external`, englische Server-Beschreibungen, `docs/tools.md` generiert
- #1.4 `analyze_sketch` mit `external` und Lint-Stufen, hängende Constraints als `error`
- #1.5 16 Core-Tests

**Release-Änderungen:**
- `[feature][sketch]` `add_geometry` unterstützt externe Geometrie (`type: external`) aus Skizzen, Datums und Bindern desselben Bodys; Referenzen `x<N>` in `add_constraints`, Ausgabe in `analyze_sketch`
- `[feature][sketch]` `analyze_sketch` meldet externe Geometrie mit Quelle sowie hängende Constraints nach gelöschter Quelle

**Blocker:**
- keine

**Erkenntnisse:**
- FreeCAD ignoriert ungültige Elementnamen bei `addExternal` still – eigene Validierung ist Pflicht.
- Nach Löschen der Quelle bleibt die Skizze formal gültig, Constraints hängen an nicht mehr existierenden GeoIds.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: Kompatibilität (`addExternal`, ElementMap), neues Modul `external.py`, Regel reale Layout-Geometrie → in 98
- Nicht übernehmen: Spike-Skripte (liegen nur im Scratchpad)

**Validierung:**
- `uv run poe test-core`: 194 passed (inkl. 16 neu); `uv run poe test-tools`: 91 passed; `ruff check`, `ruff format --check`, `pyright`: sauber
- Browser-/manuelle Abnahme: keine in dieser Session

**Nächste Session:**
- S2: #2.1 `shape_binder` Core, #2.3 `hole`-Senkungsmaße
- Relevant: `buddy_core/features.py`, `buddy_core/compat.py`, `buddy_bridge/methods.py`, `src/buddy_server/tools.py`

---

## Session 0 — 2026-09-28 (Planung)

**Ziel:** Sprint aus Ralfs Auftrag planen (externe Geometrie, `shape_binder`, Senkungsmaße, Regel Layout-Skizze).

**Erledigt:**
- Sprint-Spec Stand 1 (Entwurf) mit R-01…R-10, AC-01…AC-12, 14 Aufgaben in 3 Phasen/Sessions.
- OF-01 durch Ralf entschieden: Tool-Budget 100, `shape_binder` als eigenes Tool; R-10/AC-12 im Sprint `freecad-buddy-design-regelwerk` auf Spec-Stand 5 nachgezogen.

**Release-Änderungen:**
- `[skip][todos]` Reine Planung, keine Produktänderung.

**Blocker:**
- keine; Umsetzung wartet auf Spec-Freigabe durch Ralf.

**Erkenntnisse:**
- Anlass Lüfterrahmen v2: Lochabstand musste in drei Skizzen dupliziert werden, das Maß zwischen den Löchern entstand nur über Radius-Constraint + 180°-Muster.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: Referenzmodell und Tool-Budget in `98-architecture-update.md` notiert.
- Nicht übernehmen: Maße des Lüfterrahmens.

**Validierung:**
- nicht ausgeführt – Planungssession.
- Browser-/manuelle Abnahme: keine in dieser Session.

**Nächste Session:**
- Nach Spec-Freigabe: S1, Einstieg #1.1 (Spike FreeCAD 26.3).
- Relevant: `buddy_core/sketch/*`, `src/buddy_server/tools.py`.

---

*(Einträge in umgekehrt chronologischer Reihenfolge — neueste oben.)*
