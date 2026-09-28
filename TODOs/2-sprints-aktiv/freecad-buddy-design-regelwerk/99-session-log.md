# 📓 Session-Log

Chronologisches Protokoll aller Arbeitssessions. Nach jeder Session einen neuen Eintrag oben anlegen.
`Release-Änderungen` in derselben Session pflegen; sie bilden später die Grundlage für CHANGELOG/Release-Notes. Interne Änderungen bewusst mit `skip` markieren.

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
