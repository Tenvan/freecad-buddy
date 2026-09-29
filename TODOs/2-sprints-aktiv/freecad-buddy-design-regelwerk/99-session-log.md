# 📓 Session-Log

Chronologisches Protokoll aller Arbeitssessions. Nach jeder Session einen neuen Eintrag oben anlegen.
`Release-Änderungen` in derselben Session pflegen; sie bilden später die Grundlage für CHANGELOG/Release-Notes. Interne Änderungen bewusst mit `skip` markieren.

---

## Session 6a — 2026-09-29

**Ziel:** HexFill-Pfad streichen (Ralf: „dann lass weg“) und #5.4 englische MCP-Ausgaben.

**Erledigt:**
- HexFill komplett gestrichen: Regel im Thema `addons`, G13 und Empfehlung entfernt, OF-10 entschieden („kein Addon“).
- OF-09 entschieden (Ralf): nur MCP-Ausgaben englisch.
- #5.4 rund 340 Texte umgestellt: Regelwerk und Instructions, Prompts, Resources, alle Tool- und Parameterbeschreibungen, Meldungen, Hinweise und Fehler aus Server, Core und Bridge, Undo-Namen (`Create body`, `Set parameters`, …). Das Präfix `Hinweis:` heißt jetzt `Hint:`, der TUI-Chat erkennt beide.
- Sprachtest `tests/server/test_language.py` (AC-17): dynamisch über `build_mcp` und statisch per AST über alle Quelltexte. Ausnahmen: TUI-/Konsolen-Module, Workbench-Befehle, Bestätigungsdialog und Bridge-Status mit Marker `# ui-de`.

**Release-Änderungen:**
- `[feature][server]` Alle MCP-Ausgaben (Instructions, Regelwerk, Tool-Beschreibungen, Ergebnisse, Fehler) sind englisch; FreeCAD-Oberfläche und TUI bleiben deutsch.
- `[removal][addons]` Keine HexFill-Empfehlung im Regelwerk.

**Blocker:**
- keine

**Erkenntnisse:**
- Der erste Wortlisten-Scan war zu lasch (z. B. „fehlgeschlagen“, „Unbekannte Methode“ rutschten durch). Der Test nutzt eine breitere Liste mit Umlauten und Fachwörtern.
- Undo-Namen sind MCP-Ausgabe (`get_model_tree`), erscheinen aber auch im FreeCAD-Undo-Menü, dort also jetzt englisch.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md`
- Doku-Delta: Sprachregel MCP englisch / UI deutsch mit Marker (98)
- Nicht übernehmen: Übersetzungsskripte

**Validierung:**
- `uv run poe check`: ruff ✅, pyright ✅, 173 Projekt-Python-Tests ✅, 219 FreeCAD-Python-Tests ✅.
- GUI-/manuelle Abnahme: keine in dieser Session. Die live laufende Bridge braucht für die neuen Texte einen FreeCAD-Neustart.

**Nächste Session:**
- #5.1 prüfen, #5.2 Doku, CHANGELOG und Version 0.2.0, #5.3 GUI-Abnahme G1–G12.

---

## Session 5 — 2026-09-29

**Ziel:** Phase 3 mit Grid-Recherche, Vorschlagsliste für Design-Tools und `hole_grid`.

**Erledigt:**
- #3.3 `hole_grid` im Core (`buddy_core/design_tools.py`), in der Bridge (`design.hole_grid`) und als Tool in der neuen Gruppe `[Design tools]`. `rect` und `hex`, `count` oder `field` mit `margin`. Bei `field` sind die Anzahlen `floor`-Expressions im VarSet und folgen Raster und Feldgröße.
- `transaction()` ist verschachtelbar. Ein Design-Tool ruft die bestehenden Tools auf und ist trotzdem genau ein Undo-Schritt.
- #3.2 `propose_design_tool` und `list_design_tool_proposals` (`proposals.py`, Ablage `design-tool-proposals.json` im Buddy-Home), Event `DesignToolProposed` in TUI und Headless-Log.
- #3.1 Grid-Recherche auf dem lokalen Katalog-Cache aus S3: `TODOs/5-konzepte/grid-loesungen.md`. Regel zur Portabilität im Thema `addons`.
- Nebenfund behoben: `values._emit` hat Konstanten in Ausdrücken mit `:g` auf 6 Stellen gerundet (z. B. 0.8660254 → 0.866025). Jetzt sind es 12 Stellen.

**Release-Änderungen:**
- ~~`[feature][design]` `hole_grid`~~ → ersetzt durch `fill_pattern` (siehe Nachtrag).
- `[feature][design]` `propose_design_tool` und `list_design_tool_proposals`: Vorschläge für fehlende Design-Tools, zusammengeführt und gezählt, Meldung in der TUI.
- `[bugfix][core]` Zahlen in Maßausdrücken verlieren keine Nachkommastellen mehr (bisher 6 signifikante Stellen).
- `[doc][konzepte]` Grid-Recherche mit Empfehlung.

**Blocker:**
- keine

**Erkenntnisse:**
- VarSet-Eigenschaften dürfen Expressions auf andere Eigenschaften desselben VarSets haben (`<<Parameters>>.X`). So folgen abgeleitete Anzahlen im Feldmodus dem Raster, ohne eigenes Objekt.
- `hex` braucht keinen zweiten MultiTransform: Zwei Startlöcher in einer Skizze plus ein Raster mit doppeltem Reihenabstand reichen.
- Der Katalog kennt kein Addon für runde Lochraster. HexFill ist der einzige gepflegte Kandidat für echte Waben (Arbeitsweise ungeprüft).

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md`
- Doku-Delta: Design-Tools als Komposition mit verschachtelbarer Transaktion, Vorschlagsablage im Server (98, bestätigt)
- Nicht übernehmen: Formeln der Anzahl-Expressions

**Validierung:**
- `uv run poe check`: ruff ✅, pyright 0 Fehler ✅, 102 Projekt-Python-Tests ✅, 216 FreeCAD-Python-Tests ✅.
- GUI-/manuelle Abnahme: G10 (`hole_grid` in der GUI, `Sieve_Pitch` ändern, Skizze vollständig bestimmt) offen. Braucht Ralf.

**Nachtrag (Ralfs Auftrag, Spec-Stand 6):**
- READMEs von HexFill und Lattice2 mit Ralfs Zustimmung live geladen. HexFill ist GUI-only, hat keine API und arbeitet nicht parametrisch. Entscheidung Ralf: kein Addon, HexFill weder angesteuert noch empfohlen (OF-10); Regel und G13 entfernt.
- `hole_grid` zu `fill_pattern` verallgemeinert: `cell` round/hex, `size` statt `diameter`, Sechseck-Zellen auf der Ecke mit gleichmäßigem Steg `pitch - size`. `add_profile polygon` kennt dafür `orientation` (`flat` | `pointy`).
- Messung headless: 918 runde Löcher inklusive Rasteränderung ≈ 5,8 s, Waben 100 × 80 mm inklusive Größenänderung ≈ 9 s. `poe check` grün (102 + 218 Tests).
- Release-Änderung ersetzt: `[feature][design]` `fill_pattern`: Sieb-, Loch-, Lüftungs- und Wabenraster in einem Aufruf, runde oder sechseckige Zellen, parametrisch, Anzahl fest oder aus der Feldgröße.
- `[feature][sketch]` `add_profile polygon` mit `orientation` `pointy` (Ecke unten).
- Live-Test in der GUI (FillTest, Platte 100 × 80 mit Rand 5 × 6): rund/rect 221 Löcher, rund/versetzt 238 Löcher, Waben 110 Zellen. Volumen rechnerisch exakt, alle Skizzen DoF 0, nach Änderung von Pitch und Size alles gültig. Befund: `field` nahm nur Zahlen an und folgte der Platte nicht. Behoben: `field` akzeptiert Parameter und Ausdrücke (`Plate_Width - 2*Rim_Width`), Test `test_field_bound_to_part_parameters_follows_the_part`. `poe check` grün (102 + 219).

**Nächste Session:**
- S6: #5.4 englische MCP-Ausgaben (Bestand), #5.1/#5.2 Doku und Release 0.2.0, #5.3 GUI-Abnahme G1–G12.

---

## Session 4a — 2026-09-28 (Ralfs Direktauftrag: Opt-in-Standard, Button-Paare)

**Ziel:** `--allow-addon-install` als Standard; die Schalter in FreeCAD wie „Bridge starten/stoppen“ als zwei Buttons.

**Erledigt:**
- Server: `allow_addon_install` standardmäßig an, `--allow-addon-install/--no-allow-addon-install`, Env `FREECAD_BUDDY_ALLOW_ADDON_INSTALL=0` schaltet ab.
- Bridge: `commands.py` mit `_Setting`/`_SetSetting`; je ein aktiver Button für an und aus (Autostart, Python, Addon-Installation). `Toggle*`-Befehle entfallen. Erzwingt eine Umgebungsvariable den Zustand, warnt die Konsole statt still nichts zu tun.
- Headless-Bridge bietet `addons.install` nie an (kein Dialog möglich). Der Doppel-Opt-in-Test hing sonst von Ralfs FreeCAD-Einstellung ab.

**Release-Änderungen:**
- `[feature][server]` `install_addon` ist serverseitig standardmäßig verfügbar, FreeCAD-Freischaltung und Dialog bleiben.
- `[feature][bridge]` Workbench-Schalter als Button-Paare (an/aus).

**Erkenntnisse:**
- Die Headless-Bridge liest die echten FreeCAD-Einstellungen des Nutzers. Tests dürfen sich darauf nicht verlassen.

**Validierung:**
- `poe check` grün: ruff, pyright 0 Fehler, 91 Projekt-Python-Tests, 157 FreeCAD-Python-Tests.
- GUI: Buttons in der Workbench offen (Teil von G9).

**Nächste Session:**
- S5 (Phase 3).

---

## Session 4 — 2026-09-28

**Ziel:** Phase 2, Addon-Installation mit doppeltem Opt-in, Dialog, Job-Muster und Aufräumen. Zusätzlich Ralfs neue Vorgabe: MCP-Ausgaben auf Englisch.

**Erledigt:**
- #2.4 `install.py` (Job-Modell, Dialog, AM-Backend, Fake-Backend-Schnittstelle), Opt-ins in FreeCAD und im Server, Tool `install_addon`.
- #2.5 Tests (Core, Server, Bridge). Kompatibilitätstest der AM-API mit echten Objekten aus dem Fixture. Import-Wächter mit gezielter Ausnahme für den Adapter.
- Spec-Stand 3: R-13, AC-17, #5.4 und OF-09 aufgenommen. Die neuen S4-Texte sind bereits englisch, der Bestand folgt in S6.
- Ralf hat die manuelle Probe von `search_addons` als einwandfrei bestätigt.

**Release-Änderungen:**
- `[feature][addons]` `install_addon` (opt-in auf beiden Seiten) installiert Addons und Makros über FreeCADs Addon Manager nach Bestätigung im FreeCAD-Dialog.
- `[feature][bridge]` Workbench-Befehl „Addon-Installation umschalten“.

**Blocker:**
- keine

**Erkenntnisse:**
- AM-Module lassen sich auch im headless FreeCAD-Python importieren. `AddonCatalog.get_addon_from_id` und `Addon.from_macro(Macro.from_cache(...))` funktionieren offline, das ist ideal für den Kompatibilitätstest.
- Beim asynchronen Workbench-Install muss das Aufräumen am Job-Ende passieren, nicht im `finally` des Starts.
- `ruff format` bricht lange Zeilen um. Ersetzungsskripte deshalb auf String-Inhalte zielen lassen, nicht auf ganze Statements.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md`
- Doku-Delta: Job-Muster und Sicherheitsmodell (98, bestätigt)
- Nicht übernehmen: Details des Fake-Backends

**Validierung:**
- `uv run poe check`: ruff ✅, pyright ✅, 90 Tests Projekt-Python ✅, 152 Tests FreeCAD-Python ✅.
- GUI-/manuelle Abnahme: G9 (Dialog, Ablehnen und Zustimmen an einem echten Addon) ist offen und braucht Ralf mit beiden Opt-ins und einem FreeCAD-Neustart.

**Nächste Session:**
- S5: #3.1 Grid-Recherche (Kandidaten aus S3: HexFill, FreeGrid, Gridfinity, CarteGrid, lattice2, Waben-Makros), #3.2 Vorschlagsliste (Tool-Budget klären), #3.3 `hole_grid`.

---

## Session 3 — 2026-09-28

**Ziel:** Phase 2, Spike Addon-Manager-API, Katalogsuche und Details.

**Erledigt:**
- #2.1 Spike per Code-Analyse (Agent) plus ein einmaliger Katalog-Download mit Ralfs Zustimmung. OF-02 ist abweichend von der Annahme entschieden: Suche im Server, Status und Installation in der Bridge.
- #2.2 Katalog-Parser, Service mit Cache, SHA-256 und Offline-Fallback, Tool `search_addons`, Bridge-Methode `addons.status`, Fixture aus dem echten Katalog.
- #2.3 Tool `get_addon` mit README-Auszug als markiertem Fremdtext.
- Probe auf dem vollständigen Katalog (438 Einträge): Die Suche „grid“ liefert FreeGrid, Gridfinity, CarteGrid und das Makro „BSurf from grid“, „perforation“ liefert HexFill, „honeycomb“ drei Makros plus HexFill. Das ist Vorarbeit für die Grid-Recherche (S5).

**Release-Änderungen:**
- `[feature][server]` `search_addons`: den offiziellen Addon-Katalog durchsuchen, mit Kompatibilität und Installationsstatus, offline aus dem Cache.
- `[feature][server]` `get_addon`: Details, Abhängigkeiten und README-Auszug eines Addons oder Makros.

**Blocker:**
- keine

**Erkenntnisse:**
- AM-Fallen für S4: Die Rückgabe von `AddonInstaller.run()` ist auch bei Fehlern `True`, nur `success` zählt. Der Konstruktor lädt ohne `allow_list` blockierend `constraints.txt`. `NetworkManager.InitializeNetworkManager()` muss im Hauptthread laufen. Downloads kommen von `addons.freecad.org/CatalogCache`.
- Der AM ignoriert offline seinen lokalen Cache (`new_cache_available` wirft außerhalb des `try`).
- Fremdinhalte (package.xml, README) sind Angriffsfläche: XML ohne DTD, README als Fremdtext markiert und nicht als Anweisung verwendet.
- Tool-Budget wird knapp, siehe Risiko im Sprint-Index.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: `docs/architecture.md`
- Doku-Delta: Aufteilung Server/Bridge für Addons (98, bestätigt)
- Nicht übernehmen: Zeilennummern aus dem Spike

**Validierung:**
- `uv run poe check`: ruff ✅, pyright ✅, 82 Tests Projekt-Python ✅, 144 Tests FreeCAD-Python ✅.
- GUI-/manuelle Abnahme: keine in dieser Session. Live-Suche in Claude Code nach Server-Neustart möglich.

**Nächste Session:**
- S4: #2.4 Installation mit Opt-in, Dialog, Job-Muster; #2.5 Tests.

---

## Session 2c — 2026-09-28 (Ralfs Direktaufträge: Auswahlgrößen, kompakter Chat)

**Ziel:** Zwei Rückmeldungen aus dem Live-Test umsetzen.

**Erledigt:**
- Auswahlgrößen: Body und jedes Buddy-Feature bekommen LineWidth 4 und PointSize 8 (`buddy_core/display.py`, aufgerufen in `create_body` und `features._new`). Überschreibbar über `Preferences/Mod/FreeCADBuddy` (`LineWidth`, `PointSize`). Hintergrund: FreeCADs globale Vorgaben greifen laut Ralf bei per Python erzeugten PartDesign-Objekten nicht (`02550bf`).
- Chat: Antwort-Blasen zeigen nur noch die Kernwerte als Text (erstellt/geändert, DoF, Volumen, Befunde, Kernwerte, Hinweise; bei Fehlern Code, Meldung und Hinweise). Das vollständige JSON steht erst in der Detailansicht (Enter) (`7834599`). Präzisierung von R-11, kein neuer Umfang.

**Release-Änderungen:**
- `[feature][core]` Dickere Kanten (4) und größere Punkte (8) an Body und Features für die Auswahl in der 3D-Ansicht.
- `[feature][tui]` Kompakte Antworten im Chat, vollständiges JSON per Enter.

**Blocker:**
- keine

**Erkenntnisse:**
- Die Wirkung der Auswahlgrößen lässt sich nur in der GUI prüfen. Headless ist nur die Logik getestet (`tests/core/test_display.py`, GUI per Monkeypatch).
- Ungeprüft: ob PartDesign die ViewObject-Werte beim Tip-Wechsel neu vom Vorgänger übernimmt. Buddy setzt sie deshalb an jedem Feature.

**Architektur-Erkenntnisse:**
- Betroffene Architektur-Doku: keine
- Doku-Delta: keins
- Nicht übernehmen: —

**Validierung:**
- `uv run poe check` (Exit-Code geprüft): ruff ✅, pyright ✅, 67 Tests Projekt-Python ✅, 141 Tests FreeCAD-Python ✅.
- GUI-/manuelle Abnahme: Auswahlgrößen und kompakter Chat werden in Ralfs nächstem Live-Aufbau gesichtet.

**Nächste Session:**
- FreeCAD und `freecad-buddy` neu starten, Platte aufbauen und sichten. Danach S3, Live-Katalog nur mit Zustimmung.

---

## Session 2b — 2026-09-28 (Live-Test mit Claude Code, Ansicht nach dem ersten Basis-Feature)

**Ziel:** Platte direkt über die MCP-Tools in Claude Code bauen und Ralfs Rückmeldung zur Startansicht umsetzen.

**Erledigt:**
- Testplatte über die MCP-Tools gebaut (Client `claude-code`): 12 Aufrufe, Volumen 98 994,7 mm³, 8 Undo-Schritte, keine Label-Probleme. Nicht gespeichert.
- Sichtung: Die Instructions kamen in Claude Code ungekürzt an (1 874 Zeichen). AC-01 ist damit per Sichtung belegt.
- Rückmeldung Ralf: Die Startansicht passt nicht, weil `set_view` im leeren Dokument nichts zum Einpassen hat. Jetzt setzt das erste Basis-Feature eines Bodys die Ansicht automatisch (iso und fit), die Regel verlangt nur noch den letzten Schritt.
- TUI-Test: Feste Pause durch Warten auf die Bedingung ersetzt, er war unter Last geflakt.

**Release-Änderungen:**
- `[bugfix][core]` Modellbaum zeigt den Ursprungspunkt von FreeCAD 26.3 nicht mehr als eigenes Objekt.
- `[feature][core]` Nach dem ersten `pad` bzw. `revolve` eines Bodys springt die FreeCAD-Ansicht auf iso und zeigt das ganze Bauteil, damit sich der Aufbau live verfolgen lässt.

**Blocker:**
- keine

**Erkenntnisse:**
- Deterministische Server-Logik ist verlässlicher als eine Regel, die der Agent befolgen muss, wenn der Zeitpunkt eindeutig ist (erstes Solid).
- `Origin001` („Ursprungspunkt“, `App::Point`) ist der Ursprungspunkt, den FreeCAD 26.3 in jedes Body-Origin legt. `model_tree` hat Origin-Elemente nach Typ gefiltert (`App::Line`, `App::Plane`) und den neuen Typ deshalb auf oberster Ebene angezeigt. Jetzt wird nach Zugehörigkeit zu `OriginFeatures` gefiltert. Der Regressionstest schlägt ohne den Fix fehl und ist mit dem Fix grün.

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
