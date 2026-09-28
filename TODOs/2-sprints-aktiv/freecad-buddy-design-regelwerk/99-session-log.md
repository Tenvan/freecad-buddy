# 📓 Session-Log

Chronologisches Protokoll aller Arbeitssessions. Nach jeder Session einen neuen Eintrag oben anlegen.
`Release-Änderungen` in derselben Session pflegen; sie bilden später die Grundlage für CHANGELOG/Release-Notes. Interne Änderungen bewusst mit `skip` markieren.

---

## Session 2b — 2026-09-28 (Live-Test mit Claude Code, Ansicht nach dem ersten Basis-Feature)

**Ziel:** Platte direkt über die MCP-Tools in Claude Code bauen und Ralfs Rückmeldung zur Startansicht umsetzen.

**Erledigt:**
- Testplatte über die MCP-Tools gebaut (Client `claude-code`): 12 Aufrufe, Volumen 98 994,7 mm³, 8 Undo-Schritte, keine Label-Probleme. Nicht gespeichert.
- Sichtung: Die Instructions kamen in Claude Code ungekürzt an (1 874 Zeichen). AC-01 ist damit per Sichtung belegt.
- Rückmeldung Ralf: Die Startansicht passt nicht, weil `set_view` im leeren Dokument nichts zum Einpassen hat. Jetzt setzt das erste Basis-Feature eines Bodys die Ansicht automatisch (iso und fit), die Regel verlangt nur noch den letzten Schritt.
- TUI-Test: Feste Pause durch Warten auf die Bedingung ersetzt, er war unter Last geflakt.

**Release-Änderungen:**
- `[feature][core]` Nach dem ersten `pad` bzw. `revolve` eines Bodys springt die FreeCAD-Ansicht auf iso und zeigt das ganze Bauteil, damit sich der Aufbau live verfolgen lässt.

**Blocker:**
- keine

**Erkenntnisse:**
- Deterministische Server-Logik ist verlässlicher als eine Regel, die der Agent befolgen muss, wenn der Zeitpunkt eindeutig ist (erstes Solid).
- Offen und ungeprüft: Auf oberster Ebene des Dokuments liegt `Origin001` („Ursprungspunkt“, `App::Point`), angelegt vermutlich nicht von Buddy.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: keine
- Doku-Delta: keins
- Nicht übernehmen: —

**Validierung:**
- `uv run poe check`: ruff ✅, pyright ✅, 65 Tests Projekt-Python ✅, 138 Tests FreeCAD-Python ✅.
- GUI-/manuelle Abnahme: Ralf hat den Live-Aufbau verfolgt. G12 prüft er nach dem FreeCAD-Neustart erneut.

**Nächste Session:**
- FreeCAD neu starten (Core geändert), Platte erneut aufbauen, danach S3.

---

## Session 2a — 2026-09-28 (Chat-Test und Ansichtsregel)

**Ziel:** Chat-Log mit Ralf live testen (Platte ohne Sieb), Farbfehler beheben, Ansichtsregel ergänzen (Spec-Stand 2).

**Erledigt:**
- Testplatte live neu gebaut: 12 Tool-Aufrufe, Volumen 98 994,7 mm³, Druckprüfung ohne Befund. Nicht gespeichert, `out/Testplatte.FCStd` bleibt unverändert.
- Bugfix nach Ralfs Screenshot: Der Kürzungshinweis wurde als JSON-Fehler rot markiert und Rich-`Syntax` malte einen schwarzen Hintergrund. Jetzt `JSONHighlighter` nur für den Vordergrund, der Hinweis ist gedimmt und kursiv (`57a5edc`).
- #1.6 Ansichtsregel und `set_view` (Spec-Stand 2).

**Release-Änderungen:**
- `[bugfix][server]` Chat-Blasen ohne schwarzen Hintergrund, Kürzungshinweis nicht mehr rot.
- `[feature][core]` Neues Tool `set_view`: Live-Ansicht setzen (iso, dimetric, trimetric, Normalansichten) und alles einpassen.
- `[feature][server]` Regelwerk: Ansicht als erster und letzter Schritt, Bauteil komplett sichtbar und isometrisch.

**Blocker:**
- keine

**Erkenntnisse:**
- Der Client des Skripts meldet sich als `mcp` (clientInfo), deshalb heißt die Session im Chat `mcp #12`.
- Das Budget der Instructions wird knapp: 1 874 von 2 000 Zeichen. Weitere Kernregeln nur, wenn andere kürzer werden.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md` (Tool-Katalog)
- Doku-Delta: keins
- Nicht übernehmen: —

**Validierung:**
- `uv run poe check`: ruff ✅, pyright ✅, 65 Tests Projekt-Python ✅, 138 Tests FreeCAD-Python ✅.
- GUI-/manuelle Abnahme: Ralf hat den Chat live gesichtet („sieht gut aus“, Farbfehler gemeldet und behoben), G11 damit teilweise belegt. G12 offen.

**Nächste Session:**
- FreeCAD neu starten, weil der Bridge-Code geändert wurde. Danach S3 (Addon-Manager), Live-Katalogabruf nur mit Zustimmung.

---

## Session 2 — 2026-09-28

**Ziel:** Phase 4, TUI-Chat-Log. Zusätzlich Ralfs Zwischenmeldung: `q` hängt.

**Erledigt:**
- #4.1 MCP-Middleware `ToolCallLog` erzeugt `ToolStarted`/`ToolFinished` mit Argumenten, Antwort, Fehlercode und Session. `ToolContext` publiziert keine Events mehr. `payloads.py` für Maskierung, Platzhalter, Grenzen und Zusammenfassung.
- #4.2 Chat-Ansicht `chat.py` mit Detailansicht und Umschaltung auf die Liste.
- #4.3 `--log-file` (JSONL), Headless-Ausgabe von Anfrage und Antwort, Tests.
- Bugfix Beenden: Obergrenzen beim Stoppen (uvicorn-Grace 2 s, zweites `q`, TUI-Wartezeit 5 s, Exit trotz hängender Threads mit Diagnose). Den Hänger selbst konnte ich nicht reproduzieren.

**Release-Änderungen:**
- `[feature][server]` Tool-Log als farbiger Chat mit Anfrage und Antwort, Detailansicht (Enter), Umschaltung auf die Liste (v) und maskierten Geheimnissen.
- `[feature][server]` `--log-file` schreibt Tool-Aufrufe als JSONL mit.
- `[bugfix][server]` `q` beendet die TUI zuverlässig. Ein zweites `q` beendet sofort.

**Blocker:**
- keine

**Erkenntnisse:**
- Die `ServerMiddleware` des MCP-SDK 2.2 ist der richtige Ort für Request-Logging: Sie sieht die Rohargumente und das fertige `CallToolResult`.
- In SDK 2.x sind die Konstruktoren von `mcp.types` snake_case (`mime_type`, `is_error`, `structured_content`); `model_dump(by_alias=True)` liefert die camelCase-Wire-Form.
- Die Ursache des `q`-Hängers ist unbestätigt. Kandidaten: ein Bridge-Aufruf, der in `asyncio.to_thread` blockiert, oder eine Verbindung, die Claude Code offen hält. Kommt die Diagnosezeile „beende trotz hängender Threads (…)“, nennt sie den Thread.
- Heredocs mit Python-Code scheitern in Git Bash gelegentlich am Quoting. Längere Skripte deshalb als Datei im Scratchpad ablegen.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md`
- Doku-Delta: Logging auf Protokollebene (98, bestätigt)
- Nicht übernehmen: CSS-Details der Chat-Ansicht

**Validierung:**
- `uv run poe check`: ruff ✅, pyright ✅, 63 Tests Projekt-Python ✅, 137 Tests FreeCAD-Python ✅.
- GUI-/manuelle Abnahme: G11 (Chat-Log sichten) und die Bestätigung des `q`-Fixes durch Ralf stehen aus.

**Nächste Session:**
- S3 (Phase 2): #2.1 Spike zur Addon-Manager-API. Live-Katalogabruf nur mit Ralfs Zustimmung.

---

## Session 1 — 2026-09-28

**Ziel:** Phase 1 – Design-Regelwerk, kompakte Instructions, `get_design_rules`, Resource.

**Erledigt:**
- #1.1 Recherche: Claude Code dokumentiert weder Übernahme noch Längengrenze der Instructions. Budget bleibt bei 2 000 Zeichen und wird per Sichtung geprüft. Tool-Ausgaben sind standardmäßig auf 25 000 Tokens begrenzt (für S2 wichtig).
- #1.2 `src/buddy_server/design_rules.py`: 9 Themen und 42 Regeln, `requires`-Filter, Druckwerte aus dem Profil.
- #1.3 Instructions aus der Quelle: 1 688 Zeichen, Design-Tool-Regel als Kernregel.
- #1.4 Tool `get_design_rules`, Resource `buddy://design-rules` und `/{topic}`, Prompts aus der Quelle. Der alte Text `HUMAN_MODELING_GUIDE` ist entfallen.
- #1.5 8 Tests in `tests/server/test_design_rules.py`. `docs/tools.md` neu erzeugt (34 Tools), README ergänzt.
- Vorab zwei Commits: `f10cbf6` (0.1.0) und `d94df30` (Planung).

**Release-Änderungen:**
- `[feature][server]` Design-Regelwerk mit 9 Themen über `get_design_rules`, MCP-Resource und Prompt; Druckwerte folgen dem Druckerprofil.
- `[feature][server]` Kompaktere, vollständigere Server-Instructions inklusive Design-Tool-Regel.

**Blocker:**
- keine

**Erkenntnisse:**
- `MCPServer.instructions` ist read-only. Die Tool-Namen werden deshalb vorab über einen `NameCollector` gesammelt, das spart private API.
- `session.read_resource` erwartet in SDK 2.2 einen `str`, keine `AnyUrl`.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md`
- Doku-Delta: Regelwerk als einzige Quelle mit `requires`-Filter (98, bestätigt)
- Nicht übernehmen: Regeltexte selbst (liegen im Code)

**Validierung:**
- `uv run poe check`: ruff ✅, pyright ✅, 53 Tests Projekt-Python ✅, 137 Tests FreeCAD-Python ✅.
- GUI-/manuelle Abnahme: Sichtung der Instructions in Claude Code nach Neustart offen (AC-01).

**Nächste Session:**
- S2 (Phase 4): #4.1 Events mit Payload, danach die Chat-Ansicht.

---

## Session 0 — 2026-09-28 (Planung)

**Ziel:** Neuen Sprint aus Ralfs Auftrag planen: Design-Regelwerk, Addon-Suche und -Installation, Grid-Recherche, Design-Tool-Regel, dazu nachgereicht der Chat-Log in der TUI.

**Erledigt:**
- Backlog-Tickets `design-regelwerk.md`, `addon-manager-integration.md`, `grid-loesung-recherche.md` und `tui-chat-log.md` angelegt. `gui-abnahme.md` in den Sprint übernommen.
- Sprint-Spezifikation Stand 1 (Entwurf) mit R-01 bis R-11, AC-01 bis AC-15, 19 Aufgaben in 5 Phasen und 6 Sessions.
- Vorentscheidungen von Ralf: Regelwerk kompakt plus Tool und Resource; Addon-Installation mit Opt-in und Dialog; Design-Tool-Regel mit Vorschlagsliste; GUI-Abnahme mitführen; Chat-Log in der TUI.

**Release-Änderungen:**
- `[skip][todos]` Nur Planung.

**Freigabe:**
- Spec-Stand 1 von Ralf im Chat freigegeben (2026-09-28), inklusive der Annahmen OF-01 bis OF-08. Start mit S1. Vorher zwei Commits (Vorgänger-Sprint, Planung).

**Blocker:**
- keine

**Erkenntnisse:**
- Addon Manager 2026.8.18 (FreeCAD 26.3): Katalog `https://addons.freecad.org/addon_catalog_cache.zip` mit `.sha256`, Makros über `macro_cache.zip`, lokaler Cache `<UserCache>/AddonManager2026-1`. Auf diesem Rechner existiert noch kein Cache. `AddonInstaller` lädt Zips in einer eigenen Event-Schleife, deshalb braucht es das Job-Muster.
- `ToolFinished` trägt bisher nur eine Kurzfassung. Für den Chat-Log braucht es Payloads im Event.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md`
- Doku-Delta: sechs vorgeschlagene Deltas in `98-architecture-update.md`
- Nicht übernehmen: —

**Validierung:**
- Nur Planungsartefakte. Links und Abdeckung Aufgaben ↔ Kriterien geprüft. Keine Produkt- oder GUI-Prüfungen.
- GUI-/manuelle Abnahme: keine erforderlich.

**Nächste Session:**
- Nach Freigabe: vorher die Umsetzung aus dem Vorgänger-Sprint committen, dann S1 (#1.1).

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
- <GUI-/manuelle Abnahme: Prüfumfang, Nutzerbestätigung oder ausdrückliche Agentenfreigabe und Ergebnis; alternativ offen oder keine erforderlich.>

**Nächste Session:**
- <Was steht als nächstes an?>
```

---

*(Einträge in umgekehrt chronologischer Reihenfolge — neueste oben.)*
