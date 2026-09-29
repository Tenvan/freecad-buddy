# 🔍 Sprint-Review — <SPRINT-TITEL>

> Bereich: `<Start-Commit>..<End-Commit>` │ Domäne: `<domäne>` │ Review-Session: YYYY-MM-DD │ Abnahme: ausstehend

Regeln: [README → Review-Gate](../../README.md#review-gate-sprint-abnahme). Review in einer frischen Session; jede Datei wird vollständig gelesen.

## Dateiliste

Erzeugt mit `git diff --name-status <Start-Commit>..HEAD`. Jede Zeile braucht einen Status.

| Datei | Änderung (A/M/D/R) | Bewertung (Korrektheit, Komplexität, Lesbarkeit, Tests/Doku) | Status |
|---|---|---|---|
| `<pfad>` | M | <Kurzbefund oder „ok“> | <ok / behoben / → Eingang E-NN> |

## Werkzeug-Befunde

| Quelle | Befund | Datei:Zeile | Status |
|---|---|---|---|
| `/code-review high` | <Befund> | `<pfad>:<zeile>` | <behoben / → Eingang E-NN / verworfen (Begründung)> |
| `/simplify` | <Befund> | `<pfad>:<zeile>` | <…> |

## Komplexität

- `C901`-Befunde vorher/nachher: <N> → <N>
- Dateien über 400 Zeilen, die im Sprint gewachsen sind: <keine / Liste>

## Ergebnis

- [ ] Jede Datei der Liste hat einen Status.
- [ ] Befunde im Sprint-Umfang behoben, `uv run poe check` danach grün.
- [ ] Übrige Befunde im Backlog-Eingang eingetragen.
- [ ] Abnahme durch Ralf im Chat bestätigt: <Datum, Zitat>
