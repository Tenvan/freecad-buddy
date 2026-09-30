# Abnahme in der FreeCAD-GUI — Checkliste

Diese Prüfungen brauchen die laufende FreeCAD-GUI bzw. deinen Slicer und werden **von dir** durchgeführt (Freigaberegel in `TODOs/README.md`); einzelne führt auf deine Freigabe der Agent aus, siehe [Agentengestützte Prüfung](#agentengestützte-prüfung). Alles andere ist automatisiert (`uv run poe check`).

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
| G8 | optional | Probedruck Box mit Deckel | Deckel passt mit dem Spiel `clearance_fit` |
| G9 | Sprint 2, AC-08 | Server normal starten (Addon-Installation ist serverseitig Standard) und in FreeCAD „Addon-Installation erlauben“ klicken; danach ist nur noch „Addon-Installation sperren“ aktiv. Dann in Claude Code `install_addon` für ein kleines Addon aufrufen (Vorschlag: Makro `FCHoneycombMaker`), zuerst ablehnen, danach erneut aufrufen und zustimmen | Dialog mit Name, Quelle, Lizenz, Standard „Abbrechen“. Bei Ablehnung `user_declined`, nichts installiert. Bei Zustimmung installiert, im Addon Manager als installiert sichtbar |
| G10 | Sprint 2, AC-11 | Platte mit Rand bauen lassen, dann `fill_pattern` je einmal mit `cell="round"` und `cell="hex"` (Feld über `field=["Plate_Width - 2*Rim_Width", …]`); in der GUI `<Name>_Pitch` und `Plate_Width` ändern und die Skizze der Startzelle öffnen | Raster gleichmäßig im Feld, Waben mit gleichem Steg; nach Änderungen folgen Anzahl und Feld; Skizze „vollständig bestimmt“; ein Undo-Schritt pro Aufruf |
| G11 | Sprint 2, AC-14 | TUI während eines Bauvorgangs ansehen, einen Eintrag mit Enter öffnen, mit `v` umschalten | Anfrage und Antwort je Aufruf verständlich, Farben nach Erfolg/Warnung/Fehler, keine Tokens sichtbar |
| G12 | Sprint 2, AC-16 | Bauteil bauen lassen; nach dem ersten `pad` und nach dem abschließenden `set_view` die 3D-Ansicht ansehen | Bauteil komplett sichtbar und leicht isometrisch |
| G13 | Sprint `freecad-buddy-partdesign`, AC-11 | Trichter (`loft` über zwei Kreise auf XY und einer Datum-Ebene), Feder (`helix`) und Kugelknauf (`primitive`) über MCP bauen lassen; in der GUI jedes Feature per Doppelklick öffnen, einen Parameter im VarSet ändern, Recompute | Features öffnen sich im Task-Panel, das Modell folgt dem Parameter ohne Fehler, Skizzen weiterhin „vollständig bestimmt“ |
| G14 | Sprint `freecad-buddy-storepoints`, AC-10 | Teil bauen lassen, `storepoint("Grundkörper")`; im Baum die Gruppe `Storepoints` öffnen, den Marker ansehen, die Beschreibungsspalte einblenden (Rechtsklick in den Baum), Doppelklick auf den Marker | Marker mit Rauten-Icon, in der Beschreibungsspalte „◆ Storepoint 1: Grundkörper“ am Feature (kein Hover-Tooltip), Doppelklick markiert das Feature |
| G15 | Sprint `freecad-buddy-storepoints`, AC-07 | Nach einem Aufbau eine Skizze in der GUI von Hand bearbeiten (mehrere Aktionen erlaubt), dann `pad` über MCP, dann `list_storepoints` | `manual_edits` = 1 (eine Bearbeitungssitzung = ein Eintrag, auch bei mehreren GUI-Transaktionen); `replay` in ein neues Dokument warnt genau einmal auf diesen Schritt |

## Agentengestützte Prüfung

Übergang bis zum GUI-Testlauf (Backlog E-27): Einige Prüfungen kann der Agent in der laufenden GUI selbst ausführen, ohne Maus und Bildschirmkoordinaten, in-process über `FreeCADGui` und Qt ([`tools/gui_checks.py`](../tools/gui_checks.py)). Voraussetzung ist die Freigabe der Prüfung und `execute_python`, das du in der TUI mit `p` einschaltest und danach wieder ausschaltest. Während des Laufs die Maus nicht im FreeCAD-Fenster bewegen.

| # | Automatisch | Bleibt bei dir |
|---|---|---|
| G13 | `task_panels`: jedes Feature öffnet sein Task-Panel (`setEdit`) und schließt wieder, Dokument danach gültig. Parameter ändern und nachmessen über die normalen Tools | Ob sich das Weiterarbeiten im Panel gut anfühlt |
| G14 | `storepoint_tree`: Marker-Icon vorhanden, Beschreibungsspalte = `Label2` am verlinkten Feature, Doppelklick-Handler des ViewProviders wählt das Feature und öffnet kein Panel | Ob das Icon die Raute ist; der echte Maus-Doppelklick (ein synthetischer per `QTest` wirkte unzuverlässig) |
| G15 | teilweise: Auswertung über `list_storepoints` und `replay`; die GUI-Bearbeitung selbst noch von Hand (echte Sketcher-Transaktionen) | die Skizzenbearbeitung |

Nicht automatisierbar: G6 (Slicer), G7 (Verständlichkeit der TUI), G8 (Probedruck) und alle Urteile über Aussehen und Bedienbarkeit.

Aufruf: Die Datei per `exec` aus dem Repo laden (so läuft der eingecheckte Stand) und `result` setzen, Beispiel im Docstring von `tools/gui_checks.py`. Erprobt am 2026-09-30 auf FreeCAD 26.3 (G13 3/3, G14 in drei Läufen stabil).

Ergebnisse bitte im Folgeticket (`TODOs/1-backlog/freecad-buddy/gui-abnahme.md`) oder im Chat festhalten.
