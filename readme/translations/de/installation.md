# Installation

[English](../../installation.md) · [Русский](../ru/installation.md) · [Deutsch](../de/installation.md) · [简体中文](../zh-CN/installation.md)

## Installieren

Im Projektverzeichnis ausführen. Benötigt: Git, curl, die Client-CLI und uv oder Python 3.11+.

**Normal**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

**Entwicklungsmodus · Codex**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --dev --client codex
```

Client, Bereich, Team und Profil wählen, dann den Plan bestätigen. **Project** wird empfohlen. Anschließend eine neue Client-Sitzung öffnen.

## Häufige Befehle

Fehlt der optionale `plex`-Befehl, etwa nach einer ersten Dev-Installation, unten `~/.local/share/plex-ai/setup.sh` statt `plex` verwenden.

| Aufgabe | Befehl |
|---|---|
| Projekt konfigurieren oder aktualisieren | `plex` |
| Konfiguration prüfen | `plex status` |
| Neuen Release laden und Setup öffnen | `plex update` |
| Setup ohne Änderungen prüfen | `plex --dry-run --client codex --project .` |
| Entfernung anzeigen | `plex uninstall --dry-run` |
| Projektteam entfernen | `plex uninstall` |
| Status als JSON | `plex status --json` |
| Entfernungsplan als JSON | `plex uninstall --dry-run --json` |

Bei einem bereits installierten Team:

| Option | Zweck |
|---|---|
| **Update only** | Einstellungen behalten, verwaltete Dateien aktualisieren. |
| **Reconfigure** | Menüs mit gespeicherten Werten öffnen. |

Explizite CLI-Optionen gelten weiterhin. `plex` nutzt den aktuellen Checkout; `plex update` lädt einen neueren veröffentlichten Release einschließlich Vorschauen.

## Entwicklungsmodus

- Nur Codex und Bereich **project**. Beide Plex-Skill-Ordner verweisen auf den Quellcheckout; dieser muss verfügbar bleiben.
- Das Projekt deaktiviert das gemeinsame Plugin; der verwaltete Anweisungsblock wählt lokale Plex-Skills. Codex muss dem Projekt vertrauen. Cloud-Plugins und andere gleichnamige Skills bleiben unberührt.
- Skill-Änderungen folgen den Links. Rollen-, Profil- und Workflow-Katalogänderungen benötigen Setup-Aktualisierung und eine neue Sitzung. Der Modus bleibt bis `--no-dev` erhalten.

| Aufgabe | Befehl |
|---|---|
| Arbeitscheckout verknüpfen | `./setup.sh --dev --client codex --project /path/to/project` |
| Zum gemeinsamen Plugin zurückkehren | `./setup.sh --no-dev --client codex --project /path/to/project` |

## BMad

Node.js/npm und uv erforderlich. Team `bmad` im Menü wählen oder ausführen:

| Aufgabe | Befehl |
|---|---|
| Ausgewählte offizielle Skills und Projekt-Runtime installieren | `plex --team bmad --client codex --install-bmad` |
| Mit vorhandenen Skills initialisieren | `plex --team bmad --client codex --init-bmad` |

Skills gelten benutzerweit; ausgewählte Skill-Dateien können ersetzt werden. Die Runtime gehört zum Projekt. Installierte Abhängigkeiten/Runtime bleiben bei Abbruch oder späterem Fehler erhalten. Ohne Rückfragen `--project . --yes` ergänzen: angezeigte BMad-Standardwerte werden akzeptiert.

## Optionsreferenz

Ausgelassene Einstellungen behalten ihre Werte. Jeder angewendete Preset speichert `interaction`. Profile, Overrides und Pfade: [Konfiguration](../../../docs/translations/de/configuration.md).

### Clients und Bereich

| Option | Zweck |
|---|---|
| `--project PATH` | Vorhandenes Projektverzeichnis. |
| `--client CLIENT` | codex, claude oder antigravity; für mehrere Clients wiederholen. |
| `--host CLIENT` | Kompatibilitätsalias eines Clients; erlaubt Anbieterprofile. |
| `--scope project / user` | Bereich für Rollen/Anweisungen; Standard project. Normale Plugins sind benutzerweit. |
| `--instructions / --no-instructions` | Plex-Anweisungsblock verwalten oder überspringen. |

### Team und Modelle

| Option | Zweck |
|---|---|
| `--team pnet / bmad` | Rollensatz; bei Neuinstallation pnet. |
| `--model-profile PROFILE` | inherit, basic, plus, pro oder pro-plus. |
| `--interaction MODE` | interactive, balanced (Standard) oder auto. |
| `--max-agents N` | Positive Grenze gleichzeitiger Aufträge. |

### Ausführung und Ausgabe

| Option | Zweck |
|---|---|
| `--dev / --no-dev` | Lokale Skills verknüpfen oder Dev verlassen; nur Codex/project. |
| `--roles-only` | Plex-Plugin überspringen; explizite BMad-Optionen gelten weiter. |
| `--command / --no-command` | ~/.local/bin/plex erstellen (Standard) oder überspringen; Dev erstellt keinen Befehl. |
| `--install-command` | Nur den Befehl installieren; fremde Befehle bleiben erhalten, nicht mit --dev kombinierbar. |
| `--dry-run` | Vorschau ohne Schreiben; nicht mit --install-command kombinierbar. |
| `--yes` | Ohne Rückfragen anwenden; Client und Projektpfad erforderlich (Pfad bei --scope user optional). |
| `--json` | JSON für status oder uninstall einschließlich Vorschau. |
| `-h / --help` | Gruppierte Hilfe und Beispiele zeigen. |

### BMad

| Option | Zweck |
|---|---|
| `--install-bmad` | Ausgewählte benutzerweite Skills und fehlende Runtime autorisieren. |
| `--init-bmad` | Runtime mit installiertem offiziellem Setup initialisieren. |
| `--bmad-skill PATH` | Expliziter Pfad zum installierten BMad-Setup-Skill. |

### Quelle — update / GitHub-Bootstrap

| Option | Zweck |
|---|---|
| `--release TAG` | Veröffentlichten Tag verwenden, z. B. v0.5.2. |
| `--development` | main verwenden; aktiviert nicht --dev. |
| `--checkout PATH` | Nur GitHub-Bootstrap; Standard ~/.local/share/plex-ai. |

Der Bootstrap speichert den gemeinsamen Checkout in `~/.local/share/plex-ai`; verfügbar halten. Bootstrap/update mit `--dry-run` prüft nur die Quellauswahl; weitere Setup-Optionen werden weitergereicht.

## Dateischutz und Fehlerbehebung

- Entfernen gilt standardmäßig für das Projekt. Mit `--client codex` begrenzen, mit `--scope user` Benutzerrollen wählen; `--yes` bestätigt ohne Rückfragen.
- Nur unveränderte eigene Rollen, Anweisungsblöcke und Dev-Links/-Overrides werden entfernt. Gemeinsame Plugins, Quellen, Einstellungen und Backups bleiben; geänderte eigene Dateien oder unbekannte Formate stoppen Änderungen.
- Quellupdates lehnen veränderte, fremde oder verlinkte Checkouts ab. Plugin-Änderungen und abgeschlossene Client-Installationen sind vom Rollen-Rollback getrennt.
- `status` prüft zuerst Projekt-, sonst Benutzerkonfiguration. Es prüft Konfiguration/Plugin-Erkennung, nicht tatsächliches Modellrouting.

| Wenn… | Verwenden |
|---|---|
| plex nicht im PATH liegt | ~/.local/bin/plex oder ./setup.sh aus dem Checkout. |
| Der Befehl zu einem anderen Checkout gehört | Den ausgegebenen setup.sh-Pfad; fremde Befehle bleiben erhalten. |
| Skills oder verwaltete Dateien kollidieren | Die gemeldete Datei prüfen; Setup überschreibt sie nicht. |
| Ein vorhandener Plugin-Override --dev blockiert | enabled manuell auf false setzen; vorhandene Overrides bleiben beim Verlassen erhalten. |

## Ausgabe

Farben gelten nur im Terminal. `NO_COLOR=1` oder `TERM=dumb` wählt schlichte Ausgabe und nummerierte Menüs; Umleitungen bleiben schlicht. `--json` hält stdout frei von Formatierung und Fortschrittsmeldungen.
