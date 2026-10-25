# Konfiguration

[English](../../configuration.md) · [Русский](../ru/configuration.md) · [Deutsch](configuration.md) · [简体中文](../zh-CN/configuration.md)

[Installation, Entwicklungsmodus und alle CLI-Optionen](installation.md).

## Teams und Profile

| Team | Rollen | Ablauf |
|---|---|---|
| `pnet` | pm, explorer, researcher, dev, reviewer, qa, devops | Eigenständige Koordination |
| `bmad` | analyst, pm, po, ux, architect, dev, reviewer, devops | Vorhandene BMad-Skills |

Profile: `inherit`, `basic`, `plus`, `pro`, `pro-plus`, `ultra`, `ultra-plus`. Gemeinsame Stufen kombinieren
die OpenAI-Einstellungen für Codex, Anthropic für Claude Code und Google für Antigravity
des gewählten Teams. `inherit` überlässt Modell/Effort dem Client.
Profile beschreiben Einstellungen, keine gemessenen Qualitätsstufen.

Editierbare Datei im gewählten Installationsstamm: `.plex/preset.toml`.
Interaktives **Reconfigure** zeigt geänderte verwaltete Rollenpfade, sichert deren geprüften Inhalt und erzeugt die Rollen aus dem gewählten Profil und den Preset-Überschreibungen neu. **Update only** stoppt weiterhin bei manuellen Änderungen. Fehlende oder fremde Dateien, Symlinks, geänderte Anweisungsblöcke, Client-Konflikte und Änderungen nach der Vorschau bleiben geschützt. Dauerhafte Modellwahl gehört in `.plex/preset.toml`.

Beide Teams bieten sechs benannte Stufen sowie `inherit`. In den Anbieterdateien steht die Koordinator-Empfehlung zuerst in jeder Stufe. Haiku/Sonnet/Opus entsprechen ungefähr Luna/Sol/Astra; gleiche Qualität ist nicht nachgewiesen. Native Google-Profile verwenden Flash oder das Modell des Hauptchats; Ultra erhöht den angeforderten Effort. Claude in Antigravity verwendet Sonnet statt des nicht verfügbaren Haiku; genaue Modell-IDs benötigen Client-Unterstützung.
```toml
team = "pnet"
model_profile = "plus"
max_agents = 3

[codex.dev]
reasoning = "max"
```

Plex konfiguriert keine Tokenbudgets. Beim Refresh werden veraltete Budgetfelder aus bestehenden Presets entfernt. Maßgeblich sind die Abnahmekriterien und tatsächlichen Einschränkungen des Clients.

Optionale Tabellen `[coordinator.<tier>]` in den Herstellerprofilen enthalten
Empfehlungen für den Hauptchat (`model`, `reasoning`). Sie bleiben von den
Rolleneinstellungen getrennt und erscheinen als `coordinator` im aufgelösten
Snapshot. Setup zeigt die Empfehlung des gewählten Profils, ändert aber weder
den Client noch installiert es eine Koordinatorrolle. Ohne Empfehlung, auch
bei `inherit`, wählt der Benutzer das Modell.

Priorität je Feld: **Profilstandard → Profilrolle → Client-Override → Rollen-Override**.
Clienttabellen heißen `[codex]`, `[claude]`, `[antigravity]`; Rollentabellen ergänzen den
Rollennamen. Beide akzeptieren `model` und `reasoning`. Für Codex-Vererbung `model`
weglassen. Teamwechsel bewahren inaktive Overrides für derzeit nicht enthaltene Rollen.

Definitionen liegen in `teams/<team>/team.toml`, `agents/*.md` und `profiles/*.toml`.
Anbieterdateien deklarieren einen Client und unabhängige Stufen, ohne Include-Ketten.
Genaue Modell-IDs und Effort-Werte gehören dorthin, nicht in duplizierte Dokumentationstabellen.

`[skills]` bindet jede Rolle an ihren Einstiegsskill. Optionale Einträge
`[[workflows.<role>]]` enthalten `skill` und eine kurze `description` sowie optional
`operation` als Menücode innerhalb einer Persona. Beispiel: Analyst verwendet
`skill = "bmad-deep-recon"`; PO verwendet `skill = "bmad-agent-po"` mit
`operation = "SPEC"`. Jeder Eintrag benötigt eine Ergebnisbeschreibung.

Der Resolver validiert den Katalog und speichert ihn in `.plex/resolved.json`.
Der Koordinator wählt anhand der Beschreibung und übergibt Absicht und Parameter;
der Subagent prüft den installierten Dispatch und lädt nur den gewählten Workflow.
Der Katalog aktiviert nicht alle Skills, installiert kein BMad und ersetzt keine
Freigabe. Die Abläufe bleiben im installierten BMad. Nach Katalogänderungen Setup
aktualisieren; vorhandene Snapshots ändern sich nicht automatisch.

Anbieterspezifische IDs wie `openai-plus` oder `google-anthropic-plus` sind über
Einzelclient-Setup mit `--host` und den Resolver verfügbar. Multi-Client-Setup mit
`--client` nutzt gemeinsame Stufen. Das Einzelclient-Custom-Menü bearbeitet Rollen-
Overrides eines benannten Profils; `custom` ist kein gespeichertes Profil.
Modellverfügbarkeit hängt vom Client und Provider ab.

## Interaktion

Interaktives Setup fragt den Modus einmal für alle ausgewählten Clients ab; vorausgewählt ist der gespeicherte Modus, sonst `balanced`. Jeder angewendete Preset speichert `interaction` ausdrücklich, auch nach Aktualisierung älterer Konfigurationen.

`interaction = "balanced"` steht auf oberster Ebene in `.plex/preset.toml`.
Alternativ `--interaction interactive|balanced|auto` an Setup oder Resolver-`apply`
übergeben. Ohne Option bleibt der gespeicherte Wert; Standard ist `balanced`.
Der Plan zeigt den Modus. Er gilt für alle Clients und bleibt bei Team-/Profilwechsel
bestehen. Nach manuellen Änderungen Setup aktualisieren.

- `interactive`: gemeinsame Ausarbeitung und wesentliche Entscheidungen mit dem Nutzer.
- `balanced`: Routineentscheidungen selbst lösen; nur bei wesentlichen offenen
  Entscheidungen oder geltenden Checkpoints fragen.
- `auto`: keine Fragen und kein Warten; erlaubte Arbeit abschließen, Teilergebnisse
  und Blocker zurückgeben.

Eine ausdrückliche Wahl für einen Auftrag überschreibt den Modus ohne Speicherung.
Der Koordinator übergibt ihn an alle Ausführenden. Subagenten melden Fragen an ihn;
er nutzt bekannte Antworten, bündelt nötige Fragen in balanced und setzt unabhängige
Arbeit fort. In auto blockiert ein offener Punkt nur abhängige Arbeit.

Bei begrenzten Artefaktaufträgen nutzen balanced/auto natives BMad-Headless, soweit
unterstützt. Sonst gelten echte Checkpoints; auto meldet einen Blocker, wenn ohne
Antwort kein autorisierter Weg besteht. Tests/Reviews, Berechtigungen, Veröffentlichungs-
und Analystenfreigaben bleiben erhalten. Unvollständige Anforderungen sind keine
freigegebenen Implementierungseingaben. Eine unbeaufsichtigte Ausführung jedes
Workflows ist damit nicht garantiert.

## Projekt- und Benutzerebene

| Client | Projektrollen | Benutzerstamm / Rollenverzeichnis |
|---|---|---|
| Codex | `.codex/agents/` | `$CODEX_HOME` oder `~/.codex` / `agents/` |
| Claude Code | `.claude/agents/` | `$CLAUDE_CONFIG_DIR` oder `~/.claude` / `agents/` |
| Antigravity | `.agents/agents/` | `~/.gemini` / `config/agents/` |

Jeder Stamm führt seinen eigenen `.plex`-Zustand. `check --host <host> --scope auto`
wählt zunächst das Projekt, sonst den Benutzer. Veraltete oder widersprüchliche
Projektzustände fallen nicht still zurück. Bereichswechsel löschen/migrieren den
anderen Bereich nicht. BMad-Benutzerrollen benötigen weiterhin Voraussetzungen in jedem Arbeitsprojekt.

## Verwaltete Anweisungen und Zustand

Unveränderte, per Beleg verwaltete Blöcke mit `plex:start` / `plex:end` werden beim Aktualisieren automatisch migriert. Gemischte Markerformate oder bearbeitete Blöcke stoppen das Update.

Plex besitzt nur `<!-- plex:managed:start -->` … `<!-- plex:managed:end -->`. Persönliche Anweisungen
außerhalb lassen. Bearbeitete, fehlende, doppelte oder ungültige Marker verursachen
einen Konflikt statt eines Überschreibens.

Setup wählt eine vorhandene nichtleere Datei oder erstellt die Standarddatei: Codex
`AGENTS.override.md`, dann `AGENTS.md`, dann Projekt-Fallbacks; Claude `CLAUDE.md`, dann
projektbezogen `.claude/CLAUDE.md`; Antigravity `GEMINI.md`, dann Projekt-`AGENTS.md`.
Benutzer-Codex nutzt keine Fallbacks. Die Auswahl ändert keine Client-Fallbackkonfiguration
und erzwingt nicht das Lesen einer zusätzlichen Anweisungsdatei.

| Datei | Zuständigkeit |
|---|---|
| `.plex/preset.toml` | Editierbares Team/Profil/Overrides |
| `.plex/resolved.json` | Generierter effektiver Snapshot |
| `.plex/applied.json` | Client-Receipt und verwaltete Hashes |
| `.plex/skill-aliases.json` | Codex-Verknüpfungen für kurze Namen; erzeugter Eigentumsnachweis |
| `.plex/dev.json` | Codex-Dev-Links und Projekt-Plugin-Override; Eigentumsnachweis |
| `.plex/backups/` | Ersetzte Dateien und ausgeschiedene Rollen |

Generierte Rollen/Receipts nicht manuell bearbeiten. Fremde oder geänderte verwaltete
Dateien, Symlinks und parallele Applies blockieren unsichere Updates.
Gemeldeten Konflikt vor dem Refresh lösen und Backups behalten. Interaktives Reconfigure darf verwaltete Rollen wie oben beschrieben ersetzen.

## Ohne Anwendung prüfen

Im Plex-Checkout, Python 3.11+:

```sh
python3 skills/plex-setup/scripts/resolve_config.py list
python3 skills/plex-setup/scripts/resolve_config.py resolve /path/to/project/.plex/preset.toml
python3 skills/plex-setup/scripts/resolve_config.py render /path/to/project/.plex/preset.toml --host codex
python3 skills/plex-setup/scripts/resolve_config.py check /path/to/project --host codex --scope auto
```

`apply` schreibt native Konfiguration. Bei direkter Resolver-Nutzung erfordern
Anweisungen ausdrücklich `--instructions`. Der Installer kombiniert Vorschau,
Plugininstallation und Anweisungsintegration.

Optionale BMad-Review-Anpassung: [Review-Richtlinie](../../../teams/bmad/review-policy.md).
Normales Setup aktiviert sie nicht.

## Andere Codex-Agenten

Plex-Aufträge verwenden ausschließlich exakte `plex-<role>`-Namen des geprüften aktiven Teams. Andere installierte oder eingebaute Agenten gehören nicht dazu; Workflow-eigene Ausführende folgen dem jeweiligen Workflow-Vertrag.

Setup zeigt andere `.toml`-Agenten im gewählten Geltungsbereich und bietet **Behalten** (Standard) oder **Ins Backup verschieben** an. Sie bleiben im Client verfügbar und können die Rollenwahl beeinflussen. Geeignete Dateien werden nach `.plex/backups/<timestamp>/codex/other-agents/` verschoben; bei Bedarf manuell daraus wiederherstellen. Andere Geltungsbereiche, Symlinks und explizit in `config.toml` registrierte Dateien bleiben erhalten. Außerhalb des interaktiven Reconfigure bleiben geänderte verwaltete Rollen Konflikte.

## Arbeitsverzeichnis und native Delegation

Nicht eingecheckte Änderungen allein erfordern keine Bestätigung. Plex erfasst den Ausgangszustand, weist Aufgabendateien zu und bewahrt bestehende Änderungen, auch fremde Abschnitte innerhalb einer zugewiesenen Datei. Diese Erlaubnis wird an Workflows weitergegeben; eine reine Dirty-Tree-Rückfrage ist damit beantwortet. Konflikte blockieren nur betroffene Arbeiten. Plex erstellt keine Worktrees und führt keinen Branchwechsel, Stash, Reset, Clean oder Commit aus, um einen sauberen Zustand herzustellen.

Für Codex ergänzt Setup fehlende Werte `hide_spawn_agent_metadata = false` und `tool_namespace = "agents"` unter `[features.multi_agent_v2]`. Wenn weder die Zielkonfiguration noch bekannte geerbte Konfiguration eine Kapazität festlegt, speichert es zusätzlich `agents.max_concurrent_threads_per_session = max_agents` in derselben Transaktion. Der Tabellenkopf `[agents]` bleibt außerhalb des entfernbaren Blocks, damit persönliche Schlüssel ihren Geltungsbereich behalten.

Vorhandene kanonische `agents.max_concurrent_threads_per_session`- und ältere
`agents.max_threads`-Werte bleiben persönlich; gleiche Aliaswerte werden erhalten.
Wird neben einem Plex-eigenen kanonischen Schlüssel ein gleicher lokaler Alias
ergänzt, gibt Plex nur seinen Schlüssel und Beleg frei; der Alias bleibt
erhalten. Unterschiedliche Aliaswerte und boolesche, nicht ganzzahlige oder
nichtpositive Werte führen vor dem Schreiben zu einem Konflikt. Werte außerhalb
des positiven Bereichs einer vorzeichenbehafteten 64-Bit-Ganzzahl führen
ebenfalls vor dem Schreiben zu einem Konflikt; dies ist eine Grenze der
Konfigurationsdarstellung, keine Empfehlung für die Thread-Anzahl. Explizite
globale Benutzerwerte bleiben bestehen, auch wenn sie unter `max_agents` liegen.
Für einen übergeordneten Kandidaten `.codex/config.toml` ohne Beleg, dass die
Konfigurationsebene gilt, oder ein Profil mit möglicher Kapazität meldet Setup
die Anwendbarkeit als unbekannt und ändert die Kapazität nicht automatisch. Bei
dieser Unsicherheit bleiben ein unveränderter Plex-Block und sein Beleg bestehen,
auch wenn sich `max_agents` ändert. Bei bekannter Anwendbarkeit folgt ein
unveränderter Plex-Block dem aktualisierten `max_agents`; Plex gibt ihn bei einem
bekannt geltenden expliziten geerbten Limit oder einem gleichen lokalen Alias
frei. Geänderte, fehlende oder nicht verwaltete Marker sind Konflikte.

`max_agents` zählt unerledigte Plex-Aufträge. Der native Grenzwert zählt zugleich
offene Kindthreads einschließlich verschachtelter und inaktiver Threads; der
Hauptthread ist ausgeschlossen. Vorschau, Anwendung und Status zeigen Quelle,
Wert und Abweichungen getrennt und melden die Sitzungsaktivierung als unbekannt.
Eine Konfigurationsprüfung belegt nur gespeicherte Werte. Der Installer startet
Codex nie neu; nach Änderungen eine neue Sitzung öffnen und die tatsächliche
Aktivierung dort prüfen.

Codex muss der Projektkonfiguration vertrauen. Nach Setup eine neue Sitzung öffnen. Preflight unterscheidet fehlendes Spawn-Werkzeug, verborgene Rollenauswahl, abgelehnte Rolle und akzeptierten Aufruf. Ist die Auswahl verfügbar, die genaue Teamrolle anfordern, auch ohne sichtbare Rollenliste; soweit unterstützt mit frischem Kontext und eigenständiger Übergabe. Konfigurationsprüfungen beweisen weder geladene Sitzungsrollen noch das tatsächliche Modell des Kindes.
