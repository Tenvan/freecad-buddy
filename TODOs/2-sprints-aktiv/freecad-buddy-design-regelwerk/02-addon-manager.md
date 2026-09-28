# Phase 2 — Addon-Manager-Integration

> **Ziel:** Der Agent durchsucht den offiziellen FreeCAD-Addon-Katalog, liest Details und kann Addons nach doppeltem Opt-in und deiner Bestätigung im FreeCAD-Dialog über FreeCADs eigenen Installer installieren.

> **Spec-Bezug:** [Sprint-Spezifikation](00-index.md#spezifikation), Stand 1, Kriterien AC-06 bis AC-09. Spec-Stand 1 freigegeben am 2026-09-28.

## Session-Pakete

### 📦 Session S3 — Spike, Adapter, Suche und Details

- **Kontext-Anker:** `%LOCALAPPDATA%\Programs\FreeCAD 26.3\Mod\AddonManager\` (`AddonCatalog.py`, `addonmanager_workers_startup.py`, `addonmanager_installer.py`, `addonmanager_freecad_interface.py`), `addon/FreeCADBuddy/buddy_bridge/methods.py`, `tests/core/test_compat.py`
- **Einstiegspunkt:** #2.1 — Spike zur Programmier-API des Addon Managers 2026.8.18
- **Erfolgskriterium:** Mit Fake-Katalog liefert `search_addons("grid")` gerankte Treffer mit Kompatibilität und Installationsstatus.
- **Architektur-Relevanz:** `docs/architecture.md` (Schichten, RPC-Methoden, Sicherheitsmodell)
- **Architektur-Notiz:** neues Core-Modul `buddy_core/addons/` als einziger Adapter zur internen Addon-Manager-API. Entscheidung OF-02: Core oder Server.

Enthaltene Aufgaben: #2.1, #2.2, #2.3

### 📦 Session S4 — Installation mit Opt-in und Dialog

- **Kontext-Anker:** `addon/FreeCADBuddy/buddy_bridge/service.py`, `commands.py`, `qt_dispatcher.py`, `src/buddy_server/bridge.py`, `cli.py`
- **Einstiegspunkt:** #2.4 — Job-Muster und Bestätigungsdialog
- **Erfolgskriterium:** Headless-Test installiert das Fixture-Addon mit simulierter Zustimmung. Bei Ablehnung bleibt das Mod-Verzeichnis unverändert.
- **Architektur-Relevanz:** `docs/architecture.md`
- **Architektur-Notiz:** Das Job-Muster (Start plus Statusabfrage oder Fortschritts-Notifications) ist neu im RPC-Vertrag. Timeouts bleiben für alle anderen Methoden unverändert.

Enthaltene Aufgaben: #2.4, #2.5

---

## ✅ Active Tasks

| Aufgabe | Beschreibung | Status | Architektur-Relevanz | Abhängigkeiten | Aufwand (h) | Spec-Kriterien / Voraussetzung |
|---|---|---|---|---|---|---|
| #2.1 | Spike: Katalog laden und prüfen (Cache-Zip, `.sha256`, lokaler Cache), Kompatibilitätsprüfung, Installationsstatus (Mod-Verzeichnis, Installationsmanifest), `AddonInstaller`/`MacroInstaller` ohne GUI-Dialoge, Abhängigkeitsauflösung. Ergebnis: Entscheidung OF-02, API-Liste für den Kompatibilitätstest. Live-Netz nur mit Ralfs Zustimmung | Geplant | `mehrere` | — | 3 | technische Voraussetzung für AC-06 bis AC-09 |
| #2.2 | Adapter `buddy_core/addons/` plus RPC `addons.search`: Katalog mit Prüfsumme, Offline-Fallback mit Cache-Alter, Ranking (Name > Tags > Beschreibung), Filter `kind`. MCP-Tool `search_addons`. Fake-Katalog als Test-Fixture | Geplant | `core`, `server` | #2.1 | 4 | AC-06 |
| #2.3 | RPC `addons.get` plus Tool `get_addon`: Lizenz, Maintainer, Repository, letzte Aktualisierung, Abhängigkeiten, README-Auszug (gekürzt, Markdown bereinigt) | Geplant | `core`, `server` | #2.2 | 2 | AC-07 |
| #2.4 | Installation: Opt-in Server (`--allow-addon-install` / `FREECAD_BUDDY_ALLOW_ADDON_INSTALL`) und FreeCAD (Einstellung `Mod/FreeCADBuddy/AllowAddonInstall`, Workbench-Befehl). Modaler Bestätigungsdialog im Hauptthread mit Standard „Abbrechen“. Job-Muster gegen Timeouts. Installation über `AddonInstaller`/`MacroInstaller`. Vorprüfungen (installiert, inkompatibel, Python-Abhängigkeiten laut OF-03) | Geplant | `mehrere` | #2.3 | 5 | AC-08, AC-09 |
| #2.5 | Tests: nicht registriert ohne Opt-in, Ablehnung → `user_declined`, Zustimmung (simuliert) → installiert und im Manifest, Abbruch → kein Rest, Kompatibilitätstest der genutzten Addon-Manager-API gegen den laufenden Build | Geplant | `core`, `bridge` | #2.4 | 3 | AC-08, AC-09 |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| — | — | — | — |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| Live-Katalogabruf von `addons.freecad.org` im Spike (#2.1) | offen | ausstehend (Zustimmung Ralf nötig) | ausstehend |
| G9 (AC-08): echtes Addon über Claude Code installieren, erst ablehnen, dann zustimmen; danach im Addon Manager als installiert sichtbar | offen | nur Ralf | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 5
> - Nächste Session: S3
> - Relevante Dateien: `Mod/AddonManager/*` im FreeCAD-Installationsverzeichnis, `buddy_bridge/methods.py`
> - Architektur-Deltas: Job-Muster, Adapter-Modul, Sicherheitsmodell in `98-architecture-update.md`
> - Startpunkt: #2.1
