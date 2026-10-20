# Konfiguration

[English](../../configuration.md) · [Русский](../ru/configuration.md) · [Deutsch](configuration.md) · [简体中文](../zh-CN/configuration.md)

## Installation und Aktualisierung

Für die Erstinstallation den [Schnellstart](../../../README.de.md#schnellstart) verwenden.
Der Bootstrap hält einen Checkout in `~/.local/share/plex-ai` und installiert die neueste
**veröffentlichte Version einschließlich Vorschauen**. Den Checkout behalten: Plugins verweisen darauf.
Der Einstieg kommt aus `main`, die Anwendungsdateien aus dem ausgewählten Versionstag.

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

### Status, Update und Entfernung

```sh
plex status
plex status --json
plex update
plex update --release v0.2.0
plex update --development
plex uninstall --dry-run
plex uninstall
```

`status` prüft zuerst die Projektkonfiguration, sonst die Benutzerinstallation des
Clients. Es zeigt Quellversion, Team/Profil, native Rollen, Konflikte und Pluginerkennung,
ohne Plex-Konfiguration zu ändern. `--json` liefert strukturierte Ausgabe. Konfigurierte
Clients mit Konflikten, veraltetem Zustand oder fehlendem Plugin ergeben einen Fehlerstatus.
Tatsächliches Modellrouting wird damit nicht nachgewiesen.

`update` wählt die neueste veröffentlichte Version und öffnet Setup für die gewählten
Clients. `--release` fixiert einen veröffentlichten Tag, `--development` wählt ausdrücklich
`main`. Lokale Änderungen, Symlinks oder fremder Origin verhindern Updates. Quellen
werden auf einen konkreten Tag ausgecheckt. `update --dry-run` zeigt die Auswahl ohne
Checkout- oder Konfigurationsschreibzugriffe.

`uninstall` gilt standardmäßig für das Projekt und alle im Receipt erfassten Clients.
`--dry-run` zeigt den Plan; interaktive Entfernung fragt nach Bestätigung, unbeaufsichtigt
ist `--yes` nötig. Mit `--client codex` filtern oder `--scope user` ausdrücklich wählen.
Nur unveränderte Receipt-Rollen und der passende verwaltete Block werden entfernt.
Geänderte/fehlende Dateien oder fehlerhafte Marker stoppen die Aktion. Fremde Dateien
und umgebende Anweisungen bleiben erhalten. Ein geteilter Block bleibt für andere
Clients bestehen. Jeder Client hat eigene Sperre, Transaktion und Backups; mehrere
Clients bilden keine gemeinsame Transaktion.

Gemeinsame Plugins, Checkout, CLI-Verknüpfung, editierbares Preset und Backups bleiben
für andere Projekte oder Neuinstallation. Native Anweisungsdateien bleiben nach Blockentfernung.
Erhaltene Projekteinstellungen haben weiterhin Vorrang vor Benutzerdefaults; der Bereich
wechselt nicht automatisch. Anschließend eine neue Clientsitzung öffnen.
Falls `plex` nicht im PATH liegt, `~/.local/bin/plex` verwenden. Reines `plex` öffnet Setup.

Im Checkout `./setup.sh` starten. Leertaste markiert Clients, Enter fährt fort.
Team, Geltungsbereich und gemeinsames Profil auswählen und jeden Installationsplan
prüfen. Projektebene ist Standard. Der jeweilige Client-CLI muss verfügbar sein.

```sh
./setup.sh --project /path/to/project --client codex --client antigravity --team pnet --model-profile plus --yes
```

Die vollständige Einrichtung installiert das gemeinsame Plex-Plugin und konfiguriert
native Rollen/Anweisungen. Skills werden nicht in Projekte dupliziert. Quellen oder
Export erhalten, solange ein lokaler Marketplace darauf verweist. BMad benötigt
bereits installierte passende Skills und eine Projekt-Runtime.

Setup erneut ausführen, um Definitionen zu aktualisieren oder Team/Profil zu wechseln.
Overrides bleiben erhalten. Neue Definitionen erreichen Rollen erst nach Refresh;
für neue Skills/Rollen eine frische Clientsitzung starten. Gemeinsame Projektprofile
aktualisieren bereits konfigurierte Clients; Clients ohne Receipt werden nicht implizit installiert.

| Option | Wirkung |
|---|---|
| `--dry-run` | Vorschau ohne Schreibzugriffe |
| `--roles-only` | Rollen/Zustand ohne Plugininstallation |
| `--no-instructions` | Verwalteten Anweisungsblock überspringen |
| `--no-command` | Verknüpfung `~/.local/bin/plex` überspringen |
| `--install-command` | Nur die Checkout-Verknüpfung installieren |
| `--max-agents N` | Gemeinsames Auftragslimit setzen |

Pluginmanager-Änderungen und abgeschlossene Clientinstallationen werden bei einem späteren Fehler nicht zurückgerollt.

Ein vorhandener Befehl aus einem anderen Checkout, eine fremde Datei oder ein
defekter Link bleibt mit Hinweis erhalten und blockiert Setup nicht. Der Installer
zeigt seinen eigenen Einstiegspunkt. Explizites `--install-command` überschreibt
weiterhin keinen fremden Befehl.

Fehlt beim projektbezogenen Team `bmad` die Runtime, bietet Setup offizielle
Initialisierung, Wechsel zu `pnet` oder Abbruch. Ohne BMad-Setup-Skill wird eine
separate Benutzerinstallation angeboten. Sie benötigt ausdrückliche Zustimmung:
ausgewählte Benutzer-Skills können ersetzt werden und gelten für andere Projekte.
Vorhandene Plugins bleiben unverändert.

`--install-bmad` erlaubt Installation und Projektinitialisierung; `--init-bmad`
verwendet vorhandene Skills. `--yes` akzeptiert angezeigte Modulstandards.
`--dry-run` schreibt nichts. Nach Planbestätigung läuft das offizielle BMad-Setup
mit nur unbeantworteten Modulfragen. Runtime und Abhängigkeiten bleiben bei
späteren Fehlern erhalten.

Neue Installationen nutzen `skills@1.7.4` und die offizielle BMad-Revision
`495ef6e0996d07b23359cc4d6c73a1aa2f3ba5ad`: nur Einstieg-/Workflow-Skills des Teams,
den Hub `bmad` und zwei Moduldatensätze. PO ist enthalten, im aktuellen Plugin-
Marketplace jedoch noch nicht. Node.js/npm und `uv` sind erforderlich. Der offizielle
Skills CLI unterstützt Codex, Claude Code und Antigravity.

Direkte Projekt-/Benutzerskills haben Vorrang. Aktivierte installierte Codex/Claude-
Toolbox-Plugins werden ebenfalls erkannt; Cache-Ordner allein reichen nicht.
`--bmad-skill /path/to/installed/bmad` wählt einen Hub ausdrücklich. Benutzerrollen
benötigen weiterhin Runtime in jedem Arbeitsprojekt.


## Teams und Profile

| Team | Rollen | Ablauf |
|---|---|---|
| `pnet` | pm, explorer, researcher, dev, reviewer, qa | Eigenständige Koordination |
| `bmad` | analyst, pm, po, ux, architect, dev, reviewer | Vorhandene BMad-Skills |

Profile: `inherit`, `basic`, `plus`, `pro`, `pro-plus`. Gemeinsame Stufen kombinieren
die OpenAI-Einstellungen für Codex, Anthropic für Claude Code und Google für Antigravity
des gewählten Teams. `inherit` überlässt Modell/Effort dem Client.
Profile beschreiben Einstellungen, keine gemessenen Qualitätsstufen.

Editierbare Datei im gewählten Installationsstamm: `.plex/preset.toml`.

```toml
team = "pnet"
model_profile = "plus"
max_agents = 3

[codex.dev]
reasoning = "max"
```

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

Plex besitzt nur `<!-- plex:start -->` … `<!-- plex:end -->`. Persönliche Anweisungen
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
| `.plex/backups/` | Ersetzte Dateien und ausgeschiedene Rollen |

Generierte Rollen/Receipts nicht manuell bearbeiten. Fremde oder geänderte verwaltete
Dateien, Symlinks und parallele Applies blockieren unsichere Updates.
Gemeldeten Konflikt vor dem Refresh lösen und Backups behalten.

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
