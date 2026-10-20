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

## Format

Mit kurzem Zweck und Auswahlbeschreibung beginnen, danach:

| Abschnitt | Inhalt |
|---|---|
| Working mode | Reihenfolge, Eingaben und fehlende Voraussetzungen |
| Focus on | Auftragsspezifische Schwerpunkte |
| Quality checks | Abschlussbelege |
| Return | Pfade, Ergebnisse, offene Befunde/Entscheidungen |
| Boundaries | Schreibbereich, Delegationsbefugnis und Stopps |

Konkrete, kurze Schritte mit gleicher Semantik für alle Clients verwenden.
Keine generischen zweiten Koordinatoren, willkürlichen Befundquoten oder Pflichtaufrufe
optionaler Rollen. Jede Rolle hat eine Quelle innerhalb ihres Teams; Client-Renderer erzeugen die nativen Formate.

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

## BMad-Verträge

Vorhandene Skills aktivieren, keine Personas kopieren oder Versionsmenüs annehmen.
Gerenderte Route, Pflichtzyklen und echte Benutzerfreigaben bewahren. Ein anwendbarer
früher Ausstieg überspringt spätere Checkpoints desselben Schritts; Bedingung/Ziel vor
Eskalation prüfen. Falsche Gates im selben Auftrag korrigieren, ohne Zustimmung zu
erfinden. Eine fertige Spezifikation allein ist kein Grund für eine Freigabepause.

Verschachtelung braucht Befugnis und Kapazität. Leaf-Prompts und Kontextverträge
bewahren; Leaf-Reviews nicht an Wrapper geben, die neue vollständige Workflows starten.
Tatsächliches Routing und nicht verfügbare Fähigkeiten melden.
