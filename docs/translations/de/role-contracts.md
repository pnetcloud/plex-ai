# Rollenverträge

[English](../../role-contracts.md) · [Русский](../ru/role-contracts.md) · [Deutsch](role-contracts.md) · [简体中文](../zh-CN/role-contracts.md)

Teams definieren Mitglieder/Skills; Profile wählen Modelle; Markdown-Quelldateien des Teams liefern
begrenzte Ausführungsanweisungen. Der Root-Vertrag ist `teams/<team>/coordinator.md`,
keine zusätzliche Subagentenrolle.


Die Quelle liegt unter `teams/<team>/agents/<role>.md`: TOML-Metadaten zwischen
`+++`, gefolgt von Markdown-Anweisungen. Teams bleiben auch bei gleichen Rollennamen
unabhängig. Modelle bleiben in Profilen, Skill-Bindungen in `team.toml`.

Pflichtfelder: `name`, `description`, `access` (`read-only` oder `workspace-write`)
sowie die booleschen Felder `web` und `delegation`. Schreibgeschützte Rollen dürfen
nicht delegieren. Codex erbt Sandbox, Freigaben und MCP-Server von der Hauptsitzung;
generierte TOML-Dateien enthalten weder `sandbox_mode` noch `approval_policy`.
Schreibschutz bleibt eine Verhaltensanweisung, keine separate Codex-Sandbox.
Claude nutzt Werkzeuglisten für schreibgeschützte Rollen, Antigravity explizite
Werkzeuglisten. Client-Berechtigungen
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

Neue Koordinatorzustände verwenden Markdown; bestehendes JSON bleibt lesbar.
Die nur lesende Prüfung gibt beide Formate mit `--markdown` als Markdown aus.
Setup migriert gültige kanonische JSON-Zustände im gewählten Installationsbereich
automatisch, sichert Originale und entfernt alte Dateien nach der Prüfung.
Konflikte bleiben erhalten; `plex status` zeigt das vorgefundene Speicherformat.
Prüfungen alter Pfade liefern den neuen `canonical_path` derselben Sitzung.
Erlaubt sind 32 KiB UTF-8 und 16 aktuelle Entscheidungen; exakte Verweise und
Agentenkennungen beibehalten. Die Grenze beschränkt weder Kontext noch Ausführung.

Nach der Bewertung führt Dev/DevOps gewöhnliche technische Schritte innerhalb
des angenommenen Auftrags selbstständig aus. Für Eskalation, alternative Werkzeuge
und unabhängige Arbeit während ausstehender Abnahme gilt die
[gemeinsame Regel](../../../skills/plex/references/assignments.md#execution-ownership).

Nach Plex-Aktivierung führt der Koordinator einen kompakten [Sitzungsstatus](../../../skills/plex/references/coordinator-state.md). Verwandte Followups aktualisieren das bestehende Ergebnis; unabhängige Anfragen dürfen vor einer Delegation vorgemerkt werden. Vor Routing oder Ausführung neuer oder vorgemerkter Arbeit ist eine kurze Bewertung durch `plex-pm` erforderlich. Root entscheidet nicht selbst über Komplexität oder Umsetzungsreife. PM liefert Aufgabenklasse, Ziel/Ausschlüsse, fehlende Entscheidungen, Rollen/Reihenfolge, Aufgabenformat und Referenz, Dev-Vertrag mit Prüfungen sowie `ready`, `needs-specialist` oder `blocked`.

Im BMad-Team aktiviert diese rolleninterne Bewertung weder Persona noch Menü, PRD oder Build. Echte BMad-Aufträge folgen ihrem jeweiligen Einstieg. Anforderungen nutzen das vorhandene Tracker-, Issue-, Spec- oder Story-Verfahren des Projekts; verwenden Sie unterstützte PO-Operationen oder katalogisierte eigenständige Spec-Workflows. Ein direkter Workflow folgt seinem eigenen Vertrag ohne Voraussetzung einer unbeteiligten Persona. Kein universelles `bmad-spec` voraussetzen und keine parallele Aufgabenablage einführen.

Nötige technische Entscheidungen gehen vor Dev an architect in BMad oder PM in pnet. Ausführliche Anforderungen oder ein kleiner Diff beweisen keine Designreife. Bewertungen für abgedeckte Schritte und unveränderte Fortsetzung wiederverwenden; wesentliche Entscheidungen außerhalb des Auftrags gehen zurück an PM. Fehlende/abgelehnte Pflichtrollen blockieren ihren Auftrag: Root darf begrenzten Kontext sammeln und Status berichten, aber nicht deren Entwurf oder Umsetzung übernehmen. Dies verlangt ein Fachresultat, keine neue Benutzerfreigabe.


## Aufgabenaufnahme und Routing

Jede zur Weiterleitung ausgewählte Plex-Aufgabe beginnt mit einer kurzen Route: Ergebnis, benötigte Rollen,
Reihenfolge und Abschlussprüfung. Root koordiniert; umfangreiche Planung und
Umsetzung gehören den zuständigen Rollen. Der Skill definiert folgende
[Arbeitsrouten](../../../skills/plex/references/task-flows.md):

| Aufgabe | Route |
|---|---|
| Begrenzte Änderung mit klarem Ziel und Abnahme | PM-Bewertung → dev → erforderliche Prüfungen → Koordinator |
| Umfangreiche neue Arbeit mit offenen Entscheidungen | PM-Bewertung → benötigte PM/PO/UX/architect-Aufträge → dev → Prüfung → Koordinator |
| Ungeklärter Fehler | PM-Bewertung → begrenzte Diagnose → Korrektur → Prüfung → Koordinator |
| Review angefordert | PM-Bewertung → reviewer → Koordinator |
| CI/CD, Release oder zugewiesenes Deployment | PM-Intake → devops → erforderliche Prüfungen/Review → Koordinator |

Die gemeinsamen [Regeln zur Aufgabenroute](../../../skills/plex/references/task-flows.md) bestimmen, wann Architect oder UX nötig ist; beide Rollen sind bedarfsabhängig und keine Standardschritte.

Bei einem ungeklärten Fehler endet die Diagnose, sobald Fehlerpfad und Ursache eine
sichere Korrektur ermöglichen. Unbekannte Produktionsidentität oder mögliche Effekte
blockieren ACK, Replay oder Änderungen, nicht aber einen isolierten Fix, der
unbekannte Fälle sicher anhält.

Nur Rollen des gewählten Teams verwenden: Im pnet-Team übernimmt PM auch die
technische Planung; BMad trennt PM, PO, UX und architect. Akzeptierte Pläne
wiederverwenden, geklärte Fragen überspringen und bei geändertem Umfang oder
Annahmen den zuständigen Spezialisten erneut einbeziehen. Die Routenwahl schafft
keine weitere Benutzerfreigabe; Workflowprüfungen und Analystenfreigabe bleiben
gültig. Kleine mechanische Aufgaben können lokal bleiben.

Für die BMad-Auswahl liest PM einmal die vollständige `workflows`-Karte aus dem
exakten, von Root übergebenen Snapshot und gibt die minimal ausreichende Route
zurück: Zweck, passende Rolle, Einstieg, Reihenfolge sowie erwartete kanonische
Ein- und Ausgaben. Bei interaktiven Optionen delegiert Root die vom Nutzer gewählte
Route; andernfalls die von PM festgelegte Route. Root integriert das Ergebnis und
setzt keine eigene Route an ihre Stelle.

## Verantwortung

| Rolle | Ergebnis |
|---|---|
| pm | Erstbewertung, Routenwahl und Abnahme; BMad PM verantwortet Anforderungen, PRDs und zugewiesene eigenständige Specs |
| explorer | Schreibgeschützte Karte relevanten Codes und bestehender Prüfungen |
| researcher | Externe Primärquellen und Unsicherheiten |
| analyst | Begrenzte Fachrecherche; BMad nur auf direkten Wunsch/Freigabe |
| po | BMad-Spec- und Aufgabenworkflows, Ticket-Aufteilung, Verfolgung und Neuplanung |
| ux | Umsetzbare Benutzerabläufe, Zustände und Gestaltung |
| architect | Technische Grenzen, Invarianten und Entscheidungen |
| dev | Umsetzung und Prüfungen; ausgewählter BMad-Ausführungsworkflow |
| reviewer | Unabhängige Befunde mit Ort, Auslöser, Wirkung und Belegen |
| qa | Unabhängige Verhaltensprüfung und Tests im zugewiesenen Bereich |
| devops | CI/CD, Release-Veröffentlichung und ausdrücklich zugewiesenes Deployment/Recovery mit revisionsbezogenen Belegen |

DevOps ist in beiden Teams ein nativer Plex-Spezialist und nutzt Projektverfahren für Releases/Deployments ohne verpflichtende BMad-Persona. PM-Intake bleibt erforderlich. Release-Autorisierung erlaubt kein Deployment; Vorbereitung, Veröffentlichung, Installation und Betriebszustand benötigen getrennte Belege. Unabhängiges Review bleibt bei reviewer.

Nur Teamrollen sind verfügbar. Pro geänderter Datei ein Besitzer. Rückgaben unterscheiden
Prüfungen, Annahmen, Harnessfehler und Lücken. Gültige Belege wiederverwenden und
betroffene Prüfungen nach Änderungen wiederholen. Weitere Vollreviews benötigen neues
Risiko, wesentliche Änderung oder ausdrücklichen Wunsch.

## BMad-Start

- Persona-/Menüaufträge: deklarierten Einstieg aktivieren, dann die Operation starten.
- Direkte eigenständige Workflows: ihrem eigenen Aktivierungs- und Rückgabevertrag folgen, ohne eine unbeteiligte Persona oder ein Menü voranzustellen.
- Reviewer aktiviert den Review-Workflow direkt; Workflow-Unteraufträge führen ihr Rezept aus und starten den Elternworkflow nicht neu.
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

Für Implementierungen konkrete akzeptierte Anforderungen wiederverwenden. Fehlen
sie, erzeugt der ausgewählte Spec- oder Build-Weg vor dem Code konkrete Anforderungen;
keine PRD, Epic, Story oder doppelte Spezifikation automatisch anlegen. In
`interactive` sendet PM wesentlich unterschiedliche Routen samt Empfehlung über Root
an den Nutzer; in `auto` wählt PM ohne optionale Routenfrage. `balanced` behält seine
bisherige Regel. Eine festgelegte Route nicht erneut abfragen; echte Workflow-Prüfpunkte
bleiben bestehen.

Verschachtelung braucht Befugnis und Kapazität. Leaf-Prompts und Kontextverträge
bewahren; Leaf-Reviews nicht an Wrapper geben, die neue vollständige Workflows starten.
Tatsächliches Routing und nicht verfügbare Fähigkeiten melden.

## Aufträge, Planung und Ziele

Bei pnet verantwortet PM Aufgabenstellung, technische Planung und Ausführungswahl.
Bei BMad übernimmt PM den Intake, PO Spezifikationen/Aufgaben und architect technische
Entscheidungen. Root koordiniert und integriert Nachweise; keine zusätzliche Manager-Rolle.

Ausführbare Aufträge nutzen den [kompakten Vertrag](../../../skills/plex/references/assignments.md)
und dessen schreibfreien Validator: Eingaben, Schreibgrenzen/Ausschlüsse, akzeptierte
Abhängigkeiten, Bereitschaft und normalerweise drei beobachtbare Kriterien (eins bis fünf)
mit jeweils einer Prüfung. Bestehende Issues/Specs/Stories bleiben maßgeblich. Erster
PM-Intake und Workflow-Unteraufträge benötigen keinen zusätzlichen JSON-Vertrag.
Strukturprüfung beweist weder fachliche Bereitschaft noch Sandbox oder echten Dispatch.
Die Kriteriengrenze gilt für die Auftragszusammenfassung; alle Spec-/Workflow-Prüfungen bleiben erhalten.

PM/PO wählt begründet `normal`, `plan` oder `goal`, in `auto` ohne zusätzliche Modusfrage.
Plan klärt Entscheidungen vor Anwendungscode-Änderungen; goal arbeitet innerhalb des
akzeptierten Umfangs bis zu nachgewiesenen Kriterien. Native Client-Modi sind optional:
sonst normal planen oder begrenzt zielorientiert arbeiten und den tatsächlichen Ansatz
melden. Weder Chat-Modus heimlich wechseln noch bestehende Ziele ersetzen oder eine
vom Host nicht unterstützte Fortsetzung versprechen. Host-Rechte und Benutzerwahl gelten.

Für passende unbeaufsichtigte BMad-Implementierung in `auto` installiertes
`bmad-build-auto` wählen: eine gerenderte Workflow-Iteration mit erforderlichen
Subagenten und Endstatus. Sonst eine autorisierte unterstützte Build-Route verwenden.
Spezifikation, Renderer, Prüfungen und echte Gates erhalten; kein zweiter Plan-/Review-Zyklus.

Agenten wiederverwenden. Neue Entscheidungen, geänderte Nachweise und die verbleibende
Frage statt ganzer Transkripte weitergeben. Unabhängige Bewertungen parallel ausführen;
abhängige Arbeit wartet auf akzeptierte Eingaben. Widersprüche dem Entscheidungsverantwortlichen
melden, keinen Konsens erfinden. Ergebnisse belegen jedes Kriterium und benennen Lücken.

`max_agents` begrenzt gleichzeitig unerledigte Plex-Aufträge, nicht alle bisherigen Starts.
Abgeschlossene/idle Aufträge zählen dafür nicht mehr; ihre Handles können weiterhin
native Thread-Slots belegen. Beide Grenzen vor einer Kapazitätssperre getrennt prüfen.

## Geprüfte Rückgaben und Hilfsanfragen

Neue Plex-Aufträge erhalten ein Aufgabenlabel und eine positive `revision`. Der
[gemeinsame Antwortvertrag](../../../skills/plex/references/assignments.md#response-contract)
prüft Rolle, Auftragsidentität, Status und Nachweise vor der Abnahme. Der bisherige
CLI-Aufruf für Eingaben bleibt kompatibel. Antworten werden mit
`check_assignment.py --resolved <snapshot> --assignment <current-assignment.json>`
und einem JSON-Objekt auf stdin geprüft. Beide Prüfungen sind schreibgeschützt.

- `progress`: neues Ergebnis/Beobachtung und nächster Schritt; keine Bestätigung abwarten.
- `needs-decision`: konkrete Frage, bereits ausgeführte Prüfungen und Empfehlung;
  der Koordinator leitet sie an PM/PO, Architekt oder Daten-/Berechtigungsverantwortliche weiter.
- `blocked`: tatsächliche Einschränkung, Nachweise und Bedingung für die Fortsetzung.
- `completed`: alle Auftragskriterien mit Nachweisen erfüllt; die empfangende Rolle
  prüft weiterhin die Abnahme. Reviewer können durch die Lieferung von Befunden abschließen.

`completed` schließt nur diesen Auftrag ab. PM/PO formuliert das übergeordnete
Benutzerziel und hält im bestehenden Handoff die zuständige Rolle und die Prüfung
seines Endzustands fest; der Koordinator schließt das übergeordnete Ziel erst, wenn
integrierte Nachweise diese Prüfung bestehen. Ein abgeschlossener
Voraussetzungsauftrag ist noch keine Lieferung: Ein erfolgreicher Build kann eine
Voraussetzung erfüllen, ein angefragtes laufendes Deployment erfordert jedoch die
Prüfung des benannten Ziels. Bei mehrstufiger Arbeit wird jedes übergebene Ergebnis
im [Koordinatorstatus](../../../skills/plex/references/coordinator-state.md)
festgehalten und `next_action` des übergeordneten Ziels aktualisiert; ein blockierter
Folgeschritt öffnet ein bereits übergebenes Ergebnis nicht erneut.

Ist eine Nachweismethode nicht verfügbar oder scheitert sie aus methodenspezifischem
Grund, nutzen Sie eine unterstützte Alternative innerhalb derselben autorisierten
Handlung und desselben Umfangs. Erhalten Sie dabei Abnahmekriterien und erforderliche
Prüfungen; bitten Sie nicht allein wegen des Methodenwechsels um Erlaubnis.
Eine Host-Ablehnung, geänderte Handlung/Umfang/Wirkung, eine Host-Grenze oder unklare
Befugnis geht an die tatsächliche Berechtigungsstelle.

Derselbe Ausführende setzt mit neuen Nachweisen, korrigierter Eingabe oder einer
Entscheidung fort. Unveränderte Probleme erhalten weder ein neues Label noch einen
Workflow-Neustart. Einen Fehler der Antwortstruktur einmal mit genauer Diagnose an
den Autor zurückgeben. Zuvor geprüfte Nachweise samt ursprünglichem Artefakt,
Revision und Herkunft erhalten; Arbeit oder Prüfungen nur wiederholen, wenn sich
die Nachweise ändern oder ungültig werden. Keine Nachweise im Namen des Autors
ergänzen. Bleibt die Korrektur ungültig, Teilergebnisse behalten und melden statt
endlos umzuformatieren. Fortschritt wird ereignisbasiert gemeldet: ohne Timer, neues
Tokenlimit oder automatischen Modellwechsel.

PM-Erstaufnahme und interne Workflow-Schritte behalten ihre Formate. Die äußere
BMad-Rückgabe enthält weiterhin Aktivierungs- und Workflow-Nachweise. Alte Verträge
bleiben lesbar; Identität für neue Antwortprüfungen ergänzen, ohne laufende Arbeit
neu zu starten. Plex auffrischen und eine neue Clientsitzung öffnen, um die Anweisungen
zu laden. Strukturprüfung beweist keine Nachweisqualität, verhindert nicht jede
Schleife und erzwingt keinen nativen Dispatch; Live-Verhalten separat prüfen.
