# 🔍 Sprint-Review — FreeCAD Buddy: Design-Stream mit Storepoints

> Bereich: `da5701a..HEAD` (HEAD = `675e72c`) │ Domäne: `core` + `bridge` + `server` (Feature-Durchstich, vor den Sprint-Regeln aus `77ea07a` gestartet) │ Review-Session: 2026-09-30 │ Abnahme: 2026-09-30 durch Ralf

Regeln: [README → Review-Gate](../../README.md#review-gate-sprint-abnahme). Review in einer frischen Session; jede Datei wird vollständig gelesen. Code-Dateien hat der Reviewer selbst gelesen, die Doku-Dateien ein zweiter Reviewer-Agent. Doku-Befunde hat ein Fixer-Agent behoben, der Reviewer hat die Änderungen im Diff geprüft. Dateien, die nur den PartDesign-Sprint betreffen (`TODOs/2-sprints-aktiv/freecad-buddy-partdesign/**`), stehen in dessen `97-review.md`.

Hinweis zum Zuschnitt: Der Sprint startete (`03e0881`) vor den Regeln zu Domäne, Größe und Komplexität (`77ea07a`). Er mischt `core`, `bridge` und `server` und hat 10 Aufgaben. Das ist bekannt und wird nicht nachgearbeitet. Komplexität und Dateigrößen wurden trotzdem nach den neuen Regeln geprüft.

## Dateiliste

Erzeugt mit `git diff --name-status da5701a..HEAD`. Jede Zeile braucht einen Status.

| Datei | Änderung (A/M/D/R) | Bewertung (Korrektheit, Komplexität, Lesbarkeit, Tests/Doku) | Status |
|---|---|---|---|
| `addon/FreeCADBuddy/buddy_core/stream.py` | A | **Korrektheit, hoch (R-01):** Die Aufzeichnung erkannte mutierende Aufrufe an `UndoCount`. Bei vollem Undo-Stack (20) wächst der Zähler nicht mehr, und ab dann fehlte jeder Aufruf im Stream, ohne Meldung (Probe: 26 Aufrufe, 21 Einträge). **Korrektheit, hoch (R-02):** `reconcile` glich nur über Undo-Namen ab, ohne die vorherige Historie zu kennen. Zwei gleichnamige Schritte (zweimal `set_parameters` auf `Box_Width`) plus Undo ließen den zurückgenommenen Eintrag stehen, und das Replay baute den falschen Wert (Probe: Stream `[60, 80]`, Dokument 60). Undo bis zum Anfang wirkte nicht. **Fix:** Zähler `transaction.commits` statt `UndoCount`. `reconcile` wählt die kürzeste Erklärung der Differenz zur zuletzt gesehenen Historie (`_difference`, `_drop`, `_seen`). Ein Dokument-Observer vergisst die Historie bei Schließen, Anlegen und `restore`. Die Grenze `min(MaxUndoSize, 20)` gilt nur für einen vollen Stack, `RedoCount` schützt bei gelöschter Historie. Polls parsen den Stream nur bei Änderung (`_align`). Fremdobjekte in der Gruppe sind keine Marker (`markers`). **Verifikation:** Ein unabhängiger Verifier-Agent hat in zwei Runden (42 Läufe gegen neue und alte Logik) weitere Fälle gefunden, die jetzt behoben und als Tests abgesichert sind: GUI-Undo gefolgt von Aufruf oder manueller Änderung, zwei GUI-Undos, voller Stack mit GUI-Undo, gleichnamiger Schritt mit GUI-Undo, `restore()` sowie ein zu hohes Undo-Limit. C901 ≤ 10, 368 Zeilen. **GUI:** G15 wurde am alten Abgleich bestätigt und bleibt nach Ralfs Entscheidung (Chat, 2026-09-30) abgenommen; keine Wiederholung. | behoben (+ 11 Regressionstests) |
| `addon/FreeCADBuddy/buddy_core/transaction.py` | M (Review-Fix) | Neuer Zähler `commits` je Dokument nach `commitTransaction` (Fix R-01). | behoben |
| `addon/FreeCADBuddy/buddy_bridge/registry.py` | M | **Korrektheit, hoch (R-03):** `execute` rief `stream.snapshot/record` auch für Methoden mit `main_thread=False` auf (`system.ping`, `addons.install_status`). Damit wurden FreeCAD-Dokumente aus dem Verbindungs-Thread gelesen und bei `reconcile` beschrieben, was in der GUI nicht thread-sicher ist. **Fix:** Der Stream wird nur auf dem Hauptthread berührt; `_method` fasst die Nachschlage-Logik zusammen. Die doppelte Signaturprüfung in `invoke`/`execute` bleibt bewusst (frühe Ablehnung vor dem Hauptthread-Wechsel). | behoben (+ Test) |
| `addon/FreeCADBuddy/buddy_bridge/replay.py` | A | Allowlist `REPLAYABLE` ist solide (Stream gilt als Fremddaten). **Komplexität:** `replay` C901 12, neu im Sprint (Backlog E-08). **Fix:** Schritt-Ausführung in `_run_step` ausgelagert, doppeltes `sorted` entfernt; jetzt ≤ 10. | behoben |
| `addon/FreeCADBuddy/buddy_bridge/methods.py` | M | `replay` hing an der globalen `_active_registry` (zuletzt gebaute Registry, nicht die aufrufende). **Fix:** `build_registry` bindet die eigene Registry per `functools.partial`; der Wrapper und die globale Variable sind entfallen. | behoben |
| `addon/FreeCADBuddy/buddy_bridge/__init__.py` | M | Version 0.4.0 | ok |
| `addon/FreeCADBuddy/buddy_core/__init__.py` | M | Version 0.4.0 | ok |
| `addon/FreeCADBuddy/buddy_core/documents.py` | M | `_node` las `Position`/`Feature` an jedem Gruppenkind. Ein vom Nutzer in die Gruppe gezogenes Objekt ließ `get_model_tree` mit `AttributeError` scheitern. `steps` zählte rohe Zeilen samt beschädigter. **Fix:** `stream.markers`, `len(stream.entries(...))`. Bekannt und außerhalb des Sprints: `has_unsaved_changes` headless über `UndoCount` hat dieselbe 20-Schritte-Grenze (→ E-35). | behoben / → Eingang E-35 |
| `src/buddy_server/tools/session.py` | M | Tool-Texte ungenau: `replay` nannte nur Python und Addons als übersprungen, `storepoint` ohne „◆“. Server-Timeout `replay` 600 s = Bridge-Timeout, Konvention ist Server länger (120 → 150). **Komplexität:** `register` 10 → 13 (E-07). **Fix:** Texte korrigiert, Timeout 630 s, `document`-Dispatch als Tabelle, `register` wieder ≤ 10. | behoben |
| `src/buddy_server/__init__.py` | M | Version 0.4.0 | ok |
| `src/buddy_server/design_rules.py` | M | Regel „Storepoint an jedem Meilenstein“ inhaltlich gut. **Dateigröße:** 429 → 436 Zeilen (über 400 und gewachsen; die Regel galt beim Commit noch nicht). | → Eingang E-33 |
| `tests/bridge/test_stream.py` | A | Gute Szenarien (Aufzeichnung, Undo, `manual_edit`, Persistenz, Replay, Allowlist). **Fake-Assertion:** `assert … or True` (Z. 194) prüfte nichts. **Fix:** entfernt; neue Tests für R-01, R-02, R-03 und Fremdobjekte in der Gruppe. | behoben |
| `tests/server/test_e2e.py` | M | E2E über MCP für storepoint → list → replay, passend. | ok |
| `tools/gen_tool_docs.py` | M | Beispiele für die drei neuen Tools. | ok |
| `tools/gui_checks.py` | A | Übergangsskript für G13/G14 (E-27), klar begrenzt, läuft nur mit `execute_python`-Freigabe. `_document`/`_tree_items` werfen bei falschem Namen `StopIteration`/`KeyError`, für ein Prüfskript akzeptabel. | ok |
| `pyproject.toml` | M | Version 0.4.0 | ok |
| `uv.lock` | M | Version 0.4.0 | ok |
| `docs/tools/session.md` | M (generiert) | Nach dem Fix an `tools/session.py` neu generiert; `gen_tool_docs.py --check` grün. | behoben |
| `docs/tools.md` | M (generiert) | aktuell (60 Tools) | ok |
| `docs/architecture.md` | M | Design-Stream-Abschnitt korrekt. Stand-Zeile (0.2.0), Layout-Tabelle, Namensräume, Timeouts und Versionswarnung waren veraltet oder fehlten. | behoben |
| `docs/acceptance.md` | M | G13 bis G15 korrekt belegt. Der Kopfsatz widersprach der agentengestützten Prüfung, die Reihenfolge war unsortiert. | behoben |
| `CHANGELOG.md` | M | korrekt; Datum 2026-09-29 beim Release prüfen | ok |
| `README.md` | M | korrekt (60 Tools, Design-Stream) | ok |
| `TODOs/0-vorlagen/backlog-domain-index.template.md` | M | Statuslegende weicht leicht von der README ab (🔵, ✅) | → Eingang E-37 |
| `TODOs/0-vorlagen/sprint-00-index.template.md` | M | ok | ok |
| `TODOs/0-vorlagen/sprint-review.template.md` | A | Kopfzeile nannte `<End-Commit>` statt `HEAD` | behoben |
| `TODOs/0-vorlagen/sprint-session-log.template.md` | M | ok (`Komplexität:`) | ok |
| `TODOs/1-backlog/freecad-buddy/00-index.md` | M | Eingang konsistent; E-08 durch den Review-Fix erledigt, E-01-Zahl angepasst, neue Einträge E-29 bis E-37 | behoben |
| `TODOs/1-backlog/freecad-buddy/design-stream-storepoints.md` | M | AC-Checkboxen und Nachweise nicht gepflegt, geplanter Server-Weg ohne Vermerk „abgelöst“, A-05-Fallback und Addon-Vorabprüfung ohne Scope-Entscheidung | behoben / → Eingang E-34 |
| `TODOs/2-sprints-aktiv/freecad-buddy-storepoints/00-index.md` | A | veraltete Aussagen (G13, `NEVER_REPLAYED`, Prüfebene, Session 1b) | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-storepoints/01-aufzeichnung.md` | A | Plan-Namen (`compact`, `undo_count`) und AC-07-Status veraltet | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-storepoints/02-storepoints-baum.md` | A | Testpfad `tests/core` statt `tests/bridge` | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-storepoints/03-replay.md` | A | Pfad `buddy_bridge/stream.py`, Skip-Beschreibung vor der Allowlist | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-storepoints/04-server-doku-abschluss.md` | A | Session-Bezeichnung, historische Testzahlen | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-storepoints/98-architecture-update.md` | A | Sicherheits-Delta vor der Allowlist, Anker, Datum | behoben |
| `TODOs/2-sprints-aktiv/freecad-buddy-storepoints/99-session-log.md` | A | Zeile `Komplexität:` fehlte in drei Sessions, Release-Änderungen für `bae72c0`, `675e72c` und `77ea07a` fehlten | behoben |
| `TODOs/README.md` | M | `97-review.md` fehlte unter den Pflichtbestandteilen. Tippfehler außerhalb des Diffs (Eingang) | behoben / → Eingang E-37 |
| `TODOs/master-todo.md` | M | ok | ok |
| `TODOs/roadmap.md` | A | R0-Bereich `da5701a..0b8025f` statt `..HEAD`, Datum | behoben |

## Werkzeug-Befunde

| Quelle | Befund | Datei:Zeile | Status |
|---|---|---|---|
| Reviewer (Probe) | R-01: Aufzeichnung stoppt bei vollem Undo-Stack | `buddy_core/stream.py` `record` | behoben |
| Reviewer (Probe) | R-02: `reconcile` behält zurückgenommene gleichnamige Schritte, Undo bis zum Anfang wirkt nicht | `buddy_core/stream.py` `reconcile` | behoben |
| Reviewer | R-03: Stream-Zugriff aus dem Verbindungs-Thread | `buddy_bridge/registry.py` `execute` | behoben |
| Verifier (Runde 1) | Neuer Abgleich erkennt kein GUI-Undo, wenn die Historie nicht kürzer wird (Abschneiden fälschlich angenommen); RedoCount-Guard nach Abzug von `keep` | `buddy_core/stream.py` `_difference`, `_align` | behoben |
| Verifier (Runde 2) | `restore()` (gleiches Dokument-Objekt, leere Historie) verwarf gespeicherte Einträge; ein zu hohes Undo-Limit zerstört den Stream; gleichnamiger Schritt mit GUI-Undo und Aufruf blieb stehen | `buddy_core/stream.py` | behoben (Observer, `min(…, 20)`, `least_added`) |
| `/code-review high` | Fremdobjekt in der Gruppe `Storepoints` lässt `get_model_tree` scheitern | `buddy_core/documents.py:201` | behoben |
| `/code-review high` | Fehler in `stream.record` meldet einen erfolgreichen Aufruf als Fehler (Retry → Doppel-Feature) | `buddy_bridge/registry.py:86` | → Eingang E-29 |
| `/code-review high` | `replay` über globale `_active_registry` | `buddy_bridge/methods.py:99` | behoben |
| `/code-review high` | Stream wird je Aufruf komplett geparst und bei `append` neu geschrieben (O(n)) | `buddy_core/stream.py:95` | → Eingang E-30 |
| `/code-review high` | Signatur doppelt geprüft (`invoke` und `execute`) | `buddy_bridge/registry.py:93` | verworfen (frühe Ablehnung vor dem Hauptthread-Wechsel ist gewollt) |
| `/code-review high` | `NOT_RECORDED` seit dem Commit-Zähler größtenteils redundant | `buddy_bridge/registry.py:24` | → Eingang E-31 |
| `/code-review high` | Thread-Guard in `execute` ohne Test | `tests/bridge/test_stream.py` | behoben |
| `/code-review high` | Storepoint verlinkt nach Umbenennen das falsche Feature | `buddy_core/stream.py` `_last_created` | → Eingang E-32 |
| `/code-review high` | `_seen` hält geschlossene Dokument-Objekte | `buddy_core/stream.py` `_seen` | behoben (Observer entfernt den Eintrag beim Schließen; `_seen` hält keine Dokument-Objekte mehr) |
| `/simplify` (Effizienz) | Polls (`record` mit `store=False`) parsen den Stream, obwohl sich die Undo-Historie nicht geändert hat | `buddy_core/stream.py` `reconcile` | behoben (`_align` parst nur bei Änderung) |
| `/simplify` (Effizienz) | `_node` parst den Stream nur für die Schrittzahl | `buddy_core/documents.py:201` | verworfen (korrekte Zahl ohne beschädigte Zeilen ist gewollt; Gesamtkosten → E-30) |
| `/simplify` (Effizienz) | `list_storepoints` sucht jeden Marker per `getObjectsByLabel` | `buddy_core/stream.py` `list_storepoints` | verworfen (bei wenigen Storepoints nicht messbar) |
| `/simplify` (Effizienz) | `_seen` und `commits` werden nie bereinigt | `buddy_core/stream.py`, `transaction.py` | `_seen` behoben (Observer); `commits` verworfen (eine Zahl je Dokumentname) |
| `/simplify` (Altitude) | Präfixlisten `NOT_RECORDED`/`REPLAYABLE` getrennt von `METHODS`, Aufzeichnung fail-open | `buddy_bridge/registry.py:24`, `replay.py:19` | → Eingang E-31 |
| `/simplify` (Altitude) | Sonderfall `fn is replaying.replay` in `build_registry` | `buddy_bridge/methods.py` | verworfen (ein Nutzer; generisches Flag kommt mit E-31) |
| `/simplify` (Altitude/Reuse) | Lazy-Import `resolve_document` in `stream.py` wegen des Zyklus `documents` ↔ `stream` | `buddy_core/stream.py` | verworfen (bewusste Auflösung des Zyklus, kein Verhaltensgewinn) |
| `/simplify` (Altitude) | `registry.function()` nur für die Signatur-Abfrage im Replay | `buddy_bridge/replay.py` `_run_step` | verworfen (kommt mit E-31) |
| `/simplify` (Vereinfachung) | Signaturprüfung doppelt ausformuliert | `buddy_bridge/registry.py` | behoben (`_check_params`) |
| `/simplify` (Vereinfachung) | `storepoints(items)` in `storepoint()` zweimal berechnet | `buddy_core/stream.py` `storepoint` | behoben |
| `/simplify` (Vereinfachung) | `claimed()` ist ein Wrapper mit einem Aufrufer | `buddy_core/stream.py` | behoben (entfernt, `documents` nutzt `markers`) |
| `/simplify` (Vereinfachung) | `StorepointViewProvider.attach`/`claimChildren` sind entbehrlich | `buddy_core/stream.py` | verworfen (GUI-Verhalten, bräuchte eine neue G14-Prüfung mit Freigabe) |
| `/simplify` (Reuse) | `gui_checks._document` baut `resolve_document` nach; PySide6-Fallback weicht von der Konvention ab | `tools/gui_checks.py:23` | verworfen (Übergangsskript, nur in der GUI prüfbar; entfällt mit E-27) |

## Komplexität

- `C901`-Befunde vorher/nachher: 16 (`da5701a`) → 18 (`675e72c`, neu: `replay.replay` 12, `tools/session.register` 13) → 16 nach den Review-Fixes.
- Dateien über 400 Zeilen, die im Sprint gewachsen sind: `src/buddy_server/design_rules.py` 429 → 436 (→ E-33). `buddy_core/stream.py` hat 368 Zeilen.

## Ergebnis

- [x] Jede Datei der Liste hat einen Status.
- [x] Befunde im Sprint-Umfang behoben, `uv run poe check` danach grün (2026-09-30: ruff, pyright, 186 + 269 Tests).
- [x] Übrige Befunde im Backlog-Eingang eingetragen.
- [x] Abnahme durch Ralf im Chat bestätigt: 2026-09-30, „Abnahme erteilt“ (ohne GUI-Wiederholung von G15)
