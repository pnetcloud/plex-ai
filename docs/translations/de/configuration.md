# Konfiguration

[English](../../configuration.md) · [Русский](../ru/configuration.md) · [Deutsch](configuration.md) · [简体中文](../zh-CN/configuration.md)

## Installation und Aktualisierung

Für die Erstinstallation den [Schnellstart](../../../README.de.md#schnellstart) verwenden.
Der GitHub-Befehl lädt den Branch `main` nach `~/.local/share/plex-ai` und startet Setup,
ohne das aktuelle Zielprojektverzeichnis zu wechseln.

Diesen Checkout aus dem Zielprojekt aktualisieren:

```sh
git -C "$HOME/.local/share/plex-ai" pull --ff-only && \
  "$HOME/.local/share/plex-ai/setup.sh"
```

`git clone` nicht in einen vorhandenen Checkout wiederholen. Bei anderem Speicherort
dessen Pfad nutzen. Den Setup-Plan prüfen, neue Rollen/Profile anwenden und den Client
neu laden. `~/.local/bin/plex` im Terminal öffnet Setup; die Plex-Anfrage im Client
startet Koordination.

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

Definitionen liegen in `teams/<team>/team.toml`, `agents/<host>/` und `profiles/*.toml`.
Anbieterdateien deklarieren einen Client und unabhängige Stufen, ohne Include-Ketten.
Genaue Modell-IDs und Effort-Werte gehören dorthin, nicht in duplizierte Dokumentationstabellen.

Anbieterspezifische IDs wie `openai-plus` oder `google-anthropic-plus` sind über
Einzelclient-Setup mit `--host` und den Resolver verfügbar. Multi-Client-Setup mit
`--client` nutzt gemeinsame Stufen. Das Einzelclient-Custom-Menü bearbeitet Rollen-
Overrides eines benannten Profils; `custom` ist kein gespeichertes Profil.
Modellverfügbarkeit hängt vom Client und Provider ab.

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
