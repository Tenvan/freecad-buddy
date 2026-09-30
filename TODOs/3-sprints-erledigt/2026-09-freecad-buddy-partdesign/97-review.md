# 🔍 Sprint-Review — FreeCAD Buddy: PartDesign-Vollständigkeit

> Bereich: `4fd92f8..da5701a` plus die Sprint-eigenen Dateien aus `932f976` │ Domäne: `core` + `server` (Feature-Durchstich, vor den Sprint-Regeln aus `77ea07a` gestartet) │ Review-Session: 2026-09-30 │ Abnahme: 2026-09-30 durch Ralf

Regeln: [README → Review-Gate](../../README.md#review-gate-sprint-abnahme). Review in einer frischen Session, jede Datei vollständig gelesen: Code und Tests durch einen Reviewer-Agenten (mit Probe-Tests in temporären Dokumenten), Doku und TODOs durch einen zweiten Reviewer-Agenten. Die Doku-Fixes hat ein Fixer-Agent umgesetzt, die Code-Fixes der Reviewer. Der Reviewer hat alle Änderungen im Diff geprüft. `..HEAD` statt `..da5701a` würde die Dateien des Storepoints-Sprints mitziehen; die gemeinsam geänderten Dateien sind dort reviewt ([`97-review.md`](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/97-review.md)).

Hinweis zum Zuschnitt: Der Sprint hat 16 Aufgaben, mischt `core` und `server` und lief vor den Regeln zu Domäne, Größe und Komplexität. Das ist bekannt und wird nicht nachgearbeitet.

## Dateiliste

Erzeugt mit `git diff --name-status 4fd92f8..da5701a`. Jede Zeile braucht einen Status.

| Datei | Änderung (A/M/D/R) | Bewertung (Korrektheit, Komplexität, Lesbarkeit, Tests/Doku) | Status |
|---|---|---|---|
| `addon/FreeCADBuddy/buddy_core/features.py` | M | Sechs neue Tools, konsistent über `_new`/`_finish`/`transaction`; `make_helix` ersetzt die zweite Helix-Implementierung. **Korrektheit, hoch (P-01):** Zwei gegenseitige Booleans wurden angenommen und bauten einen Zyklus. `doc.RootObjects` war danach leer, das Dokument ließ sich trotzdem speichern (Probe). **Fix:** Guard `target in tool.OutListRecursive`. **P-02:** Derselbe Tool-Body doppelt übergeben wurde doppelt eingefügt. **Fix:** doppelte Tool-Bodies werden entfernt. **Komplexität:** `loft` 11 und `_primitive_props` 11 (beide neu). **Fix:** `_loft_sketches` ausgelagert, Primitive als Dispatch-Tabelle; beide jetzt ≤ 10. Prüfungen von `boolean` in `_check_boolean_tool` (C901 hatte 10 erreicht). **Größe:** 564 → 1025 Zeilen (E-05); nach den Review-Fixes wieder 1025, nicht gewachsen. Kleinere Befunde → Eingang. | behoben / → Eingang E-05, E-39, E-41, E-42, E-43, E-50 |
| `addon/FreeCADBuddy/buddy_core/select.py` | M | `faces:vertical` knapp und richtig. Der Docstring erklärt `vertical` nur für Kanten. `_face_filter` C901 11 → 12 | → Eingang E-43, E-06 |
| `addon/FreeCADBuddy/buddy_core/sketch/model.py` | M | `plane_support` mit Map-Modus sauber, LCS als Skizzenebene getestet | ok |
| `addon/FreeCADBuddy/buddy_core/thread.py` | M | nutzt `features.make_helix`; Label, Anzeigestil und Modus unverändert (`_new` setzt den Stil) | ok |
| `addon/FreeCADBuddy/buddy_core/compat.py` | M | `REQUIRED_TYPES` um 24 Typen ergänzt, vollständig | ok |
| `addon/FreeCADBuddy/buddy_bridge/methods.py` | M | sechs Methoden registriert | ok |
| `addon/FreeCADBuddy/buddy_bridge/__init__.py` | M | Version 0.3.0 | ok |
| `addon/FreeCADBuddy/buddy_core/__init__.py` | M | Version 0.3.0 | ok |
| `src/buddy_server/__init__.py` | M | Version 0.3.0 | ok |
| `pyproject.toml` | M | Version 0.3.0 | ok |
| `uv.lock` | M | Version 0.3.0 | ok |
| `src/buddy_server/tools/feature.py` | M | Schemas passen zum Core. **Sprache:** Drei deutsche MCP-Texte (`Skizzen-Label`, `Nut (Groove)`, `ISO-Metrisch`) widersprachen A-10. **Fix:** übersetzt, Doku neu generiert. Dazu `Body-Label` (4×). **Komplexität:** `register` 12 → 17 (E-07). **Größe:** 256 → 406 Zeilen, über 400. **Fix:** fillet/chamfer kompakt wie die übrigen Tools, jetzt 394 Zeilen. | behoben / → Eingang E-07 |
| `src/buddy_server/tools/reference.py` | M | `datum`-Schema passt | ok |
| `src/buddy_server/tools/base.py` | M | Selektor-Hilfe um `faces:vertical` ergänzt | ok |
| `src/buddy_server/design_rules.py` | M | Sechs Regeln mit `requires`, gut lesbar. 395 → 429 Zeilen, über 400 (E-33) | → Eingang E-33 |
| `tests/core/test_features.py` | M | Formel-Tests mit Parameteränderung und Undo, keine Stub-Tests. Negativfälle fehlten. **Fix:** „already used by a boolean“, Boolean-Zyklus und doppelter Tool-Body jetzt getestet. Übrige Lücken (8 × subtraktiv, Datum-Achse gegen Body-Achse, `unsupported`, Pocket-Taper-Vorzeichen) → Eingang | behoben / → Eingang E-40 |
| `tests/server/test_design_rules.py` | M | Die Erweiterung auf Parameter- und Enum-Namen schwächt `test_rules_only_name_registered_tools` | → Eingang E-45 |
| `tools/gen_tool_docs.py` | M | Beispiele vollständig | ok |
| `docs/tools/feature.md` | M (generiert) | nach dem Sprachfix neu generiert, `--check` grün | behoben |
| `docs/tools/reference.md` | M (generiert) | aktuell | ok |
| `docs/tools.md` | M (generiert) | aktuell; Kurzbeschreibungen mitten im Satz abgeschnitten | → Eingang E-49 |
| `docs/architecture.md` | M | sieben Deltas vorhanden; „`Hole.ModelThread` seit 1.0“ war nur für 26.3 belegt | behoben |
| `docs/acceptance.md` | M | G13 korrekt | ok |
| `CHANGELOG.md` | M | 0.3.0 korrekt; „jedes Standard-Werkzeug“ ohne die Ausnahmen aus dem Ticket | behoben |
| `README.md` | M | gleiche Überzeichnung wie im CHANGELOG | behoben |
| `TODOs/1-backlog/freecad-buddy/00-index.md` | M | Sprint-Änderungen korrekt; neue Eingangszeilen E-39 bis E-50 (E-38 durch den Review-Fix hinfällig) | behoben |
| `TODOs/1-backlog/freecad-buddy/design-stream-storepoints.md` | A | im Storepoints-Review behandelt | ok |
| `TODOs/1-backlog/freecad-buddy/partdesign-vollstaendigkeit.md` | M | AC-Checkboxen und Nachweise nicht nachgeführt, OF-02/OF-03 als ungeklärt geführt | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-partdesign/00-index.md` | A | AC-03 und AC-06 stärker formuliert als belegt (jetzt „teilweise erfüllt“ mit Folgetests E-40), AC-10 genauer, OF-03 präzisiert, Entscheidung `draft` ohne `pull_direction` ergänzt | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-partdesign/01-spikes-fundament.md` | A | Spike-Ergebnisse vollständig; „25 Typen“ statt 24 | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-partdesign/02-additive-features.md` | A | Abnahmetabelle veraltet, Loft-Vorprüfung falsch beschrieben | behoben (Härtung → E-39) |
| `TODOs/2-sprints-aktiv/freecad-buddy-partdesign/03-referenzen-bestand.md` | A | korrekt; das Vorzeichen des Pocket-Tapers ist nicht belegt | → Eingang E-40 |
| `TODOs/2-sprints-aktiv/freecad-buddy-partdesign/04-boolean-draft.md` | A | korrekt | ok |
| `TODOs/2-sprints-aktiv/freecad-buddy-partdesign/05-regelwerk-doku-abschluss.md` | A | Undo-Aussage zu breit | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-partdesign/98-architecture-update.md` | A | sieben Deltas übernommen | ok |
| `TODOs/2-sprints-aktiv/freecad-buddy-partdesign/99-session-log.md` | A | Release-Zeilen für alle Commits vorhanden; „25 Typen“; `Komplexität:` fehlt (Regel kam später, nur Hinweis) | behoben |
| `TODOs/master-todo.md` | M | konsistent | ok |

## Werkzeug-Befunde

| Quelle | Befund | Datei:Zeile | Status |
|---|---|---|---|
| Reviewer-Agent (Probe) | P-01: Boolean-Zyklus bei zwei gegenseitigen Booleans | `buddy_core/features.py` `boolean` | behoben (+ Test) |
| `/code-review high` | P-02: derselbe Tool-Body doppelt eingefügt | `buddy_core/features.py` `boolean` | behoben (+ Test) |
| `/code-review high` | `draft` mit LCS als neutraler Ebene scheitert erst beim Recompute | `buddy_core/features.py` `draft` | → Eingang E-42 |
| `/code-review high` | `primitive` prüft Maße nicht (> 0, unbekannte Schlüssel) | `buddy_core/features.py` `primitive` | → Eingang E-41 |
| `/code-review high` | Regel-Test akzeptiert jeden Parameternamen | `tests/server/test_design_rules.py:49` | → Eingang E-45 |
| `/code-review high` | `loft`-Vorprüfung lässt offene Wires und nicht benachbarte Ebenen durch | `buddy_core/features.py` `_loft_sketches` | → Eingang E-39 |
| `/code-review high` | `datum` nutzt nicht `_new` | `buddy_core/features.py` `datum` | verworfen (Datums brauchen keinen Solid-Anzeigestil) |
| `/code-review high` | C901 von `tools/feature.register` und `_face_filter` gewachsen | `src/buddy_server/tools/feature.py:15` | → Eingang E-07, E-06 |
| `/simplify` (Altitude) | `boolean` steht bei C901 10, jede weitere Prüfung bricht die Grenze | `buddy_core/features.py` `boolean` | behoben (`_check_boolean_tool`) |
| `/simplify` (Vereinfachung) | fillet/chamfer als einzige Tools ausformatiert; `Body-Label` deutsch | `src/buddy_server/tools/feature.py:236` | behoben (394 Zeilen) |
| `/simplify` (Vereinfachung/Effizienz) | gleiches Gerüst in pad, pocket, revolve, sweep, loft, primitive; unnötige Volumenberechnung bei additiven Features | `buddy_core/features.py` | → Eingang E-50 (Umbau mit E-05) |
| `/simplify` (Reuse) | `datum_plane` baut `datum`/`_attach` nach, eigenes Achsen-Dict neben `select._AXES` | `buddy_core/features.py` | → Eingang E-50 |
| `/simplify` (Vereinfachung) | Dims doppelt in `_PRIMITIVES` und `_primitive_props`, Box/Wedge als Sonderfälle | `buddy_core/features.py` | → Eingang E-50 |
| `/simplify` (Reuse) | zwei handgeschriebene Integer-Setter neben `values.apply` | `buddy_core/features.py` | → Eingang E-50 |
| `/simplify` (Reuse) | `thread.py` dupliziert `_attach` und `_volume` | `buddy_core/thread.py` | → Eingang E-50 |
| `/simplify` (Duplikat) | `_ensure_primitive_cuts` ist fast `_ensure_cuts` | `buddy_core/features.py` | verworfen (Meldungen verschieden, Helper netto +1 Zeile) |
| `/simplify` (Vereinfachung) | `_loft_sketches` mit `pairwise` straffen | `buddy_core/features.py` | verworfen (ändert die Reihenfolge der Fehlermeldungen, Gewinn 3 Zeilen) |
| `/simplify` (Altitude) | `plane_support`-3-Tupel und LCS-Zweig passen nicht für `draft` | `sketch/model.py`, `features.py` | → Eingang E-42 |
| `/simplify` | Kein doppelter Recompute in `_finish`/`transaction` | – | kein Befund |

## Komplexität

- `C901`-Befunde vorher/nachher: 14 (`4fd92f8`) → 16 (`da5701a`, neu: `loft` 11, `_primitive_props` 11) → 14 nach den Review-Fixes. Innerhalb der Baseline gewachsen: `_face_filter` 11 → 12, `tools/feature.register` 12 → 17 (E-06, E-07).
- Dateien über 400 Zeilen, die im Sprint gewachsen sind: `buddy_core/features.py` 564 → 1025 (nach Review 1025, E-05), `src/buddy_server/tools/feature.py` 256 → 406 (nach Review 394), `src/buddy_server/design_rules.py` 395 → 429 (E-33), `tests/core/test_features.py` 276 → 642 (Tests, kein Eingang), `docs/tools/feature.md` 305 → 452 (generiert).

## Ergebnis

- [x] Jede Datei der Liste hat einen Status.
- [x] Befunde im Sprint-Umfang behoben, `uv run poe check` danach grün (2026-09-30: ruff, pyright, 186 + 269 Tests).
- [x] Übrige Befunde im Backlog-Eingang eingetragen.
- [x] Abnahme durch Ralf im Chat bestätigt: 2026-09-30, „Abnahme erteilt“
