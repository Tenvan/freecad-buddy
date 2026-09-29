# 📓 Session-Log

Chronologisches Protokoll aller Arbeitssessions. Nach jeder Session einen neuen Eintrag oben anlegen.
`Release-Änderungen` in derselben Session pflegen; sie bilden später die Grundlage für CHANGELOG/Release-Notes. Interne Änderungen bewusst mit `skip` markieren.

---

## Session 5 — 2026-09-29 (Regelwerk, Doku, Version 0.3.0)

**Ziel:** #5.1, #5.2, #5.3; #5.4 vorbereiten.

**Erledigt:**
- #5.1 Regelwerk: `features` + 5 Regeln (loft, helix/model_thread, primitive, draft/taper/up_to_first, boolean), `references` + Datum-Regel.
- #5.2 `docs/architecture.md` (alle sieben Deltas aus 98), README, `CHANGELOG.md` 0.3.0, Version 0.3.0 (pyproject, uv.lock, Server, Bridge, Core), `docs/acceptance.md` G13, `docs/tools.md` regeneriert (57 Tools).
- #5.3 Gesamtcheck grün; Regelwerk-Test erweitert (Parameter-Namen und Enum-Werte der Tools sind gültige Bezeichner in Regeltexten).
- #5.4 vorbereitet: G13 beschrieben; Prüfung wartet auf Ralfs Freigabe (Blocker im Index).

**Release-Änderungen:**
- `[doc][server]` Regelwerk-Themen `features` und `references` um die neuen Tools ergänzt.
- `[doc][docs]` Architektur, README, CHANGELOG 0.3.0, Abnahme-Katalog G13.
- `[misc][release]` Version 0.3.0.

**Blocker:**
- #5.4 GUI-Abnahme G13 — wartet auf Ralf (Freigabe oder Scope-Entscheidung).

**Erkenntnisse:**
- Nach einem Versionswechsel will `uv run` die Umgebung neu synchronisieren und scheitert an der laufenden `freecad-buddy.exe` (Ralfs MCP-Server). `uv run --no-sync` umgeht das; der Server wird nicht angefasst. Beim nächsten Serverstart synchronisiert `uv` von selbst.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: alle Deltas übernommen, 98 auf „übernommen“ mit Abschlussnotiz.
- Nicht übernehmen: nichts offen.

**Validierung:**
- `pytest tests/server/test_design_rules.py tests/server/test_language.py tests/tools`: 109 passed, nachdem `_profile_kinds` im Regelwerk-Test auch Tool-Parameter und Enum-Werte als gültige Bezeichner akzeptiert (`model_thread`, `up_to_first`).
- `uv run --no-sync poe check`: ruff ✅, ruff format ✅, pyright 0 Fehler ✅, 183 Projekt-Python-Tests ✅, 249 FreeCAD-Python-Tests ✅.
- Browser-/manuelle Abnahme: G13 offen, keine Prüfung ohne Freigabe.

**Nächste Session:**
- S6: G13 nach Ralfs Entscheidung, dann Definition of Done, Sprint nach `3-sprints-erledigt/2026-09-freecad-buddy-partdesign/`, Ticket und Backlog-Index abschließen, `master-todo.md`.
- Dateien: `00-index.md`, `05-regelwerk-doku-abschluss.md`, `docs/acceptance.md`, `TODOs/1-backlog/freecad-buddy/partdesign-vollstaendigkeit.md`.
- Architektur-Deltas: keine offen.

---

## Session 4 — 2026-09-29 (`boolean`, `draft`)

**Ziel:** #4.1 und #4.2.

**Erledigt:**
- Spike (Scratchpad): Draft-Properties (`Base`, `Angle`, `NeutralPlane`, `PullDirection`, `Reversed`); ohne Neutral Plane instabil, mit Ursprungsebene XY reproduzierbar (10° → 3336 mm³ Narrowing, `Reversed` → 4747 mm³ Widening); Pull Direction ändert nichts.
- #4.1 `boolean` (Core, Bridge, Server, Beispiel) nach Spike-Entscheidung OF-02.
- #4.2 `draft` über `_dress_up`; Face-Selektor `faces:vertical`; `SELECTOR_HELP` ergänzt.
- `docs/tools.md` regeneriert: 57 Tools (Planziel erreicht).

**Release-Änderungen:**
- `[feature][core]` `boolean`: fuse, cut, common zwischen Bodies desselben Bauteils; Werkzeug-Bodies bleiben editierbar.
- `[feature][core]` `draft`: Flächen mit Selektor um eine Neutral Plane neigen, parametrisch, Selektor wird nachgeführt.
- `[feature][core]` Selektor `faces:vertical`.
- `[feature][server]` Tools `boolean` und `draft` im Katalog (Features).

**Blocker:**
- keine

**Erkenntnisse:**
- `PartDesign::Draft` braucht eine Neutral Plane für ein deterministisches Ergebnis; Pull Direction ist bei planaren Seitenwänden überflüssig.
- `getParentGroup()` reicht, um Bodies in der Assembly-`Parts`-Gruppe zu erkennen.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: Boolean-Regel bestätigt, `faces:vertical` in der Selektor-Grammatik (98).
- Nicht übernehmen: Spike-Zahlen.

**Validierung:**
- `run-core-tests -k "draft or boolean or selectors"`: 4 passed; `pytest tests/tools tests/server/test_language.py`: 98 passed.
- `uv run poe check`: ruff ✅, ruff format ✅, pyright 0 Fehler ✅, 183 Projekt-Python-Tests ✅, 249 FreeCAD-Python-Tests ✅.
- Browser-/manuelle Abnahme: keine in S4.

**Nächste Session:**
- S5: #5.1 Regelwerk (`features`, `references`), #5.2 `docs/architecture.md` aus 98, README, CHANGELOG, Version (OF-05), #5.3 Gesamtcheck, #5.4 GUI-Abnahme AC-11 nur nach Freigabe durch Ralf.
- Dateien: `src/buddy_server/design_rules.py`, `docs/architecture.md`, `README.md`, `CHANGELOG.md`, `pyproject.toml`.
- Architektur-Deltas: alle sieben aus 98 übernehmen.

---

## Session 3 — 2026-09-29 (`datum`, Achsen, Taper, `model_thread`)

**Ziel:** #3.1 bis #3.4.

**Erledigt:**
- Spike (Scratchpad): Attachment-Modi für Point (`ObjectOrigin`), Line (`ObjectZ` = Ebenennormale), LCS (`ObjectXY`); Skizze auf LCS; Revolution, PolarPattern und Helix akzeptieren `(DatumLine, [""])`; Pad/Pocket-Typen `UpToFirst` und `TaperAngle`/`TaperAngle2`; LCS hat in 26.3 keine Kind-Ebenen.
- #3.1 `datum` (Core, Bridge, Server, Beispiel); #3.2 `_axis_reference`, `plane_support` mit Map-Mode und LCS; #3.3 Taper und `up_to_first`; #3.4 `model_thread`.
- `docs/tools.md` regeneriert: 55 Tools. Deutsche Beschreibung im `pattern`-Tool korrigiert.
- Nebenbei (kein Sprint-Umfang): Backlog-Ticket [`design-stream-storepoints.md`](../../1-backlog/freecad-buddy/design-stream-storepoints.md) aus Ralfs Idee im Chat angelegt.

**Release-Änderungen:**
- `[feature][core]` `datum`: Datum Point, Datum Line und LCS parametrisch; Datum Line als Achse für `revolve`, `helix`, `pattern(polar)`; LCS als Skizzenebene.
- `[feature][core]` `pad`/`pocket`: `taper` und Modus `up_to_first`.
- `[feature][core]` `hole`: `model_thread` schneidet echte Gewindegeometrie.
- `[feature][server]` Tool `datum` (Referenzen); neue Parameter in `pad`, `pocket`, `hole`.
- `[bugfix][server]` `pattern`: Beschreibung `polar: Gesamtwinkel` war deutsch.
- `[skip][todos]` Backlog-Ticket Design-Stream.

**Blocker:**
- keine

**Erkenntnisse:**
- `PartDesign::Point` kennt `ObjectXY` nicht (Recompute-Fehler „not implemented“), `ObjectOrigin` funktioniert; die `MapMode`-Enumeration ist je Datum-Typ verschieden.
- Positiver `TaperAngle` macht das Pad zum Ende hin weiter; die Pyramidenstumpf-Formel mit Wachstum passt auf < 1 %.
- Ein Loft/Helix/Torus in Tests am besten über exakte Volumenformeln prüfen, OCC-Bounding-Boxen sind zu grob.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: Datum-Referenzregel und `plane_support` als einziger Ebenen-Resolver in 98.
- Nicht übernehmen: Attachment-Modus-Tabellen.

**Validierung:**
- `run-core-tests -k "datum or taper or up_to_first or model_thread or lcs"`: 8 passed; `pytest tests/tools tests/server/test_language.py`: 98 passed.
- `uv run poe check`: ruff ✅, ruff format ✅, pyright 0 Fehler ✅, 183 Projekt-Python-Tests ✅, 246 FreeCAD-Python-Tests ✅.
- Browser-/manuelle Abnahme: keine in S3.

**Nächste Session:**
- S4: #4.1 `boolean` (Spike-Ergebnis OF-02 umsetzen), #4.2 `draft`.
- Dateien: `features.py` (`_dress_up`, `fillet`), `select.py` (`SELECTOR_PROPERTY`), `assembly.py` (`Parts`-Gruppe).
- Architektur-Deltas: Boolean-Regel in 98 bestätigen.

---

## Session 2 — 2026-09-29 (`helix`, `primitive`)

**Ziel:** #2.2 und #2.3.

**Erledigt:**
- Spike (Scratchpad): Property-Namen und Enumerationen aller Additive*-Typen und der Helix, Standardlage der Primitive (Box ab Ecke, Zylinder/Kegel/Prisma um die Achse ab 0, Kugel/Ellipsoid/Torus zentriert), `AttachmentOffset`-Expression an VarSet-Parameter folgt Änderungen.
- #2.2 `make_helix` + `helix` (Core, Bridge, Server, Beispiel), `thread` auf `make_helix` umgestellt (`display`-Import in `thread.py` entfällt).
- #2.3 `primitive` mit `_PRIMITIVES`, `_primitive_props`, `_attach`, `_ensure_primitive_cuts`; `sketch/model.py`: `_support` → `plane_support` (jetzt von `features` mitgenutzt).
- `docs/tools.md` regeneriert: 54 Tools.

**Release-Änderungen:**
- `[feature][core]` `helix`: additive und subtraktive Helix mit `pitch` und `height` oder `turns`, Achse wie bei `revolve`, Kegelwinkel, Linksgewinde.
- `[feature][core]` `primitive`: acht Primitive additiv/subtraktiv, Lage über Ebene, `center` und `offset`, Maße als Durchmesser/Ausdehnungen und Parameter.
- `[feature][server]` Tools `helix` und `primitive` im Katalog (Features).
- `[skip][core]` `thread` intern über `make_helix`, Verhalten unverändert.

**Blocker:**
- keine

**Erkenntnisse:**
- Screw-Volumen einer Helix ist unabhängig von der Steigung (Fläche × Schwerpunktbahn × Windungen); damit ist der Federtest exakt prüfbar.
- Subtraktive Primitive haben kein `Reversed`; `_ensure_cuts` passt nicht, deshalb eigener Check ohne Umkehr.
- OCC-Bounding-Boxen sind bei Torus/Ellipsoid zu groß; Lageprüfungen über `CenterOfMass`.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: Primitive-Regel (Referenzpunkt, Ebene, Offset) in 98 bestätigt; `plane_support` als gemeinsamer Ebenen-Resolver für Skizzen und Primitive.
- Nicht übernehmen: Property-Tabellen aus dem Spike.

**Validierung:**
- `run-core-tests -k "helix or primitive or thread or loft"`: 31 passed.
- `uv run poe check`: ruff ✅, ruff format ✅, pyright 0 Fehler ✅, 183 Projekt-Python-Tests ✅, 241 FreeCAD-Python-Tests ✅.
- Browser-/manuelle Abnahme: keine in S2; GUI-Anteil gesammelt in AC-11 (S5).

**Nächste Session:**
- S3: #3.1 `datum` (point/line/lcs), #3.2 Achsen über Datum Line + `create_sketch` auf LCS, #3.3 Taper/`up_to_first`, #3.4 `model_thread`.
- Dateien: `features.py` (`datum_plane`, `_attach`, `_revolve_axis`, `pad`, `pocket`, `hole`), `sketch/model.py` (`plane_support`), `sketch/external.py` (`DATUM_TYPES`), `src/buddy_server/tools/reference.py`.
- Architektur-Deltas: Datum-Referenzregel in 98 konkretisieren.

---

## Session 1 — 2026-09-29 (Spikes, Fundament, `loft`)

**Ziel:** #1.1, #1.2, #1.3 und #2.1.

**Erledigt:**
- #1.1 Spike Boolean: fuse/cut/common funktionieren über `addObjects`; Werkzeug-Body wandert in die Boolean-Gruppe, Undo/Rollback sauber. Entscheidung OF-02 im Index.
- #1.2 Spike ModelThread: Eigenschaft in 26.3 vorhanden, M6 ≈ 1,8 s / 91 Flächen, M10 ≈ 1,4 s / 64 Flächen, Solids gültig. Entscheidung OF-03 im Index.
- #1.3 `compat.REQUIRED_TYPES` + 25 Typen, `test_compat` grün. Volumenhelfer nach #2.3 verschoben.
- #2.1 `loft` in Core (`features.loft`, `_same_plane`), Bridge (`feature.loft`), Server (Tool `loft`), Beispiel in `gen_tool_docs`, `docs/tools.md` regeneriert (52 Tools); drei Core-Tests.

**Release-Änderungen:**
- `[feature][core]` `loft`: additiver und subtraktiver Loft über zwei oder mehr Skizzen, Sektionen auf eigenen Ebenen, Vorprüfung mit verständlicher Meldung.
- `[feature][server]` Tool `loft` im Katalog (Features).
- `[skip][core]` `REQUIRED_TYPES` erweitert (Vorbereitung, keine Nutzeränderung).

**Blocker:**
- keine

**Erkenntnisse:**
- Serena's Language-Server brauchte nach `activate_project` einen zweiten Aufruf, bevor Symbol-Tools funktionierten.
- In FreeCADs Python liefert ein Skript mit `import time` auf Modulebene trotzdem `NameError` für `time` (vermutet: FreeCAD-Init überschreibt `__main__`-Globals); `__import__("time")` im Ausdruck umgeht das. Nur für Spikes relevant.
- `Sections` (PropertyLinkSubList) akzeptiert eine einfache Objektliste.

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: Boolean-Verhalten im Baum und ModelThread-Regel in 98 eingetragen.
- Nicht übernehmen: Spike-Skripte, Property-Namen.

**Validierung:**
- `uv run python tools/freecad_env.py run-core-tests -- -k "loft or compat"`: 8 passed.
- `uv run pytest tests/tools`: 24 passed (Tool-Contract, Tool-Doku aktuell).
- `uv run poe check`: ruff ✅, ruff format ✅, pyright 0 Fehler ✅, 183 Projekt-Python-Tests ✅, 227 FreeCAD-Python-Tests ✅.
- Browser-/manuelle Abnahme: keine erforderlich in S1.

**Nächste Session:**
- S2: #2.2 `helix` mit `thread`-Umstellung, #2.3 `primitive` mit Volumenhelfern.
- Dateien: `addon/FreeCADBuddy/buddy_core/thread.py`, `features.py`, `src/buddy_server/tools/feature.py`, `tools/gen_tool_docs.py`.
- Architektur-Deltas: Primitive-Ausnahme in 98 konkretisieren.

---

## Session 0 — 2026-09-29 (Planung)

**Ziel:** Sprint aus dem Ticket `partdesign-vollstaendigkeit.md` formen.

**Erledigt:**
- Sprint-Ordner mit Index, fünf Phasen (16 Aufgaben), Architektur-Update und Session-Log angelegt.
- Spec-Stand 1 durch Ralf im Chat freigegeben („starte sprint“), Annahmen OF-01 bis OF-04 als Entscheidungen übernommen.

**Release-Änderungen:**
- `[skip][todos]` Planung, keine Produktänderung.

**Blocker:**
- keine

**Erkenntnisse:**
- keine

**Architektur-Erkenntnisse:**
- Betroffene Skills: `docs/architecture.md`
- Doku-Delta: fünf geplante Deltas in `98-architecture-update.md` (Tool-Katalog, Primitive-Ausnahme, Boolean-Regel, Datum-Referenzen, `REQUIRED_TYPES`).
- Nicht übernehmen: Property-Namen der PartDesign-Typen aus den Ticket-Notizen.

**Validierung:**
- nicht ausgeführt (nur Planungsartefakte); Pfade und Anker der Planung geprüft.
- Browser-/manuelle Abnahme: keine; AC-11 wartet auf Freigabe in S5.

**Nächste Session:**
- S1: #1.1 Spike Boolean, #1.2 Spike ModelThread, #1.3 `REQUIRED_TYPES` und Testhelfer, dann #2.1 `loft`.
- Dateien: `addon/FreeCADBuddy/buddy_core/features.py`, `addon/FreeCADBuddy/buddy_core/compat.py`, `tests/core/conftest.py`, `tests/core/test_features.py`.
- Architektur-Deltas: Spike-Ergebnisse in 98 nachtragen.

---

*(Einträge in umgekehrt chronologischer Reihenfolge — neueste oben.)*
