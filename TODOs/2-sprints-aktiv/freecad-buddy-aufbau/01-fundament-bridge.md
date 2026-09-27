# Phase 1 — Fundament, Bridge & TUI-Server

> **Ziel:** Repository, Toolchain, Architektur-Doku und Testharness stehen; die Bridge läuft in FreeCAD, und der manuell gestartete TUI-Server `freecad-buddy` verbindet Claude Code über Streamable HTTP mit der laufenden FreeCAD-GUI.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1 (S2) bzw. Stand 2 (S3), Kriterien AC-01, AC-02, AC-12, AC-13, AC-16. Umsetzung nur für freigegebenen Umfang; #1.1–#1.4 sind technische Vorarbeiten. Spec-Stand 2 freigegeben am 2026-09-27.

## Session-Pakete

### 📦 Session S1 — Recherche-Spike, Setup, Architektur, Testharness

- **Kontext-Anker:** `TODOs/5-konzepte/freecad-mcp-marktanalyse.md`, `%LOCALAPPDATA%\Programs\FreeCAD 26.3\bin\`
- **Einstiegspunkt:** #1.1 — Code-Analyse der Referenz-Repos
- **Erfolgskriterium:** `uv run pytest` läuft (leer grün), ein Core-Dummy-Test läuft in FreeCADs Python, `docs/architecture.md` beschreibt Schichten, RPC-Vertrag und Modellierungsregeln.
- **Architektur-Relevanz:** `docs/architecture.md` (Erstanlage)
- **Architektur-Notiz:** Paketlayout und Weg, wie `core` in FreeCAD geladen wird (Addon-Pfad vs. `sys.path`-Injektion), festlegen.

Enthaltene Aufgaben: #1.1, #1.2, #1.3, #1.4

### 📦 Session S2 — Bridge-Addon in FreeCAD

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_bridge/`, `addon/FreeCADBuddy/InitGui.py`, `docs/architecture.md#rpc-vertrag-server--bridge`, `tools/`
- **Einstiegspunkt:** #1.5 — Bridge-Addon
- **Erfolgskriterium:** Bridge startet in FreeCAD, beantwortet `auth.hello` und `system.status` über TCP; ein kleiner Test-Client (`tools/bridge_client.py`) belegt das gegen die laufende GUI (nur mit Freigabe); Transport/Framing/Auth sind headless getestet; Installer verlinkt das Addon.
- **Architektur-Relevanz:** `docs/architecture.md` (RPC-Vertrag, Threading)
- **Architektur-Notiz:** Main-Thread-Dispatch (Signal-Wakeup oder `QTimer`) und Token-Ablage dokumentieren; Qt über FreeCADs `PySide`-Shim importieren.

Enthaltene Aufgaben: #1.5, #1.7

### 📦 Session S3 — TUI-Server `freecad-buddy` (Spec-Stand 2)

- **Kontext-Anker:** `src/buddy_server/`, `docs/architecture.md#mcp-transport-client--server`, `.mcp.json`
- **Einstiegspunkt:** Spike — uvicorn (`Server.serve()`) als async Worker im Textual-Event-Loop; danach #1.6
- **Erfolgskriterium:** `uv run freecad-buddy` öffnet die TUI; Claude Code verbindet sich per HTTP; `get_status` liefert Version 26.3 und Bridge-Status; ohne FreeCAD zeigt die TUI „warte auf Bridge“ und das Tool liefert `bridge_unavailable` ≤ 10 s; `--headless` für Tests.
- **Architektur-Relevanz:** `docs/architecture.md` (MCP-Transport, Sicherheit, TUI)
- **Architektur-Notiz:** Ereignisfluss Server-Kern → TUI (Events statt direkter Widget-Zugriffe) festhalten, damit `--headless` denselben Kern nutzt.

Enthaltene Aufgaben: #1.6, #1.8, #1.9

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #1.5 | Bridge-Addon (`addon/FreeCADBuddy/buddy_bridge`, `InitGui.py`): TCP-Server nur `127.0.0.1`, Token (zufällig, in `%APPDATA%\FreeCADBuddy\bridge-token`), JSON-RPC/NDJSON-Dispatch in den Qt-Hauptthread (Signal-Wakeup verifizieren, sonst `QTimer`-Polling), Start/Stop per Workbench-Befehl + optional Autostart (OF-07), Logging in die Report-View. Nur Stdlib. | Geplant | `bridge` | #1.3 | — | AC-02, AC-12 |
| #1.7 | Installationsskript (PowerShell): Addon per Junction nach `%APPDATA%\FreeCAD\v26-3\Mod\FreeCADBuddy` verlinken (Pfad per `FreeCAD.getUserAppDataDir()` ermittelt), Deinstallation, Statusprüfung. | Geplant | `bridge` | #1.5 | — | AC-01 |
| #1.6 | Server-Kern (`buddy_server`, `mcp`-SDK 2.2: `MCPServer`, `streamable_http_app()`, `session_manager.run()` im Lifespan, `TransportSecuritySettings` mit `allowed_hosts`/`allowed_origins` für `127.0.0.1`/`localhost`, Bearer-Token über `token_verifier` bzw. Auth-Middleware): Bridge-Client (Connect-/Request-Timeout, Auto-Reconnect, Fehler-Mapping inkl. `bridge_unavailable`), Tools `get_status`, `ping`; `execute_python` nur bei `FREECAD_BUDDY_ALLOW_PYTHON=1`; Ereignis-Bus (Tool-Aufruf gestartet/beendet, Bridge-Status, Konsole) für TUI und `--headless`-Logging; `tests/server/` in `poe test`. | Geplant | `server` | #1.5 | — | AC-01, AC-12, AC-13 |
| #1.8 | TUI (Textual 8.x): Kopfzeile mit Bridge-/FreeCAD-Status und MCP-Endpunkt, Panel „MCP-Sessions“, Live-Log der Tool-Aufrufe (Name, Dauer, Ergebnis; `RichLog` mit `max_lines=1000`, externe Texte escaped), Panel „FreeCAD-Konsole“, Tastenaktionen (Bridge neu verbinden, `claude mcp add`-Befehl kopieren, `execute_python` umschalten, beenden); uvicorn als async Worker; Pilot-Tests (`App.run_test`). | Geplant | `server` | #1.6 | — | AC-16 |
| #1.9 | Start & Anbindung: CLI `freecad-buddy [--port 8765] [--headless]` als Script-Entry in `pyproject.toml`; MCP-Token in `%APPDATA%\FreeCADBuddy\mcp-token` erzeugen (Bridge-Token liegt daneben als `bridge-token`); `.mcp.json` mit `"type": "http"`, `"url": "http://127.0.0.1:8765/mcp"`, `"headers": {"Authorization": "Bearer ${FREECAD_BUDDY_TOKEN}"}`; README-Abschnitt „Starten“ (FreeCAD → Bridge → `freecad-buddy` → Claude Code). | Geplant | `server` | #1.6 | — | AC-01 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #1.1 | Code-Analyse neka-nat, spkane, JakobThiessen, blwfish; Ergebnis in [Marktanalyse](../../5-konzepte/freecad-mcp-marktanalyse.md#code-erkenntnisse-11-2026-09-27) | in `docs/architecture.md` eingeflossen (Threading, Transaktionen, Konsolen-Mitschnitt) | 2026-09-27 |
| #1.2 | `git init` (Branch `main`, noch kein Commit), `pyproject.toml` (uv, Python 3.13, ruff, pyright, pytest, poe), `.gitignore`, `LICENSE` (MIT), `README.md`. `.mcp.json` nach #1.6 verschoben. | Layout-Abweichung: Core/Bridge unter `addon/FreeCADBuddy/` (in 98 notiert) | 2026-09-27 |
| #1.3 | `docs/architecture.md` erstellt | Erstanlage | 2026-09-27 |
| #1.4 | Testharness: `tools/freecad_env.py` (FreeCAD finden, `run-core-tests`), `tools/run_core_tests.py` (Einstieg in FreeCADs Python); `buddy_core.compat` mit API-Drift-Prüfung; `uv run poe check` führt Lint, Typecheck, `tests/tools` und `tests/core` aus | Umgebungsbereinigung (`PYTHONHOME` u. a.) in 98 notiert | 2026-09-27 |

## Geplante Abnahmeprüfungen

GUI- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen. Vorher Nutzerprüfungen abfragen und nur ausdrücklich übertragene Prüfungen übernehmen; zusätzliche oder erneute Prüfungen erneut freigeben lassen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| AC-01: FreeCAD + Bridge starten, `freecad-buddy` starten, in Claude Code `get_status` aufrufen → Version 26.3, Status „connected“, Aufruf erscheint im TUI-Log; FreeCAD beenden, erneut aufrufen → `bridge_unavailable` ≤ 10 s, TUI zeigt „warte auf Bridge“ | offen | ausstehend | ausstehend |
| AC-02: Stresstest-Skript (100 Aufrufe) gegen laufende GUI, währenddessen GUI bedienen → keine Hänger/Abstürze | offen | ausstehend | ausstehend |
| AC-16 (optional): Sichtprüfung der TUI durch Ralf – Übersicht verständlich, Log lesbar | offen | ausstehend (nur Nutzer) | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 5
> - Nächste Session: S2 (Bridge), danach S3 (TUI-Server)
> - Relevante Dateien: `docs/architecture.md` (RPC-Vertrag, Threading, Sicherheit, MCP-Transport), `addon/FreeCADBuddy/`, `src/buddy_server/`, `tools/freecad_env.py`
> - Architektur-Deltas: offene Punkte „Signal-Wakeup“, „OF-07“ (S2) und „uvicorn im Textual-Loop“, „OF-08“ (S3) aus `docs/architecture.md#offene-architekturpunkte` klären
> - Startpunkt: #1.5
> - Abnahme: GUI-Prüfungen AC-01/AC-02 nur nach Freigabe durch Ralf
