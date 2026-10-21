# Rollenverträge

[English](../../role-contracts.md) · [Русский](../ru/role-contracts.md) · [Deutsch](role-contracts.md) · [简体中文](../zh-CN/role-contracts.md)

Teams definieren Mitglieder/Skills; Profile wählen Modelle; Markdown-Quelldateien des Teams liefern
begrenzte Ausführungsanweisungen. Der Root-Vertrag ist `teams/<team>/coordinator.md`,
keine zusätzliche Subagentenrolle.


Die Quelle liegt unter `teams/<team>/agents/<role>.md`: TOML-Metadaten zwischen
`+++`, gefolgt von Markdown-Anweisungen. Teams bleiben auch bei gleichen Rollennamen
unabhängig. Modelle bleiben in Profilen, Skill-Bindungen in `team.toml`.

Pflichtfelder: `name`, `description`, `access` (`read-only` oder `workspace-write`)
sowie die booleschen Felder `web` und `delegation`. Der Renderer bildet sie auf die
bestehenden nativen Sandbox-/Werkzeugeinstellungen ab. Schreibgeschützte Rollen
dürfen nicht delegieren. Codex nutzt die Sandbox, Claude Werkzeuglisten für
schreibgeschützte Rollen, Antigravity explizite Werkzeuglisten. Client-Berechtigungen
und Auftragsbefugnisse gelten weiterhin. Team-Quellen bearbeiten und die Installation
aktualisieren; generierte Rollen nicht direkt ändern.

Claude-Rollen mit `delegation = false` sperren außerdem das native Werkzeug `Agent` über `disallowedTools`, auch bei Schreibzugriff.

## Format

Für Root-Koordinatoren und Subagenten dieselben Blöcke verwenden. Mit kurzem Zweck und Auswahlkriterien beginnen, danach:

| Abschnitt | Inhalt |
|---|---|
| Skill activation, falls nötig | Voraussetzungen, zu ladende Anweisungen und Startbelege |
| Working mode | Reihenfolge, Eingaben und fehlende Voraussetzungen |
| Focus on | Auftragsspezifische Schwerpunkte |
| Quality checks | Abschlussbelege |
| Return | Pfade, Ergebnisse, offene Befunde/Entscheidungen |
| Boundaries | Schreibbereich, Delegationsbefugnis und Stopps |

Konkrete, kurze Schritte mit gleicher Semantik für alle Clients verwenden.
Keine generischen zweiten Koordinatoren, willkürlichen Befundquoten oder Pflichtaufrufe
optionaler Rollen. Jede Rolle hat eine Quelle innerhalb ihres Teams; Client-Renderer erzeugen die nativen Formate.

Koordinatoren verwenden Markdown-Überschriften; Zweck und Blöcke entsprechen den Rollenquellen. Routing und Integration als Root-Verantwortung ausweisen. Der Plex-Skill lädt den Koordinator; er wird nicht als zusätzlicher nativer Subagent registriert.

## Verbindliche Aufgabenbewertung

Nach Plex-Aktivierung geht jede neue Aufgabe und ungeplante Teilaufgabe zuerst an die native Rolle `plex-pm` für eine kurze Bewertung. Root entscheidet nicht selbst über Komplexität oder Umsetzungsreife. PM liefert Ziel/Ausschlüsse, fehlende Entscheidungen, Rollen/Reihenfolge, Aufgabenformat und Referenz, Dev-Vertrag mit Prüfungen sowie `ready`, `needs-specialist` oder `blocked`.

Im BMad-Team aktiviert diese rolleninterne Bewertung weder Persona noch Menü, PRD oder Build. Echte BMad-Aufträge behalten ihre Aktivierungspflichten. Anforderungen folgen dem vorhandenen Tracker-, Issue-, Spec- oder Story-Verfahren des Projekts; installierte PO-/Spec-Operationen verwenden, soweit unterstützt. Kein universelles `bmad-spec` voraussetzen und keine parallele Aufgabenablage einführen.

Nötige technische Entscheidungen gehen vor Dev an architect in BMad oder PM in pnet. Ausführliche Anforderungen oder ein kleiner Diff beweisen keine Designreife. Bewertungen für abgedeckte Schritte und unveränderte Fortsetzung wiederverwenden; neue Entscheidungen gehen zurück an PM. Fehlende/abgelehnte Pflichtrollen blockieren ihren Auftrag: Root darf begrenzten Kontext sammeln und Status berichten, aber nicht deren Entwurf oder Umsetzung übernehmen. Dies verlangt ein Fachresultat, keine neue Benutzerfreigabe.


## Aufgabenaufnahme und Routing

Jede neue Plex-Aufgabe beginnt mit einer kurzen Route: Ergebnis, benötigte Rollen,
Reihenfolge und Abschlussprüfung. Root koordiniert; umfangreiche Planung und
Umsetzung gehören den zuständigen Rollen. Der Skill definiert vier verbindliche
[Arbeitsrouten](../../../skills/plex/references/task-flows.md):

| Aufgabe | Route |
|---|---|
| Begrenzte Änderung mit klarem Ziel und Abnahme | PM-Bewertung → dev → erforderliche Prüfungen → Koordinator |
| Umfangreiche neue Arbeit mit offenen Entscheidungen | PM-Bewertung → benötigte PM/PO/UX/architect-Aufträge → dev → Prüfung → Koordinator |
| Ungeklärter Fehler | PM-Bewertung → begrenzte Diagnose → Korrektur → Prüfung → Koordinator |
| Review angefordert | PM-Bewertung → reviewer → Koordinator |

Nur Rollen des gewählten Teams verwenden: Im pnet-Team übernimmt PM auch die
technische Planung; BMad trennt PM, PO, UX und architect. Akzeptierte Pläne
wiederverwenden, geklärte Fragen überspringen und bei geändertem Umfang oder
Annahmen den zuständigen Spezialisten erneut einbeziehen. Die Routenwahl schafft
keine weitere Benutzerfreigabe; Workflowprüfungen und Analystenfreigabe bleiben
gültig. Kleine mechanische Aufgaben können lokal bleiben.

## Verantwortung

| Rolle | Ergebnis |
|---|---|
| pm | Umfang, Abnahme und Umsetzungsvertrag; BMad PM verantwortet PRD |
| explorer | Schreibgeschützte Karte relevanten Codes und bestehender Prüfungen |
| researcher | Externe Primärquellen und Unsicherheiten |
| analyst | Begrenzte Fachrecherche; BMad nur auf direkten Wunsch/Freigabe |
| po | BMad-Spezifikationen, Tickets, Verfolgung und Neuplanung |
| ux | Umsetzbare Benutzerabläufe, Zustände und Gestaltung |
| architect | Technische Grenzen, Invarianten und Entscheidungen |
| dev | Umsetzung und Prüfungen; ausgewählter BMad-Ausführungsworkflow |
| reviewer | Unabhängige Befunde mit Ort, Auslöser, Wirkung und Belegen |
| qa | Unabhängige Verhaltensprüfung und Tests im zugewiesenen Bereich |

Nur Teamrollen sind verfügbar. Pro geänderter Datei ein Besitzer. Rückgaben unterscheiden
Prüfungen, Annahmen, Harnessfehler und Lücken. Gültige Belege wiederverwenden und
betroffene Prüfungen nach Änderungen wiederholen. Weitere Vollreviews benötigen neues
Risiko, wesentliche Änderung oder ausdrücklichen Wunsch.

## BMad-Start

- Persona-Rollen: Einstiegsskill aktivieren, dann die zugewiesene Operation starten.
- Reviewer: Review-Workflow direkt aktivieren.
- Workflow-Unteraufträge: geliefertes Rezept ausführen; Elternworkflow nicht neu starten.
- Startmeldung und Rückgabe nennen Skillpfad, Aktivierungsbelege,
  Workflow/Operation und erreichten Schritt. Gruß oder Rollenname reichen nicht.
- Der Koordinator bestätigt Aktivierung erst anhand der Ausführungsbelege.
- Begrenzte Änderungen gehen ohne externe Pflichtplanung an Build. Build behält
  Untersuchung, Implementierungsplan, Review und Korrekturen.

## BMad-Verträge

Vorhandene Skills aktivieren, keine Personas kopieren oder Versionsmenüs annehmen.
Gerenderte Route, Pflichtzyklen und echte Benutzerfreigaben bewahren. Ein anwendbarer
früher Ausstieg überspringt spätere Checkpoints desselben Schritts; Bedingung/Ziel vor
Eskalation prüfen. Falsche Gates im selben Auftrag korrigieren, ohne Zustimmung zu
erfinden. Eine fertige Spezifikation allein ist kein Grund für eine Freigabepause.

Verschachtelung braucht Befugnis und Kapazität. Leaf-Prompts und Kontextverträge
bewahren; Leaf-Reviews nicht an Wrapper geben, die neue vollständige Workflows starten.
Tatsächliches Routing und nicht verfügbare Fähigkeiten melden.
