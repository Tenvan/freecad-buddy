# Design-Stream mit Storepoints: Aufbau aufzeichnen, neu aufbauen, zurückspringen

> Erstellt: 2026-09-29 │ Status: ✅ Umgesetzt im Sprint [`freecad-buddy-storepoints`](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md) │ Priorität: mittel │ Architektur-Impact: mehrere

## Spezifikation

> Spec-Stand: 1 │ Spec-Status: Freigegeben │ Freigabe: Ralf im Chat, 2026-09-29 („ok, dann umsetzen“), inklusive der Annahmen OF-01 bis OF-05 als Entscheidungen; Umsetzung und Nachweise im Sprint

## Ausgangslage

Idee von Ralf (Chat, 2026-09-29): Die Aktionen eines Designs sollen als sequenzieller Stream mit Storepoints (Meilensteinen) gespeichert werden. Muss ein Design ohne Änderungen neu aufgebaut werden (z. B. nach FreeCAD-Update, bei Topologie-Problemen oder für eine Variante), oder soll zu einem bestimmten Punkt zurückgesprungen werden, entsteht ein neues Dokument, in das der Stream bis zum gewünschten Storepoint vorgespult wird.

Heutiger Stand, der das trägt:

- Jeder Tool-Aufruf ist genau eine FreeCAD-Transaktion mit vollständigen, serialisierbaren Argumenten (JSON über MCP).
- Referenzen laufen über Labels und Zwecke (`purpose`), nicht über interne Namen wie `Sketch001`; Labels entstehen deterministisch aus `naming.make_label` in Aufrufreihenfolge.
- Die TUI schreibt Tool-Aufrufe mit Argumenten und Ergebnis bereits als JSONL mit (`--log-file`), maskiert und gekürzt; ein Stream braucht dieselben Daten ungekürzt.
- `undo` ist ein Tool und damit selbst Teil des Streams.

Was fehlt: eine dokumentbezogene, dauerhafte Ablage des Streams, Storepoints als Marker, ein Replay in ein neues Dokument und der Umgang mit manuellen GUI-Änderungen zwischen den Aufrufen.

## Ziel

Ein Design lässt sich aus seinem Stream in einem neuen Dokument bis zu einem beliebigen Storepoint identisch neu aufbauen. Der Stream liegt beim Dokument, überlebt Speichern und Öffnen und ist für Menschen lesbar.

## Beteiligte und Zielgruppen

- **Ralf:** setzt Storepoints, baut Varianten und stellt Zwischenstände wieder her.
- **MCP-Client-Agent:** zeichnet nichts extra auf, der Server tut das; nutzt `replay` für Neuaufbau und Varianten.
- **Implementierender Agent:** setzt Aufzeichnung, Ablage, Storepoints und Replay um.

## Anforderungen

- **A-01 Aufzeichnung:** Jeder erfolgreiche mutierende Tool-Aufruf wird mit Tool-Name, Argumenten, Zeitstempel und Dokument in den Stream des Dokuments geschrieben; fehlgeschlagene (zurückgerollte) Aufrufe nicht. `undo` wird als eigener Eintrag aufgezeichnet oder kompaktiert den Stream (OF-02).
- **A-02 Ablage:** Der Stream liegt im Dokument selbst (z. B. als Eigenschaft eines versteckten Objekts oder im VarSet), damit er mit der FCStd-Datei gespeichert, kopiert und geöffnet wird. Ein Export als JSONL ist möglich.
- **A-03 Storepoints:** `storepoint(name)` markiert die aktuelle Position im Stream; Namen sind eindeutig je Dokument. Eine Liste mit Name, Position, Zeitstempel und Anzahl der Schritte seit dem letzten Storepoint ist abrufbar.
- **A-04 Replay:** `replay(storepoint, into)` legt ein neues Dokument an und führt die Einträge bis einschließlich des Storepoints in Reihenfolge aus. Ergebnis: Objektzahl, Labels und Volumen der Bodies stimmen mit dem Original zum Zeitpunkt des Storepoints überein. Fehlschlag eines Schritts bricht ab, meldet den Schritt und lässt das Teilergebnis zur Inspektion stehen.
- **A-05 Manuelle Änderungen:** Änderungen, die Ralf in der GUI zwischen zwei Aufrufen macht, sind nicht im Stream. Der Server erkennt sie (Objektzahl oder Undo-Namen ohne Buddy-Präfix) und markiert im Stream einen Eintrag `manual_edit`; `replay` warnt an dieser Stelle und bietet als Fallback den letzten Dokument-Snapshot (OF-03). *Der Snapshot-Fallback im Replay ist bewusst zurückgestellt, siehe Backlog-Eingang; `storepoint(snapshot=true)` speichert die Kopie.*
- **A-06 Sicherheit und Sprache:** Kein Replay von `execute_python` ohne dessen Opt-in; `install_addon` wird nie erneut ausgeführt, sondern als Voraussetzung gemeldet. Alle MCP-Ausgaben englisch.
- **A-07 Budget:** Höchstens drei neue Tools (`storepoint`, `list_storepoints`, `replay`); Tool-Budget bleibt ≤ 100.
- **A-08 Sichtbarkeit im Modellbaum (Ralf, Chat 2026-09-29):** Ein Storepoint ist in FreeCAD sichtbar, ohne Labels zu verändern (Labels sind Referenzen):
  - (a) als Beschreibung (`Label2`) auf dem Feature, das zum Zeitpunkt des Storepoints Tip des Bodys war, z. B. „◆ Storepoint 2: Deckel fertig“. FreeCAD zeigt `Label2` in der einblendbaren Spalte „Beschreibung“ (Rechtsklick in den Baum), nicht als Hover-Tooltip (in der GUI-Abnahme G14 am 2026-09-30 geprüft). Damit steht der Storepoint an der richtigen Stelle in der Feature-Kette.
  - (b) als Marker-Objekt in einer Gruppe `Storepoints` an der Dokumentwurzel, ein Objekt je Storepoint (`App::FeaturePython` ohne Shape) mit Link auf das Feature, Zeitstempel und Schrittzahl; eigenes Icon über einen ViewProvider des Addons, Auswahl des Markers markiert das verlinkte Feature. Ohne installiertes Addon lädt das Dokument trotzdem (generisches Icon, Proxy-Warnung).
  - In den Body selbst lässt sich kein Marker einfügen; PartDesign nimmt dort nur Features, Skizzen, Datums und Binder (vermutet, im Spike prüfen).
  - `undo` eines Storepoints entfernt Beschreibung und Marker wieder (beides in derselben Transaktion).

## Nicht-Ziele

- Versionsverwaltung mit Diff und Merge zwischen Streams.
- Aufzeichnung der GUI-Bedienung selbst (Sketcher-Interaktionen); manuelle Änderungen werden nur erkannt, nicht rekonstruiert.
- Replay über Dokumentgrenzen (Assembly aus mehreren Dateien) im ersten Schritt.
- Replay per Doppelklick auf einen Marker in der GUI; im ersten Schritt läuft Replay nur über das Tool.

## Regeln und Einschränkungen

- Bestehende Verträge bleiben: Tool = eine Transaktion, Labels als Referenzen, englische Ausgaben.
- Der Stream darf keine Geheimnisse enthalten (Tokens werden vor der Ablage maskiert wie im TUI-Log).
- Die Aufzeichnung darf einen Tool-Aufruf nicht messbar verlangsamen (< 5 ms) und blockiert nie die GUI.
- Der Stream ist an die Tool-Signaturen der jeweiligen Version gebunden; ein Eintrag trägt die Buddy-Version, `replay` warnt bei Abweichung.

## Beispiele

- Box mit Deckel: 40 Aufrufe, `storepoint("Grundkörper")` nach dem Pad, `storepoint("Deckel fertig")` am Ende → `replay("Grundkörper", into="Box_Variante")` liefert ein Dokument mit nur dem Grundkörper, bereit für eine andere Deckelvariante.
- FreeCAD-Update bricht ein Fillet → `replay("Deckel fertig", into="Box_neu")` baut alles neu; das Fillet scheitert, `replay` meldet Schritt 37 mit dem Fehler, das Dokument bleibt bis Schritt 36 stehen.
- Ralf verschiebt in der GUI eine Skizze von Hand → Stream erhält `manual_edit` nach Schritt 12; `replay` bis „Deckel fertig“ warnt, dass ab Schritt 12 Abweichungen möglich sind.

## Ausnahme- und Fehlerfälle

- Storepoint-Name existiert schon → `validation` mit Liste der vorhandenen.
- `replay` auf einen unbekannten Storepoint → `not_found` mit Liste.
- Zieldokument existiert → `validation` (kein Überschreiben).
- Eintrag verweist auf ein Addon-Tool (`add_gear`, `add_fastener`) ohne installiertes Addon → Abbruch mit Hinweis vor dem ersten Schritt. *Bewusst zurückgestellt, siehe Backlog-Eingang.*
- Stream fehlt im Dokument (älteres Modell) → `list_storepoints` liefert leer mit Hinweis; Aufzeichnung beginnt ab jetzt.

## Akzeptanzkriterien

AC-01 bis AC-10 sind erfüllt laut [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md#umsetzung-und-nachweis); dort stehen Nachweis und Prüfebene. Der Wortlaut unten bleibt der Stand der Spezifikation.

- [x] AC-01: Nach einem Referenzprojekt enthält der Stream jeden mutierenden Aufruf in Reihenfolge; ein zurückgerollter Aufruf fehlt.
- [x] AC-02: Der Stream überlebt Speichern, Schließen und Öffnen des Dokuments.
- [x] AC-03: `storepoint` und `list_storepoints` verhalten sich wie A-03, doppelte Namen werden abgelehnt.
- [x] AC-04: `replay` bis zum letzten Storepoint eines Referenzprojekts ergibt in einem neuen Dokument dieselben Labels und Body-Volumen (< 0,1 % Abweichung) wie das Original.
- [x] AC-05: `replay` bis zu einem mittleren Storepoint enthält genau die Objekte bis dahin.
- [x] AC-06: Ein absichtlich scheiternder Schritt bricht das Replay mit Schrittnummer und Fehler ab; das Teilergebnis bleibt.
- [x] AC-07: Eine manuelle GUI-Änderung wird als `manual_edit` markiert und `replay` warnt (GUI-Anteil Nutzerabnahme, headless über simulierte Fremdtransaktion).
- [x] AC-08: `execute_python`-Einträge werden ohne Opt-in übersprungen und gemeldet; `install_addon` wird nie erneut ausgeführt.
- [x] AC-09: Tool-Budget ≤ 100, `uv run poe check` grün, keine deutschen MCP-Texte.
- [x] AC-10: Nach `storepoint("Grundkörper")` trägt das Tip-Feature die Beschreibung „◆ Storepoint 1: Grundkörper“ und die Gruppe `Storepoints` enthält einen Marker mit Link auf dieses Feature; nach `undo` ist beides weg (headless). Sichtbarkeit von Beschreibungsspalte und Marker-Icon in der GUI als Nutzerabnahme.

## Offene Fragen

| ID | Frage | Betroffen | Annahme bis Klärung | Verantwortlich |
|---|---|---|---|---|
| OF-01 | Ablage im Dokument (verstecktes `App::FeaturePython` mit String-Property) oder Sidecar-Datei neben der FCStd? | A-02 | Im Dokument, weil Kopieren und Öffnen dann automatisch funktionieren; Sidecar nur als Export | Ralf |
| OF-02 | `undo` als Eintrag aufzeichnen oder den Stream kompaktieren (zurückgenommene Schritte entfernen)? | A-01 | Kompaktieren, damit Replay linear bleibt; `undo` selbst erscheint nicht im Stream | Ralf |
| OF-03 | Snapshot-Fallback bei manuellen Änderungen: FCStd-Kopie je Storepoint speichern? | A-05 | Ja, optional per Parameter `snapshot=true` in `storepoint`, Ablage neben der FCStd | Ralf |
| OF-04 | Soll `replay` optional Argumente überschreiben können (z. B. Parameterwerte) für Varianten? | A-04 | Nein im ersten Schritt; Varianten entstehen nach dem Replay über `set_parameters` | Ralf |
| OF-05 | Baum-Anzeige nur als Beschreibung (a), nur als Marker-Gruppe (b) oder beides? | A-08, AC-10 | Beides: (a) zeigt die Stelle in der Feature-Kette, (b) liefert die Liste mit Icon und Zeitstempel | Ralf |

## Umsetzung und Nachweis

| Kriterium | Geplante Aufgabe / Schritte | Prüfebene und erwartetes Ergebnis | Nachweis / Status |
|---|---|---|---|
| AC-01, AC-02 | ~~Aufzeichnung im Server (`ToolContext.call` nach Erfolg) → Bridge-Methode `stream.append` schreibt in das Dokument~~ abgelöst durch Registry-Aufzeichnung, siehe Sprint-Entscheidungen | Headless-Core-Test + E2E über MCP | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md#umsetzung-und-nachweis) |
| AC-03 | `storepoint`, `list_storepoints` | Headless-Core-Test | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md#umsetzung-und-nachweis) |
| AC-04, AC-05, AC-06 | `replay` im Server (führt Tool-Aufrufe erneut aus) mit Referenzprojekt-Fixture | E2E-Test über MCP (Referenzprojekt) | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md#umsetzung-und-nachweis) |
| AC-07 | Erkennung fremder Transaktionen in der Bridge | Headless-Core-Test + GUI-Nutzerabnahme | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md#umsetzung-und-nachweis) |
| AC-08 | Filter für `execute_python`/`install_addon` | Unit-Test Server | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md#umsetzung-und-nachweis) |
| AC-09 | Doku, `poe check` | `uv run poe check` | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md#umsetzung-und-nachweis) |
| AC-10 | `Label2` auf dem Tip-Feature, Gruppe `Storepoints` mit Marker-Objekten und ViewProvider-Icon im Addon | Headless-Core-Test + GUI-Nutzerabnahme (Beschreibungsspalte, Icon) | erfüllt, siehe [Sprint-Index](../../3-sprints-erledigt/2026-09-freecad-buddy-storepoints/00-index.md#umsetzung-und-nachweis) (GUI G14 bestanden 2026-09-30) |

Umsetzung folgt dem freigegebenen Spec-Stand. Browser-/manuelle Prüfungen zusätzlich nach der [Abnahmefreigabe](../../README.md#browser--und-manuelle-abnahmeprüfungen) behandeln; Spec-Freigabe ist keine Testfreigabe.

## Architektur-Impact

| Bereich | Einschätzung |
|---|---|
| `docs/architecture.md` | aktualisieren: neuer Datenfluss „Design-Stream“ (Server zeichnet auf, Dokument speichert, Server spielt ab), Abschnitt Transaktionen (Erkennung fremder Transaktionen) |

Relevante Architekturfragen (Schichten core / bridge / server, RPC-Vertrag, Modellierungsregeln):

- Aufzeichnung gehört in den Server (er kennt Tool-Name und Argumente), die Ablage in den Core (Dokument); `replay` ruft die Tools über denselben Weg wie ein Client auf, damit es keine zweite Ausführungslogik gibt. *Abgelöst durch Registry-Aufzeichnung und Replay in der Bridge, siehe Sprint-Entscheidungen.*
- Der Stream ist ein weiteres Artefakt im Dokument neben dem VarSet `Parameters`; Regel: Die Gruppe `Storepoints` ist im Modellbaum sichtbar (A-08), der Stream bleibt eine Property dieser Gruppe und ist kein Feature.
- Erkennung manueller Änderungen nutzt `ensure_user_not_editing` und die Undo-Namen (Buddy-Transaktionen tragen Präfixe wie `Pad:`).

## Relevante Dateien / Module

- `src/buddy_server/tools/base.py` (`ToolContext.call`), `src/buddy_server/logs.py` (JSONL-Log, Maskierung)
- `addon/FreeCADBuddy/buddy_core/documents.py` (`undo`, Dokumentlebenszyklus), `addon/FreeCADBuddy/buddy_core/transaction.py`
- `addon/FreeCADBuddy/buddy_bridge/methods.py`
- `examples/reference_projects.py` (Fixture für Replay-Tests)
- `docs/architecture.md`, `docs/tools.md`

## Abhängigkeiten

- Sprint `freecad-buddy-partdesign` sollte abgeschlossen sein (Tool-Signaturen stabil, bevor Streams daran gebunden werden).

## Notizen

AUTO-RESUME START

**Start-Prompt:** Setze das Ticket `design-stream-storepoints` um. Kläre zuerst OF-01 bis OF-04 mit Ralf oder übernimm die Annahmen. Beginne mit der Aufzeichnung (A-01, A-02) und einem Headless-Test, dann Storepoints, dann `replay` gegen das Referenzprojekt Box mit Deckel. GUI-Prüfung AC-07 nur nach ausdrücklicher Freigabe.

**Lies zuerst:**

- dieses Ticket, Abschnitte Anforderungen und Offene Fragen
- `src/buddy_server/tools/base.py` (`ToolContext.call`: hier hängt die Aufzeichnung)
- `src/buddy_server/logs.py` (Maskierung wiederverwenden)
- `addon/FreeCADBuddy/buddy_core/transaction.py` (Undo-Namen, Fremdtransaktionen)
- `docs/architecture.md`, Abschnitt Transaktionen und Ergebnisvertrag

AUTO-RESUME ENDE

**Machbarkeit (Einschätzung Agent, 2026-09-29):** Umsetzbar mit geringem Risiko, weil die Tools bereits deterministisch über Labels arbeiten und Argumente JSON sind. Die beiden echten Schwierigkeiten sind manuelle GUI-Änderungen (nicht rekonstruierbar, nur erkennbar) und Tools mit Nebenwirkungen (`install_addon`, `execute_python`). Replay-Dauer entspricht der ursprünglichen Bauzeit; `model_thread`-Löcher dominieren.

**Release-Änderungen (Sprint-Session-Log):** `[feature][server]` Stream und Replay, `[feature][core]` Ablage im Dokument, `[doc][docs]` Architektur.

## Übergabe an Sprint-Planung

- Architektur-Update-Artefakt nötig: ja (`98-architecture-update.md`, Datenfluss Design-Stream)
- Vermutete Ziel-Dokumente: `docs/architecture.md`, `docs/tools.md`
- Offene Klärungen vor Umsetzung: OF-01 bis OF-05
