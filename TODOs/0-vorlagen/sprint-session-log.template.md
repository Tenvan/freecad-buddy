# 📓 Session-Log

Chronologisches Protokoll aller Arbeitssessions. Nach jeder Session einen neuen Eintrag oben anlegen.
`Release-Änderungen` in derselben Session pflegen; sie bilden später die Grundlage für CHANGELOG/Release-Notes. Interne Änderungen bewusst mit `skip` markieren.

---

## Session-Eintrag-Template

```
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
- Betroffene Skills: <keine / docs/architecture.md>
- Doku-Delta: <Welche stabile Architekturregel, Modulgrenze, Datenfluss-, Integrations-, Security-, Test- oder Deployment-Erkenntnis muss in 98-architecture-update.md?>
- Nicht übernehmen: <Temporäre Implementierungsdetails oder Code-Samples, die nicht in die Architektur-Doku gehören.>

**Validierung:**
- <Tests, Builds, manuelle Prüfung oder nicht ausgeführt mit Begründung>
- <Browser-/manuelle Abnahme: Prüfumfang, Nutzerbestätigung oder ausdrückliche Agentenfreigabe und Ergebnis; alternativ offen oder keine erforderlich. Gültige Nachweise übernehmen, nicht automatisch wiederholen.>

**Nächste Session:**
- <Was steht als nächstes an?>
- <Welche Dateien/Module sind relevant?>
- <Welche Architektur-Deltas sind vor Sprint-Abschluss noch zu prüfen?>
```

---

*(Einträge in umgekehrt chronologischer Reihenfolge — neueste oben.)*
