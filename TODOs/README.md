# TODOs — Konventionen & Lebenszyklus

Zentrale Ablage für alle Tasks, Pläne und Backlog-Einträge des Projekts **FreeCAD Buddy** (eigener MCP-Server für PartDesign/Sketcher-basierte 3D-Druck-Projekte).

## Verzeichnisstruktur

```
TODOs/
├── README.md                          # diese Datei
├── master-todo.md                     # manuell gepflegter Gesamtindex (kein Generator vorhanden)
├── roadmap.md                         # Reihenfolge der kommenden Sprints, je Sprint eine Domäne
│
├── 0-vorlagen/                        # Templates für neue Sprints/Tickets
├── 1-backlog/<domain>/                # Backlog je Domain mit 00-index.md
├── 2-sprints-aktiv/<sprint>/          # Laufende Sprints
├── 3-sprints-erledigt/<YYYY-MM-name>/ # Abgeschlossene Sprints
├── 4-archiv/                          # Endgültig stillgelegt
└── 5-konzepte/                        # Architektur-/Designdocs (read-only)
```

## Lebenszyklus eines Tickets

```
1-backlog/<domain>/<thema>.md
       │
       │  Beim Einplanen: zu Sprint formen
       ▼
2-sprints-aktiv/<sprint-name>/
        ├── 00-index.md
        ├── 01-<phase>.md … 0N-<phase>.md
        ├── 97-review.md
        ├── 98-architecture-update.md
        └── 99-session-log.md
       │
       │  Bei Abschluss (erst nach Review-Gate): Selbst-Move mit Datum-Präfix
       ▼
3-sprints-erledigt/YYYY-MM-<sprint-name>/
       │
       │  Nach Quartal o. Ä.
       ▼
4-archiv/<YYYY>/<sprint-name>/
```

## Arbeitsweise

Verbindlich ab 2026-09-29 für neue Sprints. Die Reihenfolge der Sprints und die Domänen-Tabelle stehen in [`roadmap.md`](roadmap.md).

### Backlog-Eingang

- Jede Idee und jedes Problem wird **sofort** als eine Zeile im Abschnitt „Eingang“ des Backlog-Index eingetragen: ID (`E-NN`), Datum, Domäne, Typ (`idee` / `problem` / `schuld`), ein Satz, Quelle. Eine Spezifikation ist dafür nicht nötig.
- Der Agent trägt Befunde außerhalb des Session-Umfangs selbst ein, statt sie nebenbei zu beheben.
- Triage bei jeder Sprint-Planung: Zeile wird zu einem Ticket (SDD), an ein bestehendes Ticket angehängt oder gelöscht. Übernommene Zeilen verweisen auf ihr Ticket, bis dieses umgesetzt ist.

### Sprint-Zuschnitt

- **Eine Domäne je Sprint.** Frameworks/Abhängigkeiten (`infra`), `server`, `bridge`, `core`, `tui`, `regelwerk` und `abnahme` werden nicht gemischt. Einzige Ausnahme ist der Feature-Durchstich (`core` + dünner Server-Wrapper + generierte Tool-Doku, siehe Roadmap).
- **Klein:** höchstens 3 Sessions und etwa 6 Aufgaben je Sprint, eine Spezifikation. Größere Vorhaben werden auf mehrere Sprints verteilt.
- **Nicht mischen:** Feature, Refactoring, Regelwerk und Infrastruktur stehen nie im selben Sprint.
- **WIP-Grenze:** höchstens ein Umsetzungs-Sprint aktiv; zusätzlich darf ein Sprint auf Abnahme durch Ralf warten.
- **Start-Commit:** Der Sprint-Index nennt den Commit, auf dem der Sprint startet. Er ist die Basis des Review-Gates.

### Session-Regeln (niedrige Komplexität)

- Eine Session setzt genau ein Session-Paket um und endet mit grünem `uv run poe check` und einem Commit.
- Neuer oder geänderter Code bleibt bei zyklomatischer Komplexität ≤ 10 (`uv run ruff check --select C901 .`); die bestehende Baseline darf nicht wachsen.
- Dateien über 400 Zeilen wachsen nicht weiter; eine nötige Aufteilung geht als `schuld` in den Eingang.
- Keine neue Abhängigkeit und kein Framework-Update außerhalb eines `infra`-Sprints.
- Der Session-Log-Eintrag enthält die Zeile `Komplexität:` (neue `C901`-Befunde, gewachsene Dateien, oder „unverändert“).

### Review-Gate (Sprint-Abnahme)

Ein Sprint ist erst abgenommen, wenn **alle** im Sprint erstellten oder geänderten Dateien reviewt sind:

1. In einer frischen Session die Dateiliste erzeugen: `git diff --name-status <Start-Commit>..HEAD` und in `97-review.md` eintragen (Vorlage `sprint-review.template.md`).
2. Jede Datei vollständig lesen und bewerten: Korrektheit, Komplexität, Lesbarkeit und Konsistenz mit dem umgebenden Code, passende Tests und Doku.
3. Unterstützend `/code-review high` über den Sprint-Bereich und `/simplify` laufen lassen; deren Befunde fließen in dieselbe Tabelle.
4. Befunde im Sprint-Umfang sofort beheben (danach `uv run poe check`), alle anderen in den Eingang.
5. Ralf bestätigt die Abnahme im Chat; das Datum steht in `97-review.md`. Erst danach wird der Sprint nach `3-sprints-erledigt/` verschoben.

## Release-Änderungen

Eine Release-Queue (`pending-release-log.md`) ist in diesem Projekt derzeit **nicht** eingerichtet. Release-relevante Änderungen werden je Session im `99-session-log.md` des Sprints unter `Release-Änderungen` im Format `[feature|bugfix|doc|removal|misc|skip][scope]` gepflegt und bilden die Quelle für ein späteres `CHANGELOG.md`.

## Naming (verbindlich)

| Element | Pattern | Beispiel |
|---|---|---|
| Top-Level-Nummern-Ordner | `<N>-<name>` lowercase | `0-vorlagen` |
| Sprint-Ordner aktiv | `<name>` lowercase kebab-case | `freecad-buddy-aufbau` |
| Sprint-Ordner erledigt | `YYYY-MM-<name>` lowercase | `2026-05-cleanup-sprint` (Datum = Abschluss) |
| Backlog-Domain-Ordner | `<domain>` lowercase | `freecad-buddy` |
| Index-Datei | `00-index.md` | – |
| Phasen-Datei | `<NN>-<thema>.md` lowercase | `01-vorbereitung.md` |
| Session-Log | `99-session-log.md` | – |
| Sprint-Review | `97-review.md` | – |
| Architektur-Update | `98-architecture-update.md` | – |
| Backlog-Ticket | `<thema>.md` lowercase kebab-case | `kommissionierung-update.md` |
| Templates | `<typ>.template.md` | `sprint-phase.template.md` |
| Auto-Generat | `master-todo.md` lowercase | – |
| **Einzige Ausnahme** | **`README.md`** Grossbuchstaben | OS-Konvention |

**Verboten in neuen Dateien:**

- `_<name>.md` Hilfs-Präfixe (Triage-Notizen statt in Phasen-Dateien einarbeiten)
- `UPPER_SNAKE_CASE.md` (historisch im `Archiv/` zu sehen)
- Punkte, Leerzeichen, Umlaute in Datei-/Ordnernamen

## Pflichtbestandteile

### In jedem Sprint-Ordner

- `00-index.md` mit:
  - Ziel, Phasen-Übersicht (Tabelle mit Fortschritt)
  - Session-Übersicht
  - Abhängigkeits-Graph (Mermaid optional)
  - Architektur-Update und Sprint-Abschluss-Gates
  - Architektur-Doku-Ziel ist `docs/architecture.md` (entsteht in Sprint `freecad-buddy-aufbau`, Session S1)
- `0N-<phase>.md` für jede Phase mit:
  - Session-Pakete, Active Tasks, Done Tasks
- `98-architecture-update.md` für Architektur-Deltas, die am Sprint-Ende in `docs/architecture.md` übernommen oder begründet verworfen werden
- `99-session-log.md` für chronologisches Protokoll

### In jedem Backlog-Domain-Ordner

- `00-index.md` mit:
  - Übersicht der Tickets nach Priorität
  - Status pro Ticket (🔴/🟡/🔵/✅)

## Status-Marker

| Marker | Bedeutung |
|---|---|
| 🔴 | Nicht gestartet / kritisch |
| 🟡 | In Vorbereitung / Folgetask |
| 🔵 | Aktiv / in Arbeit |
| ✅ | Erledigt |
| ⏸️ | Pausiert |
| ❌ | Verworfen |

## master-todo.md

`master-todo.md` wird **manuell** gepflegt, da im Projekt kein Index-Generator existiert. Bei neuem Sprint, Sprint-Abschluss oder neuer Backlog-Domain die passende Zeile ergänzen bzw. verschieben.

## Spec-Driven Development (SDD)

Neue Backlog-Tickets und Sprints werden mit `todo-planner` spezifikationsgetrieben geplant: **Spezifikation → Klärung/Freigabe → Umsetzungsplan → Umsetzung → Nachweis**. Die Spezifikation steht im Ticket beziehungsweise im Sprint-Index; eine zusätzliche Spec-Datei ist nicht erforderlich.

- **Geltungsbereich:** Die Definition und Vorlagen sind auf SDD umgestellt. Bereits bestehende Tickets und Sprints behalten ihren Stand. Ihre Migration erfolgt ausschließlich auf ausdrückliche Aufforderung für die benannten Ziele, nicht bei Statusupdates, Ergänzungen oder beim Laden neuer Vorlagen. Ein neuer Sprint aus einem alten Backlog folgt SDD, ohne das Quellticket automatisch umzuschreiben.
- **Spezifikation:** Der Dokumenttitel ist der Spec-Titel. Die zehn unten genannten Rubriken bilden den fachlichen Vertrag vor dem Umsetzungsplan. Akzeptanzkriterien erhalten stabile IDs wie `AC-01` und beschreiben beobachtbares Verhalten statt Implementierungsschritte.
- **Freigabe:** Spec-Stand, Status `Entwurf` oder `Freigegeben`, offene Entscheidungen und Freigabenachweis dokumentieren. Neue Spezifikationen starten als Entwurf. Umsetzung erst für den ausdrücklich freigegebenen Stand ohne blockierende Fachentscheidungen; technische Entwürfe dürfen vorher geplant werden. Historische Freigaben nicht erfinden.
- **Ableitung:** Jede Umsetzungsaufgabe verweist auf Kriterien-IDs oder eine begründete technische Voraussetzung. Jedem Kriterium eine Aufgabe und die kleinste ausreichende Prüfebene zuordnen. Unverändert übernommene Quellspezifikationen mit Pfad und Stand referenzieren statt duplizieren; IDs bei mehreren Quellen mit dem Quelldokument qualifizieren.
- **Änderungen:** Geänderte Anforderungen zuerst in der Spezifikation und ihrem Stand nachziehen, betroffene Aufgaben/Nachweise abgleichen und geänderten Umfang erneut freigeben lassen. Kriterien nicht nachträglich an die Implementierung anpassen, nur damit sie erfüllt erscheinen.
- **Nachweis:** Ergebnisse den Kriterien zuordnen; Umsetzung ist nicht automatisch Abnahme. Gültige Nutzer-/Agentennachweise erhalten. Nicht erfüllte Kriterien bleiben offen oder werden durch eine ausdrückliche Scope-Entscheidung mit Folgeaufgabe zurückgestellt.

Verbindliche Spec-Rubriken für neue oder ausdrücklich migrierte Tickets und Sprint-Indizes:

| Rubrik | Inhalt |
|---|---|
| Ausgangslage | Welches Problem besteht? |
| Ziel | Welches Ergebnis soll erreicht werden? |
| Beteiligte und Zielgruppen | Wer benutzt oder verantwortet das Ergebnis? |
| Anforderungen | Was muss das Ergebnis leisten? |
| Nicht-Ziele | Was ist ausdrücklich nicht Teil der Aufgabe? |
| Regeln und Einschränkungen | Welche fachlichen, technischen oder organisatorischen Grenzen gelten? |
| Beispiele | Wie sehen typische Fälle und ihre erwarteten Ergebnisse aus? |
| Ausnahme- und Fehlerfälle | Was passiert bei ungültigen oder ungewöhnlichen Situationen? |
| Akzeptanzkriterien | Welche objektiv überprüfbaren Bedingungen müssen erfüllt sein? |
| Offene Fragen | Was muss noch entschieden werden? |

Rubriken in dieser Reihenfolge knapp ausfüllen; „nicht relevant“ nur mit Begründung, unbekannte Angaben als offene Fragen kennzeichnen. Unveränderte freigegebene Quellen pro Rubrik referenzieren statt ihren Inhalt zu duplizieren. Spec-Stand und Freigabe bleiben Metadaten. Beispiele beschreiben Verhalten und sind keine zusätzlichen automatischen Testaufträge.

**Spec-Freigabe ist keine Browser-Testfreigabe.** Die folgende Abnahmeregel bleibt unverändert und gilt unabhängig von SDD auch für bestehende Pläne. SDD fordert keine zusätzlichen Browserläufe oder vollständigen Testmatrizen.

## Browser- und manuelle Abnahmeprüfungen

Verbindlich für bestehende und neue Sprints sowie Backlog-Pläne:

- Browser- und manuelle Abnahmeprüfungen vorab konkret auflisten: Ablauf, erwartetes Ergebnis und betroffener Umfang. Akzeptanzkriterien allein sind kein Auftrag zu Browserprüfungen.
- Vor der Ausführung fragen: „Welche dieser Prüfungen hast du bereits selbst durchgeführt und bestätigt, und welche verbleibenden Prüfungen soll der Agent übernehmen?“
- Nur die ausdrücklich freigegebenen Prüfungen ausführen. „Noch nicht selbst geprüft“, ein offenes TODO oder ein allgemeiner Umsetzungsauftrag gelten nicht als Freigabe. Ohne Antwort bleibt die Prüfung offen.
- Zusätzliche oder erneute Prüfungen benötigen eine neue Freigabe. Kein automatisches Ausweiten auf weitere Seiten, Zustände, Viewports oder explorative Durchläufe.
- Bereits bestätigte Ergebnisse übernehmen, nicht bei jeder Session oder beim Sprint-Abschluss erneut prüfen. Ändert sich die relevante Grundlage, den betroffenen Nachweis als erneut zu prüfen markieren und eine neue Freigabe einholen.
- Nutzerbestätigungen, Agentenfreigaben und Ergebnisse mit Prüfumfang im Backlog-Ticket beziehungsweise in `99-session-log.md` dokumentieren und aus der Phase referenzieren. Nutzerprüfungen nicht als vom Agenten ausgeführt ausgeben.

Diese Freigaberegel betrifft Browser- und manuelle Abnahmeprüfungen. **In diesem Projekt zählen dazu insbesondere Prüfungen in der laufenden FreeCAD-GUI** (Modellbaum sichten, Skizze öffnen und manuell bearbeiten, Maß ändern und Recompute beobachten) sowie Probedrucke. Gezielte Unit-/Komponententests während der Implementierung sowie bestehende Build- und Komplexitätsregeln bleiben unverändert. Browser-Skills beschreiben die Ausführung, ersetzen aber weder Testplanung noch Freigabe.

GUI-Prüfungen, die der Agent über `execute_python` in der laufenden GUI ausführt ([`tools/gui_checks.py`](../tools/gui_checks.py), siehe [`docs/acceptance.md`](../docs/acceptance.md#agentengestützte-prüfung)), sind Agentenprüfungen im Sinne dieser Regel: Sie brauchen die Freigabe der konkreten Prüfung **und** Ralfs Freischaltung von `execute_python` in der TUI (`p`), die er danach wieder abschaltet. Der Agent schaltet `execute_python` nie selbst frei.

## Vorlagen

Neue Sprints/Tickets aus den Templates in `0-vorlagen/` ableiten:

| Vorlage | Verwendung |
|---|---|
| `sprint-00-index.template.md` | Sprint-Index |
| `sprint-phase.template.md` | Phasen-Datei |
| `sprint-session-log.template.md` | Session-Log |
| `architecture-update.template.md` | Architektur-Deltas und Abschlussprüfung für `docs/architecture.md` |
| `sprint-review.template.md` | Review-Gate: Dateiliste, Bewertung je Datei, Abnahme |
| `backlog-domain-index.template.md` | `00-index.md` einer Backlog-Domain |
| `backlog-ticket.template.md` | Einzelnes Backlog-Ticket |

## Konzepte vs. TODOs

`5-konzepte/` enthält **Architektur- und Designdokumente** (read-only Referenz), keine ausführbaren Tasks. TODOs gehoeren in Sprints oder Backlog.
