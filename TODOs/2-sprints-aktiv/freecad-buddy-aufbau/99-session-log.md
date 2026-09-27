# 📓 Session-Log

Chronologisches Protokoll aller Arbeitssessions. Nach jeder Session einen neuen Eintrag oben anlegen.
`Release-Änderungen` in derselben Session pflegen; sie bilden später die Grundlage für CHANGELOG/Release-Notes. Interne Änderungen bewusst mit `skip` markieren.

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
