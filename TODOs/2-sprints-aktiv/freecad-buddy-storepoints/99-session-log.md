# 📓 Session-Log

Chronologisches Protokoll aller Arbeitssessions. Nach jeder Session einen neuen Eintrag oben anlegen.
`Release-Änderungen` in derselben Session pflegen; sie bilden später die Grundlage für CHANGELOG/Release-Notes. Interne Änderungen bewusst mit `skip` markieren.

---

## Session 2 — 2026-09-30 (GUI-Abnahme G14/G15)

**Ziel:** #4.3 GUI-Anteil; Ralf überträgt die Führung an den Agenten („Agent führt, ich schaue“) und prüft selbst in der GUI.

**Erledigt:**
- Aufbau über MCP (`Abnahme_Storepoints`: Platte mit Mulde, Storepoints `Grundkörper`/`Mulde`), sauberer `replay` als Gegenprobe (Baum, Undo-Liste, Screenshot identisch).
- G14: Ralf bestätigt Rauten-Icon, Doppelklick markiert das Feature, „◆ Storepoint 1: Grundkörper“ in der Beschreibungsspalte. Hover-Tooltip gibt es nicht (FreeCAD zeigt `Label2` nur in der Spalte); Ralf entscheidet: Katalogtext korrigieren (`docs/acceptance.md`, Phase 2, Ticket).
- G15, 1. Lauf ❌: eine Skizzenbearbeitung in der GUI sind 5 Transaktionen (`Edit`, `Edit`, `Drag Constraint`, `Modify sketch constraints`, `Sketch recompute`); weil jeder Bridge-Aufruf (auch Lesezugriffe) abgleicht, entstanden 5 `manual_edit`-Einträge mit überlappenden Namen und 5 Replay-Warnungen.
- Bugfix `0b8025f`: `reconcile` sucht die Undo-Namen eines vermerkten `manual_edit` ab dem Cursor und übernimmt direkt folgende GUI-Transaktionen in denselben Eintrag; Regressionstest `test_gui_transactions_between_polls_stay_one_manual_edit` (schlägt ohne Fix fehl).
- G15, 2. Lauf ✅ (`Abnahme_G15`, nach Neustart von FreeCAD): `manual_edits` = 1 vor und nach `pad`, `replay("Fuß")` warnt genau einmal an Schritt 9; Replay-Volumen 16659,2 mm³ (Radius 3) gegenüber Original 16683,3 mm³ (Ralfs Radius) – die manuelle Änderung ist wie erwartet nicht im Stream.
- `docs/architecture.md`: Zusammenfassung aufeinanderfolgender GUI-Transaktionen ergänzt.

**Release-Änderungen:**
- `[bugfix][core]` Eine GUI-Bearbeitung aus mehreren Transaktionen zählt als ein `manual_edit`; das Replay warnt einmal statt je Transaktion.
- `[doc][docs]` Abnahme-Katalog G14 (Beschreibungsspalte statt Tooltip), G15 präzisiert; Architektur-Abschnitt Design-Stream.

**Blocker:**
- keine; nächster Schritt Review-Gate (Agent, danach Abnahme durch Ralf).

**Erkenntnisse:**
- Lesezugriffe gleichen den Stream ab; manuelle GUI-Arbeit wird also in Stücken erfasst, die zusammengeführt werden müssen. Headless-Tests mit einer einzigen Fremdtransaktion haben das nicht gezeigt.
- Solange in FreeCAD ein Task-Panel offen ist, lehnt die Bridge mit `[busy_user_transaction]` ab – bei GUI-Abnahmen den Nutzer zuerst schließen lassen.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: ein Satz im Abschnitt Design-Stream (Abgleich mit der Undo-Historie).
- Nicht übernehmen: Namen der Sketcher-Transaktionen.

**Komplexität:** unverändert (`ruff --select C901` auf `stream.py` ohne Befund, 334 Zeilen).

**Validierung:**
- `uv run poe test-core`: 258 passed (neuer Test ohne Fix rot).
- `ruff check`/`ruff format --check` auf den geänderten Dateien sauber.
- Browser-/manuelle Abnahme: G14 und G15 durch Ralf bestätigt (Chat, 2026-09-30).

**Nächste Session:**
- S3: Review-Gate in frischer Session (`97-review.md`, `git diff --name-status da5701a..HEAD`), Abnahme durch Ralf, dann Verschieben nach `3-sprints-erledigt/2026-09-freecad-buddy-storepoints/`, Ticket, Backlog-Index, `master-todo.md`, Roadmap R0.

---

## Session 1b — 2026-09-30 (Sicherheitsbefund Replay)

**Ziel:** Befund „allowlist-semantic-escape“ der Push-Sicherheitsprüfung in `buddy_bridge/replay.py` beheben.

**Erledigt:**
- Replay spielt nur noch Modellier-Methoden ab (Allowlist `REPLAYABLE`), `assembly.insert_step` (Pfad aus dem Stream) ausgenommen; alles andere wird übersprungen und gemeldet. Vorher hätte eine präparierte FCStd `document.save`, `document.open` oder `print.export` mit fremden Pfaden abspielen können.
- `MethodRegistry.execute` prüft Parameter aus dem Stream gegen die Signatur wie eine RPC-Anfrage.
- `NOT_RECORDED` explizit statt Präfix `document.`: `document.delete` gehört zum Design und wird jetzt aufgezeichnet.
- Test: präparierter `document.save`-Eintrag wird übersprungen, keine Datei entsteht.
- Erneute Sicherheitsprüfung (Subagent, alle replaybaren Namespaces auf Datei-, Netz-, Subprozess- und Code-Senken verfolgt): kein Befund über der Schwelle. Zwei Beobachtungen umgesetzt: `assembly.insert_step` wird nicht mehr aufgezeichnet (lokaler Pfad in der FCStd), beschädigte Stream-Zeilen werden verworfen statt jeden Aufruf scheitern zu lassen (Test `test_damaged_stream_lines_are_ignored`).

**Release-Änderungen:**
- `[bugfix][bridge]` Replay führt nur Modellier-Methoden aus; `document.delete` wird aufgezeichnet.

**Blocker:**
- unverändert #4.3 (GUI-Abnahme, Ralf).

**Erkenntnisse:**
- Denylists an Datengrenzen sind ein Fehler; der Stream ist Fremddaten, sobald eine Datei geöffnet wird.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: Abschnitt Design-Stream (Allowlist, Aufzeichnungsliste) aktualisiert.
- Nicht übernehmen: —

**Validierung:**
- `run-core-tests -- tests/bridge/test_stream.py`: 8 passed (neu: präparierter `document.save`-Eintrag, `document.delete`, beschädigte Zeilen).
- `uv run poe check`: ruff, pyright 0 Fehler, 186 Projekt-Python-Tests, 257 FreeCAD-Python-Tests.
- Browser-/manuelle Abnahme: unverändert offen.

**Nächste Session:**
- unverändert S2.

---

## Session 1 — 2026-09-29 (Umsetzung Phase 1–4)

**Ziel:** #1.1 bis #4.2, #4.3 ohne GUI-Anteil.

**Erledigt:**
- #1.1/#1.2 `buddy_core/stream.py` (Gruppe `Storepoints` mit `Stream`-Property, `record`, `reconcile`, `snapshot`), `MethodRegistry.execute` als einziger Ausführungsweg mit Aufzeichnung, `NOT_RECORDED`-Liste; #1.3 Marker unter der Gruppe im Modellbaum, Gruppe zeigt `steps` und `storepoints`.
- #2.1–#2.3 `storepoint` (Marker mit `Feature`, `Position`, `Created`, `Steps`, `Label2` am Feature, optional Snapshot-Kopie), `list_storepoints`, `StorepointViewProvider` (Icon, Doppelklick markiert das Feature; nur mit GUI gesetzt).
- #3.1 `buddy_bridge/replay.py`: neues Dokument, Schritte über `registry.execute`, Skips für `python.*`/`addons.install`, Warnungen bei `manual_edit` und fremder Version, Abbruch mit Schrittnummer; `stream.replay` mit Timeout 600 s; `_active_registry` in `methods.py`.
- #4.1 Server-Tools und E2E; #4.2 Regelwerk, Architektur, README, CHANGELOG 0.4.0, Version, G14/G15; #4.3 `poe check` grün.

**Release-Änderungen:**
- `[feature][core]` Design-Stream im Dokument, Storepoints mit Marker und Beschreibung, `list_storepoints`.
- `[feature][bridge]` Aufzeichnung in der Registry, Replay bis zu einem Storepoint.
- `[feature][server]` Tools `storepoint`, `list_storepoints`, `replay` (Session).
- `[doc][docs]` Architektur-Abschnitt Design-Stream, README, CHANGELOG, Abnahme-Katalog G14/G15, Regelwerk `workflow`.
- `[misc][release]` Version 0.4.0.

**Blocker:**
- #4.3 GUI-Abnahme G14/G15 — wartet auf Ralf.

**Erkenntnisse:**
- Ein bereits vermerkter `manual_edit` muss beim nächsten Abgleich den Cursor über seine Undo-Namen schieben, sonst entsteht er doppelt (Test hat es gefangen).
- Beim Replay muss `snapshot` des Storepoint-Aufrufs auf `false` gesetzt werden, die Kopie hat noch keine Datei.
- Nach Ralfs Serverstopp ließ sich die venv wieder synchronisieren; die Tests liefen danach ohne `--no-sync`.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: alle vier Deltas übernommen (98 auf „übernommen“ mit Abschlussnotiz).
- Nicht übernehmen: Property-Namen der Marker, XPM-Icon.

**Validierung:**
- `run-core-tests -- tests/bridge/test_stream.py`: 6 passed.
- `uv run poe check`: ruff ✅, ruff format ✅, pyright 0 Fehler ✅, 186 Projekt-Python-Tests ✅ (inkl. E2E `test_storepoints_and_replay_over_mcp`), 255 FreeCAD-Python-Tests ✅.
- Browser-/manuelle Abnahme: G14/G15 offen, keine Prüfung ohne Freigabe.

**Nächste Session:**
- S2: G14/G15 nach Ralfs Entscheidung, dann Definition of Done, Sprint nach `3-sprints-erledigt/2026-09-freecad-buddy-storepoints/`, Ticket und Backlog-Index abschließen.
- Dateien: `00-index.md`, `04-server-doku-abschluss.md`, `docs/acceptance.md`.
- Architektur-Deltas: keine offen.

---

## Session 0 — 2026-09-29 (Planung)

**Ziel:** Sprint aus dem Ticket `design-stream-storepoints.md` formen.

**Erledigt:**
- Sprint-Ordner mit Index, vier Phasen (10 Aufgaben), Architektur-Update und Session-Log angelegt.
- Spec-Stand 1 durch Ralf im Chat freigegeben („ok, dann umsetzen“), Annahmen OF-01 bis OF-05 als Entscheidungen übernommen.

**Release-Änderungen:**
- `[skip][todos]` Planung, keine Produktänderung.

**Blocker:**
- keine

**Erkenntnisse:**
- keine

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: vier geplante Deltas in `98-architecture-update.md`.
- Nicht übernehmen: Property-Namen der Marker.

**Validierung:**
- nicht ausgeführt (nur Planungsartefakte).
- Browser-/manuelle Abnahme: keine; G14/G15 warten auf Freigabe in S3.

**Nächste Session:**
- S1: #1.1 `stream.py`, #1.2 Registry-Hook, #1.3 Modellbaum.
- Dateien: `addon/FreeCADBuddy/buddy_bridge/registry.py`, `addon/FreeCADBuddy/buddy_core/stream.py`, `tests/bridge/test_stream.py`, `tests/core/test_stream.py`.
- Architektur-Deltas: Design-Stream in 98.

---

*(Einträge in umgekehrt chronologischer Reihenfolge — neueste oben.)*
