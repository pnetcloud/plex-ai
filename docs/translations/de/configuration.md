# Konfiguration

[English](../../configuration.md) · [Русский](../ru/configuration.md) · [Deutsch](configuration.md) · [简体中文](../zh-CN/configuration.md)

[Installation, Entwicklungsmodus und alle CLI-Optionen](../../../readme/translations/de/installation.md).

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
