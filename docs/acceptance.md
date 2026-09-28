# Abnahme in der FreeCAD-GUI — Checkliste

Diese Prüfungen brauchen die laufende FreeCAD-GUI bzw. deinen Slicer und werden **von dir** durchgeführt (Freigaberegel in `TODOs/README.md`). Alles andere ist automatisiert (`uv run poe check`).

Vorbereitung: `uv sync`, `uv run poe install-addon`, FreeCAD neu starten, `uv run freecad-buddy`, Claude Code per `c` in der TUI anbinden.

| # | Kriterium | Ablauf | Erwartetes Ergebnis |
|---|---|---|---|
| G1 | AC-01 | In Claude Code `get_status` aufrufen; dann FreeCAD schließen und erneut aufrufen | Version 26.3, Status verbunden, Aufruf in der TUI; nach dem Schließen `[bridge_unavailable]` in ≤ 10 s, TUI zeigt „wartet“ |
| G2 | AC-02 | Während Claude Code ein Referenzprojekt baut, in FreeCAD die Ansicht drehen und Menüs öffnen | GUI bleibt bedienbar, keine Hänger oder Abstürze |
| G3 | AC-03 | Nach einem Tool-Aufruf in FreeCAD „Bearbeiten → Rückgängig“ öffnen | genau ein Schritt pro Tool mit sprechendem Namen (z. B. „Pad: Base“) |
| G4 | AC-09 | `screenshot` (view iso) aufrufen | Bild der aktuellen 3D-Ansicht in Claude Code |
| G5 | AC-14 | Referenzprojekte bauen (`uv run python examples/reference_projects.py`), je Projekt: Modellbaum sichten, eine Skizze öffnen, einen Wert im VarSet `Parameters` ändern, selbst ein Feature ergänzen | sprechende Labels; Skizze „vollständig bestimmt“; Modell aktualisiert sich korrekt; manuelles Weiterarbeiten problemlos |
| G6 | AC-11 | Exportierte 3MF-Datei im Slicer öffnen | Teil liegt auf dem Bett, Maße stimmen |
| G7 | AC-16 | TUI ansehen | Status, Sessions, Tool-Log und Meldungen verständlich |
| G9 | Sprint 2, AC-08 | Server mit `--allow-addon-install` starten und in FreeCAD „Addon-Installation umschalten“ wählen. Dann in Claude Code `install_addon` für ein kleines Addon aufrufen (Vorschlag: Makro `FCHoneycombMaker`), zuerst ablehnen, danach erneut aufrufen und zustimmen | Dialog mit Name, Quelle, Lizenz, Standard „Abbrechen“. Bei Ablehnung `user_declined`, nichts installiert. Bei Zustimmung installiert, im Addon Manager als installiert sichtbar |
| G8 | optional | Probedruck Box mit Deckel | Deckel passt mit dem Spiel `clearance_fit` |

Ergebnisse bitte im Folgeticket (`TODOs/1-backlog/freecad-buddy/gui-abnahme.md`) oder im Chat festhalten.
