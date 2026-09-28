# Phase 1 — Fundament, Bridge & TUI-Server

> **Ziel:** Repository, Toolchain, Architektur-Doku und Testharness stehen; die Bridge läuft in FreeCAD, und der manuell gestartete TUI-Server `freecad-buddy` verbindet Claude Code über Streamable HTTP mit der laufenden FreeCAD-GUI.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 2 (freigegeben 2026-09-27), Kriterien AC-01, AC-02, AC-12, AC-13, AC-16.

## Session-Pakete

### 📦 Session S1 — Recherche-Spike, Setup, Architektur, Testharness ✅

Enthaltene Aufgaben: #1.1, #1.2, #1.3, #1.4

### 📦 Session S2 — Bridge-Addon in FreeCAD ✅

- **Ergebnis:** `buddy_bridge` (Protokoll, Tokens, TCP-Server, Registry, Qt-Hauptthread-Dispatcher, Service, Workbench-Befehle, Headless-Modus), `InitGui.py`, Installer.

Enthaltene Aufgaben: #1.5, #1.7

### 📦 Session S3 — TUI-Server `freecad-buddy` ✅

- **Ergebnis:** Server-Kern (MCP über Streamable HTTP, Bearer-Auth, Host/Origin-Schutz, Session-Zählung, Event-Bus, Bridge-Client mit Watchdog), Textual-TUI, CLI, `.mcp.json`.

Enthaltene Aufgaben: #1.6, #1.8, #1.9

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| — | Alle Aufgaben umgesetzt; offen sind nur GUI-Abnahmen (siehe unten) | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #1.1 | Code-Analyse neka-nat, spkane, JakobThiessen, blwfish; Ergebnis in [Marktanalyse](../../5-konzepte/freecad-mcp-marktanalyse.md#code-erkenntnisse-11-2026-09-27) | in `docs/architecture.md` eingeflossen | 2026-09-27 |
| #1.2 | `git init`, `pyproject.toml` (uv, Python 3.13, ruff, pyright, pytest, poe), `.gitignore`, `LICENSE`, `README.md` | Layout `addon/FreeCADBuddy/` | 2026-09-27 |
| #1.3 | `docs/architecture.md` | Erstanlage | 2026-09-27 |
| #1.4 | Testharness (`tools/freecad_env.py`, `tools/run_core_tests.py`), `buddy_core.compat` | Umgebungsbereinigung, Plugin-Autoload aus | 2026-09-27 |
| #1.5 | Bridge-Addon: `buddy_bridge/{protocol,tokens,client,server,registry,dispatch,qt_dispatcher,methods,service,commands,headless}.py`, `InitGui.py` (Workbench „FreeCAD Buddy“, Autostart, OF-07: beides) | Signal-Dispatch statt Polling, Code `1009 gui_timeout` | 2026-09-27 |
| #1.7 | Installer: `uv run poe install-addon` / `uninstall-addon` / `addon-status` (Junction, nie echte Verzeichnisse löschen) – umgesetzt vom `fixer` | — | 2026-09-27 |
| #1.6 | Server-Kern `src/buddy_server/{config,events,bridge,tools,app,runner,prompts,logs}.py` (mcp-SDK 2.2) | eigene Bearer-Middleware, `AppStatus`-Reset, Logging-Umleitung | 2026-09-27 |
| #1.8 | Textual-TUI `src/buddy_server/tui.py` (Status, Sessions, Tool-Log, Meldungen, Tasten r/c/p/q) – umgesetzt vom `designer` | Event-Bus → `post_message` | 2026-09-27 |
| #1.9 | CLI `freecad-buddy` (`--port`, `--bridge-port`, `--headless`, `--allow-python`, `--print-claude-command`), `.mcp.json` mit `${FREECAD_BUDDY_TOKEN}`, README „Starten“ | — | 2026-09-27 |

## Geplante Abnahmeprüfungen

GUI- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen). Ablauf je Prüfung in [`docs/acceptance.md`](../../../docs/acceptance.md).

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| G1 / AC-01: Claude Code ↔ TUI ↔ FreeCAD-GUI, `get_status`; FreeCAD schließen → `bridge_unavailable` ≤ 10 s | offen | ausstehend | automatisiert gegen Headless-Bridge belegt (`tests/server/test_e2e.py`) |
| G2 / AC-02: GUI bleibt während Tool-Aufrufen bedienbar | offen | ausstehend | Dispatcher headless belegt (`tests/bridge/test_qt_dispatcher.py`) |
| G7 / AC-16: TUI-Sichtprüfung | offen | ausstehend (nur Nutzer) | Pilot-Tests grün (`tests/server/test_tui.py`) |

## 🔄 Nächste Session

> **Einstieg:** Phase umgesetzt. Offen sind nur die GUI-Abnahmen G1, G2, G7 (Nutzer, siehe `docs/acceptance.md`).
