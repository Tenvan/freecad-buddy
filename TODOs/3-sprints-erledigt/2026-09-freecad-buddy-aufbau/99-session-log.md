# 📓 Session-Log

Chronologisches Protokoll aller Arbeitssessions. Nach jeder Session einen neuen Eintrag oben anlegen.
`Release-Änderungen` in derselben Session pflegen; sie bilden später die Grundlage für CHANGELOG/Release-Notes. Interne Änderungen bewusst mit `skip` markieren.

---

## Live-Test & Sprint-Abschluss — 2026-09-28

**Ziel:** Erster Einsatz gegen die echte FreeCAD-GUI, danach Sprint-Abschluss auf Wunsch von Ralf.

**Erledigt:**
- Testplatte 200 × 100 × 5 mm mit vier Bohrungen Ø 8 mm (Randabstand 10 mm) live über TUI-Server und GUI-Bridge gebaut, von Ralf bestätigt („passt“). Datei `out/Testplatte.FCStd`.
- Sieb-Lochung begonnen (Parameter, Skizze, Start-Pocket). Ein Muster auf ein LinearPattern schlug in PartDesign fehl („Cannot transform invalid support shape“) und wurde sauber zurückgerollt → neues `pattern kind="grid"` (MultiTransform aus zwei LinearPatterns, `direction2`/`length2`/`count2`); Muster auf Muster wird jetzt mit Hinweis abgelehnt. Das Raster selbst ist noch nicht angelegt (Lauf von Ralf abgebrochen) → Notiz im Folgeticket.
- TUI: Bereiche „Tool-Aufrufe“ und „Meldungen“ stehen übereinander statt nebeneinander (Wunsch Ralf).
- Sprint-Abschluss: GUI-Abnahme G1–G8 per Scope-Entscheidung von Ralf in das Folgeticket [`gui-abnahme.md`](../../1-backlog/freecad-buddy/gui-abnahme.md) verschoben. Sprint nach `3-sprints-erledigt/2026-09-freecad-buddy-aufbau/` verschoben, `master-todo.md` und Backlog-Index angepasst.

**Release-Änderungen:**
- `[feature][core]` `pattern` mit `kind="grid"` für 2D-Raster; verständliche Ablehnung von Muster auf Muster.
- `[feature][server]` TUI-Log-Bereiche übereinander.
- `[skip][todos]` Sprint-Abschluss und Folgeticket.

**Blocker:**
- keine

**Erkenntnisse:**
- Nach Änderungen am Core muss FreeCAD neu gestartet werden; ein Neustart der Bridge allein lädt die Module nicht neu.
- Die Konsole unter Windows (cp1252) braucht für Skript-Clients `PYTHONIOENCODING=utf-8`.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: keine
- Doku-Delta: keins (`grid` ist ein Feature-Detail, kein Schichtwechsel)
- Nicht übernehmen: Testplatte-Skripte (nur Scratchpad)

**Validierung:**
- `uv run poe check`: ruff ✅, pyright ✅, 45 Tests Projekt-Python ✅, 137 Tests FreeCAD-Python ✅ (inkl. `grid` und Muster-auf-Muster).
- GUI-/manuelle Abnahme: nicht abgenommen. Teilnachweise G1 (Live-Betrieb verbunden) und G7 (TUI im Einsatz) im Folgeticket; ausdrückliche Bestätigungen stehen aus.

**Nächste Session:**
- Folgeticket `gui-abnahme.md` einplanen; Sieb-Raster der Testplatte als Prüflauf für G2 fertigstellen.
- Umsetzung seit `6c05a50` ist nicht committet.

---

## Review-Runde — 2026-09-27 (unabhängiger Review-Agent, 12 Befunde, alle behoben)

**Erledigt:**
- Hoch #1: kein Retry nach gesendeter Anfrage (Doppel-Features), eigener `[timeout]`-Fehler, Server-Timeout > Bridge-Timeout; `gui_timeout` unterscheidet „verworfen“ und „läuft weiter“.
- Mittel #2: Einheiten in Ausdrücken (`Height + 2` → `+ 2 mm`), Expression aus dem AST.
- Mittel #3: Parameternamen, die FreeCAD als Einheit/Konstante liest, werden abgelehnt (`parseQuantity`-Probe, gegen 30 Namen verifiziert).
- Mittel #4: Export erzwingt passende Endung, Überschreiben nur mit `overwrite`.
- Mittel #5: `reconnect`/`close` blockieren den Event-Loop nicht mehr (Socket ohne Lock schließen).
- Mittel #6: Busy-Check bei modalem Dialog/Aufgabenbereich im Dispatcher; `undo`/`save` respektieren Nutzer-Bearbeitung.
- Mittel #7: `python.execute` braucht zusätzlich die FreeCAD-seitige Freischaltung (Einstellung `AllowPython`, neuer Workbench-Befehl); Token-Dateien mit Owner-Rechten.
- Niedrig #8–#12: `exit()` in Skripten abgefangen, keine sterbenden Verbindungs-Threads (auch bei nicht serialisierbaren Antworten), Backoff im Watchdog und Rate-Limit für Ablehnungs-Logs, Reject mit `id=None` erkannt, kein Socket-Leck beim Connect, Screenshot (Container sichtbar, 3D-Ansicht geprüft, Kamera/aktives Dokument wiederhergestellt), `create_body` auf dem richtigen GUI-Dokument, keine Steuerzeichen im Profil.

**Release-Änderungen:**
- `[bugfix][server]` Keine doppelte Ausführung nach Zeitüberschreitung; verständliche Timeout-Meldungen.
- `[bugfix][core]` Ausdrücke mit Zahl plus Parameter funktionieren; ungültige Parameternamen und Export-Endungen werden klar abgelehnt.
- `[bugfix][bridge]` Robuster gegen Dialoge, Skript-`exit()` und falsche Tokens.
- `[feature][bridge]` Workbench-Befehl „Python-Ausführung umschalten“; `execute_python` doppelt abgesichert.

**Validierung:**
- `uv run poe check`: ruff ✅, pyright ✅, 45 + 135 Tests ✅ (neu u. a. `tests/core/test_review_fixes.py`, `tests/server/test_bridge_client.py`, Busy-/Exit-Tests).
- GUI-only-Befunde (#6 Dialog-Erkennung, #10 Screenshot, #11 Body-Aktivierung): Code angepasst, Wirkung nur in der GUI prüfbar → Teil der Nutzerabnahme G2/G4.

---

## Sessions 2–10 — 2026-09-27 (durchgehende Umsetzung per `/goal`)

**Ziel:** Sprint komplett umsetzen, ohne weitere Rückfragen (Auftrag Ralf).

**Erledigt:**
- S2 #1.5, #1.7 — Bridge-Addon (`buddy_bridge`, `InitGui.py`, Workbench, Autostart) und Installer (`fixer`).
- S3 #1.6, #1.8, #1.9 — Server-Kern (mcp-SDK 2.2, Streamable HTTP, Auth, Host/Origin, Event-Bus), TUI (`designer`), CLI, `.mcp.json`.
- S4 #2.1–#2.5 — Dokumente, Transaktionen, `ToolResult`, VarSet-Parameter, Werte/Ausdrücke, Screenshot, Labels.
- S5/S6 #3.1–#3.7 — Sketch-Engine: Anlage, Low-Level, Analyse, 7 Profile, Assistent, Lint.
- S7/S8 #4.1–#4.7 — Features, Selektoren inkl. Koordinaten-Filter, Re-Resolve, Fehlerkatalog.
- S9 #5.1–#5.4 — Druckerprofil, Druckbarkeitsprüfung, Export (`fixer`), Designhinweise.
- S10 #6.1–#6.4 — Prompts, Referenzprojekte E2E, README, `docs/tools.md` (generiert), `CHANGELOG.md`, `docs/acceptance.md`.
- Team: `fixer` (Installer, Druck-Workflow), `designer` (TUI), 3× `librarian` (SDK-Recherche), unabhängiger Review-Agent. Agenten-Ergebnisse gegengeprüft (SDK-Quellcode, Testläufe); zwei Agenten stoppten am Turn-Limit und wurden fortgesetzt.

**Release-Änderungen:**
- `[feature][bridge]` FreeCAD-Addon mit Bridge (Token, 127.0.0.1, Hauptthread-Dispatch, Autostart, Workbench-Befehle, Headless-Modus).
- `[feature][server]` TUI-Server `freecad-buddy` mit MCP über Streamable HTTP, 32 Tools (+ `execute_python` opt-in), Prompts.
- `[feature][core]` Sketch-Engine mit vollständig bestimmten Profilen, Parametern/Ausdrücken, PartDesign-Features, semantischen Selektoren.
- `[feature][print]` Druckerprofil, Druckbarkeitsprüfung, Export STL/3MF/STEP.
- `[feature][examples]` Referenzprojekte Box mit Deckel, Wandhalter, Drehknopf.
- `[doc][docs]` README, Tool-Katalog, Abnahme-Checkliste, Changelog, Architektur-Nachtrag.
- `[misc][tooling]` Installer, Headless-Bridge, Tool-Doku-Generator, Import-/Vertragswächter.

**Blocker:**
- keine. Offen: GUI-/manuelle Abnahmen G1–G8 (nur Ralf, `docs/acceptance.md`).

**Erkenntnisse:**
- FreeCAD 26.3: kein Python-Observer für Konsolenmeldungen → Objektstatus + Fehlerkatalog statt Mitschnitt.
- FreeCAD öffnet Transaktionen lazy (`HasPendingTransaction` erst nach erster Änderung).
- `sse_starlette.AppStatus.should_exit` ist prozessweit: ohne Reset beenden spätere Server-Instanzen jeden SSE-Stream sofort (TUI-Neustart, Tests).
- mcp-SDK 2.x: snake_case (`is_error`, `structured_content`); `from __future__ import annotations` verlangt Annotationen auf Modulebene; Token-Verifier setzt OAuth voraus → eigene Middleware.
- pytest in FreeCADs Python braucht `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, sobald das venv Pakete mit Plugin-Entry-Points enthält.
- mcp/uvicorn loggen mit INFO auf stderr → in der TUI Umleitung in den Event-Bus nötig (Smoke-Test gefunden, nicht durch Tests).

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md` (Transaktionen, Ausdrücke, Selektoren, geklärte Punkte, Tool-Katalog, Teststrategie)
- Doku-Delta: in `98-architecture-update.md` übernommen.

**Validierung:**
- `uv run poe check`: ruff ✅, pyright 0 Fehler ✅, 40 Tests Projekt-Python ✅ (inkl. E2E über MCP gegen Headless-FreeCAD und 3 Referenzprojekte), 121 Tests FreeCAD-Python ✅.
- CLI-Smoke `freecad-buddy --headless` / `--print-claude-command` mit Tokens im Scratchpad ✅.
- GUI-/manuelle Abnahme: **nicht ausgeführt** (Freigaberegel; kein Auftrag zur GUI-Prüfung). Checkliste G1–G8 in `docs/acceptance.md`.

**Nächste Session:**
- Nutzerabnahme G1–G8; Befunde als Bugfix-Sessions; danach Sprint-Abschluss (Verschieben nach `3-sprints-erledigt/`, `master-todo.md`).

---

## Planungs-Update — 2026-09-27 (nach S1)

**Ziel:** Plananpassung „MCP-Server mit TUI“ und Umbenennung.

**Erledigt:**
- Spec-Stand 2 (Entwurf): R-11, AC-16 neu; AC-01, AC-12 angepasst; OF-08 (MCP-Port) neu; neue Session S3 (TUI-Server), Folge-Sessions um eins verschoben (jetzt S1–S10); Aufgaben #1.6 überarbeitet, #1.8 (TUI) und #1.9 (Start & Anbindung) neu → 36 Aufgaben.
- Umbenennung auf **FreeCAD Buddy**: `addon/FreeCADBuddy/`, `buddy_core`, `src/buddy_server/`, CLI `freecad-buddy`, Env `FREECAD_BUDDY_ALLOW_PYTHON`, Sprint-Ordner `freecad-buddy-aufbau`, Backlog-Domain `freecad-buddy`. Vorherige Kandidaten „Sketchsmith“ (verworfen: Zungenbrecher) und `freecad-mcp` (von anderen Projekten belegt).
- `docs/architecture.md`: Abschnitte „MCP-Transport“ und „TUI“, Token-Ablage vereinheitlicht.
- Recherche (Team, 3× `librarian`): mcp-SDK 2.2 (`MCPServer`, `streamable_http_app`, `TransportSecuritySettings`, `token_verifier` – im SDK-Quellcode gegengeprüft), Textual 8.2.8 (Workers, `RichLog(max_lines)`, `run_test`), Claude-Code-HTTP-Konfiguration (`.mcp.json` mit `type: http`, `headers`, `${VAR}`-Expansion).

**Release-Änderungen:**
- `[misc][naming]` Projekt und Pakete in „FreeCAD Buddy“ umbenannt.
- `[doc][architecture]` MCP-Transport per Streamable HTTP und TUI-Konzept dokumentiert.

**Freigabe:**
- Spec-Stand 2 von Ralf im Chat freigegeben (2026-09-27); OF-08: MCP-Port 8765.

**Blocker:**
- keine

**Erkenntnisse:**
- Eine TUI und stdio-Transport schließen sich aus (stdin/stdout gehören dem MCP-Client).
- Offen und nicht dokumentiert: Hook für Tool-Aufruf-Ereignisse im SDK, uvicorn im Textual-Loop, Auto-Reconnect-Verhalten von Claude Code bei spätem Serverstart.

**Validierung:**
- `uv run poe check` nach Umbenennung: ruff ✅, pyright 0 Fehler ✅, 6 Tool-Tests ✅, 5 Core-Tests ✅.
- Linkprüfung der Planungsartefakte (siehe unten).

**Nächste Session:**
- S2: #1.5 Bridge-Addon, #1.7 Installer.

---

## Session 1 — 2026-09-27

**Ziel:** Referenz-Code analysieren, Repo/Toolchain aufsetzen, Architektur-Doku schreiben, Headless-Testharness bauen.

**Erledigt:**
- #1.1 — Code-Analyse von vier Referenz-Repos (flache Clones im Scratchpad, nichts ausgeführt); Ergebnis in `5-konzepte/freecad-mcp-marktanalyse.md#code-erkenntnisse-11-2026-09-27`.
- #1.2 — `git init` (Branch `main`, kein Commit), `pyproject.toml` (uv, Python 3.13, ruff, pyright, pytest, poethepoet), `.gitignore`, `LICENSE` (MIT), `README.md`. `.mcp.json` nach #1.6 verschoben.
- #1.3 — `docs/architecture.md` (Schichten, Layout, RPC-Vertrag, Fehlercodes, Threading, Transaktionen, `ToolResult`, Sicherheit, Modellierungsregeln, API-Drift, Teststrategie).
- #1.4 — `tools/freecad_env.py`, `tools/run_core_tests.py`, `buddy_core.compat` (Versionsinfo, `missing_types()`), Tests in `tests/tools` und `tests/core`.

**Release-Änderungen:**
- `[feature][tooling]` Entwicklungsumgebung mit `uv run poe check` (Lint, Typecheck, Tests inkl. Core-Tests in FreeCADs Python).
- `[feature][core]` Kompatibilitätsprüfung: benötigte FreeCAD-Dokumenttypen werden gegen den laufenden Build geprüft.
- `[doc][architecture]` Architektur-Dokumentation `docs/architecture.md`.

**Blocker:**
- keine

**Erkenntnisse:**
- `uv run` exportiert `PYTHONHOME` des uv-Pythons; FreeCADs conda-forge-`python.exe` lädt dann eine fremde Stdlib (`platform.python_version()` scheitert). Lösung: Interpreter-Variablen im Subprozess entfernen (Test vorhanden).
- FreeCADs `python.exe` kann `FreeCAD` direkt importieren, wenn `bin/` und `lib/` in `sys.path` stehen; pytest aus dem venv läuft darin unverändert.
- Alle 17 benötigten Typen (inkl. `App::VarSet`, `PartDesign::MultiTransform`) sind in 26.3.0 vorhanden.
- User-Mod-Pfad: `%APPDATA%\FreeCAD\v26-3\Mod`.
- `mcp`-SDK liegt in Version 2.2.0 vor (Major 2): API vor #1.6 gegen aktuelle Doku prüfen, nicht aus Trainingswissen übernehmen.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md`
- Doku-Delta: Layout-Abweichung, Teststrategie, Transaktions-Konzept, API-Drift → in `98-architecture-update.md` als übernommen eingetragen.
- Nicht übernehmen: Details der Referenz-Implementierungen (insb. blwfish, LGPL).

**Validierung:**
- `uv run poe check`: ruff check + format ✅, pyright 0 Fehler ✅, `tests/tools` 6 passed ✅, `tests/core` 5 passed (FreeCAD 26.3.0, Python 3.13.15) ✅.
- GUI-/manuelle Abnahme: in S1 keine erforderlich.

**Nächste Session:**
- S2: #1.5 Bridge-Addon, #1.6 MCP-Server (vorher `mcp`-SDK-2.x-Doku prüfen), #1.7 Installationsskript.
- Relevant: `docs/architecture.md` (RPC-Vertrag, Threading, Sicherheit), `addon/FreeCADBuddy/`, `src/buddy_server/`.
- Offen vor Sprint-Abschluss: OF-07 (Bridge-Start), Signal-Wakeup verifizieren.

---

## Session 0 — 2026-09-27 (Planung)

**Ziel:** Sprint-Plan für den eigenen FreeCAD-MCP-Server erstellen.

**Erledigt:**
- TODO-Struktur (`TODOs/`) inkl. Vorlagen angelegt.
- Marktanalyse bestehender FreeCAD-MCP-Projekte (README-Ebene) in `5-konzepte/freecad-mcp-marktanalyse.md`.
- Sprint `freecad-buddy-aufbau` mit Spezifikation (Stand 1, Entwurf), 6 Phasen, 9 Sessions, 34 Aufgaben.

**Release-Änderungen:**
- `[skip][planning]` Reine Planung, keine Produktänderung.

**Blocker:**
- keine

**Erkenntnisse:**
- FreeCAD 26.3.0 weekly (Build 2026-09-22) mit Python 3.13.15 unter `%LOCALAPPDATA%\Programs\FreeCAD 26.3`; `App::VarSet` verfügbar; `uv` installiert.
- Bestehende Projekte setzen auf viele Low-Level-Tools und `execute_python`; Differenzierung über Intent-Level-Tools, voll bestimmte Skizzen, Transaktionen und Druckbarkeits-Checks.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md` (noch anzulegen)
- Doku-Delta: vorgeschlagene Grundentscheidungen in `98-architecture-update.md` eingetragen.
- Nicht übernehmen: —

**Validierung:**
- Nur Planungsartefakte geprüft (Links, Zählungen, Abdeckung Aufgaben ↔ Kriterien). Keine Produkt- oder GUI-Prüfungen ausgeführt.
- GUI-/manuelle Abnahme: keine erforderlich.

**Freigabe:**
- Spec-Stand 1 von Ralf im Chat freigegeben (2026-09-27). Entscheidungen: VarSet, Druckerprofil 256³/0,4 mm/PLA, `execute_python` opt-in, Claude Code als Client, lokales Git + MIT, englische ASCII-Labels. OF-07 offen (nicht blockierend).

**Nächste Session:**
- S1 starten: #1.1 Code-Analyse der Referenz-Repos, danach #1.2 Setup.

---

## Session-Eintrag-Template

```text
## Session <N> — YYYY-MM-DD

**Ziel:** <Was sollte erreicht werden?>

**Erledigt:**
- <Aufgabe #ID — Kurzbeschreibung>

**Release-Änderungen:**
- `[<feature|bugfix|doc|removal|misc|skip>][<scope>]` <Nutzerrelevante Änderung oder Begründung für `skip`>

**Blocker:**
- <Beschreibung> — blockiert <Aufgabe #ID>

**Erkenntnisse:**
- <Was wurde gelernt? Was lief gut/schlecht?>

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: <keine / docs/architecture.md>
- Doku-Delta: <Stabile Erkenntnis für 98-architecture-update.md>
- Nicht übernehmen: <Temporäre Implementierungsdetails oder Code-Samples>

**Validierung:**
- <Headless-/Unit-Tests, Lint oder nicht ausgeführt mit Begründung>
- <GUI-/manuelle Abnahme: Prüfumfang, Nutzerbestätigung oder ausdrückliche Agentenfreigabe und Ergebnis; alternativ offen oder keine erforderlich. Gültige Nachweise übernehmen, nicht automatisch wiederholen.>

**Nächste Session:**
- <Was steht als nächstes an?>
- <Welche Dateien/Module sind relevant?>
- <Welche Architektur-Deltas sind vor Sprint-Abschluss noch zu prüfen?>
```

---

*(Einträge in umgekehrt chronologischer Reihenfolge — neueste oben.)*
