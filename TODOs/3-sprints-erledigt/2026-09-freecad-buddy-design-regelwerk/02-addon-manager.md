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
| — | — | — | — | — | — | — |

## ✔️ Done Tasks

| Aufgabe | Beschreibung | Architektur-Delta | Erledigt am |
|---|---|---|---|
| #2.1 | Spike (Code-Analyse AM 2026.8.18, Katalog einmal mit Ralfs Zustimmung geladen: 176 Addons/262 Makros, SHA-256 geprüft). Ergebnisse: Katalogformat (Einträge je Branch, Details nur im `package_xml`), Installiert-Logik (`Mod/<id>` nicht leer; Makro-Datei im Makro-Ordner), Installer-Signale (`run()`-Rückgabe unzuverlässig), Netzwerk nur im Hauptthread initialisierbar, Offline-Bug im AM. Entscheidung OF-02: Suche im Server, Status/Installation in der Bridge | in 98 notiert | 2026-09-28 |
| #2.2 | `src/buddy_server/addon_catalog.py` (Parser, Kompatibilität, Ranking Name > Tag > Beschreibung, alle Begriffe müssen passen; `package_xml` ohne DOCTYPE/ENTITY gegen XXE) und `addon_service.py` (Download mit SHA-256, Cache unter `<Buddy-Home>/addon-catalog`, täglicher Abgleich über `.sha256`, offline mit Cache und Warnung, sonst `catalog_unavailable`, falsche Prüfsumme `catalog_checksum` ohne Teil-Update). Tool `search_addons`, Bridge-Methode `addons.status`. Fixture aus dem echten Katalog (`tests/fixtures/addon_catalog`) | in 98 notiert | 2026-09-28 |
| #2.4 | Installation: `buddy_core/addons/install.py` mit Job-Modell (`addons.install` gibt sofort eine Job-Id zurück, `addons.install_status` pollt). Der modale Dialog läuft per `QTimer.singleShot` im Hauptthread, Standard „Abbrechen“. Workbenches über `AddonInstaller` im `QThread` (nur `success` zählt, Fallback `Mod/<id>`, `allow_list=[]`), Makros über `MacroInstaller`. Ein fehlgeschlagener Job entfernt das neu angelegte `Mod/<id>`. Opt-in in FreeCAD (Einstellung `AllowAddonInstall`, Befehl „Addon-Installation umschalten“, Env) und im Server (`--allow-addon-install`, Env). Tool `install_addon` mit Vorprüfungen und Polling bis `wait_seconds`. Texte englisch (Spec-Stand 3) | in 98 notiert | 2026-09-28 |
| #2.5 | Tests: `tests/core/test_addons_install.py` (7, mit Fake-Backend; dazu Kompatibilitätstest der AM-API, der echte `Addon`-Objekte aus dem Fixture baut), `tests/server/test_addon_install_tool.py` (8: Opt-in, Vorprüfungen, doppeltes Opt-in gegen Headless-Bridge), Bridge-Registry-Test. Der Import-Wächter erlaubt AM-Module nur in `install.py` | keins | 2026-09-28 |
| #2.3 | Tool `get_addon`: Details, Kompatibilität, Status, README-Auszug (bereinigt, gekürzt, als Fremdtext markiert, Regel im Thema `addons`) | keins | 2026-09-28 |

## Geplante Abnahmeprüfungen

Browser- und manuelle Prüfungen nur nach der [Freigaberegel in TODOs/README.md](../../README.md#browser--und-manuelle-abnahmeprüfungen) ausführen.

| Prüfung / Spec-Kriterium / Umfang / erwartetes Ergebnis | Status | Nutzerbestätigung oder Agentenfreigabe | Ergebnis / Session-Log-Nachweis |
|---|---|---|---|
| Live-Katalogabruf von `addons.freecad.org` im Spike (#2.1) | durchgeführt | Zustimmung Ralf im Chat, 2026-09-28 (einmaliger Download) | 4 Dateien, SHA-256 geprüft, nur im Scratchpad |
| G9 (AC-08): echtes Addon über Claude Code installieren, erst ablehnen, dann zustimmen; danach im Addon Manager als installiert sichtbar | offen | nur Ralf | ausstehend |

## 🔄 Nächste Session

> **Einstieg für den nächsten Agenten / die nächste Session:**
>
> - Offene Aufgaben: 0 (Phase abgeschlossen)
> - Nächste Session: S5 (Phase 3)
> - Relevante Dateien: `Mod/AddonManager/*` im FreeCAD-Installationsverzeichnis, `buddy_bridge/methods.py`
> - Architektur-Deltas: Job-Muster, Adapter-Modul, Sicherheitsmodell in `98-architecture-update.md`
> - Startpunkt: #3.1 in `03-design-tools.md`
