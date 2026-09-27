# TODOs — Konventionen & Lebenszyklus

Zentrale Ablage für alle Tasks, Pläne und Backlog-Einträge des Projekts **FreeCAD Buddy** (eigener MCP-Server für PartDesign/Sketcher-basierte 3D-Druck-Projekte).

## Verzeichnisstruktur

```
TODOs/
├── README.md                          # diese Datei
├── master-todo.md                     # manuell gepflegter Gesamtindex (kein Generator vorhanden)
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
        ├── 98-architecture-update.md
        └── 99-session-log.md
       │
       │  Bei Abschluss: Selbst-Move mit Datum-Präfix
       ▼
3-sprints-erledigt/YYYY-MM-<sprint-name>/
       │
       │  Nach Quartal o. Ä.
       ▼
4-archiv/<YYYY>/<sprint-name>/
```

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

## Vorlagen

Neue Sprints/Tickets aus den Templates in `0-vorlagen/` ableiten:

| Vorlage | Verwendung |
|---|---|
| `sprint-00-index.template.md` | Sprint-Index |
| `sprint-phase.template.md` | Phasen-Datei |
| `sprint-session-log.template.md` | Session-Log |
| `architecture-update.template.md` | Architektur-Deltas und Abschlussprüfung für `docs/architecture.md` |
| `backlog-domain-index.template.md` | `00-index.md` einer Backlog-Domain |
| `backlog-ticket.template.md` | Einzelnes Backlog-Ticket |

## Konzepte vs. TODOs

`5-konzepte/` enthält **Architektur- und Designdokumente** (read-only Referenz), keine ausführbaren Tasks. TODOs gehoeren in Sprints oder Backlog.
