# Installation und CLI-Referenz

[English](../../installation.md) · [Русский](../ru/installation.md) · [Deutsch](../de/installation.md) · [简体中文](../zh-CN/installation.md)

Benötigt: Git, curl, die ausgewählte Client-CLI und uv oder Python 3.11+. BMad-Abhängigkeiten benötigen außerdem Node.js/npm und uv.

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


## Vorhandene Installationen und Kompatibilität

Nach Auswahl von Client, Bereich und Projekt erkennt Setup ein vorhandenes Team
an seinem Installationsbeleg und bietet **Update only** (`refresh`) oder
**Reconfigure** (`configure`) an. Standard ist Update; explizite Einstellungsoptionen
machen Reconfigure zur Vorauswahl. Update überspringt Fragen zu Team, Profil,
Interaktion und Parallelität und behält die Entscheidung zum Anweisungsblock pro
Client bei. Explizite CLI-Overrides gelten weiterhin; der Plan muss bestätigt werden.
Bei mehreren Clients gilt die Aktion weiter, sobald das erste vorhandene Team
gefunden wurde. Ein gemeinsames Plugin allein ist kein installiertes Projektteam.

Mit `--yes` bleiben Einstellungen ohne explizite Overrides erhalten. Reconfigure
öffnet normale Menüs mit gespeicherten Werten. Fehlende BMad-Voraussetzungen können
weiterhin Entscheidungen erfordern; Update bietet keinen Teamwechsel an. Es nutzt
die Definitionen dieses Checkouts; neue Quellen zuerst mit `plex update` oder dem
GitHub-Installer laden. Der lokale Entwicklungsmodus bleibt erhalten.

Kompatibilität bleibt im vorhandenen Resolver: fehlende Standardwerte ergänzen,
Overrides behalten und unterstützte alte Marker migrieren. Anbieterspezifische
Profil-IDs bleiben beim Update erhalten. Bestehende Backups und Besitzprüfungen
schützen ersetzte verwaltete Dateien. Bearbeitete verwaltete Dateien oder unbekannte
Konfigurations-/Belegfelder stoppen die Operation; persönliche Texte und fremde
Dateien bleiben erhalten. Kein erzwungenes Zurücksetzen und kein allgemeines
Migrationsframework. Plugin-Manager-Änderungen sind vom Rollen-Rollback getrennt.

## Lokale Entwicklung mit Codex

Ein Testprojekt direkt mit dem Plex-Arbeitsverzeichnis verbinden:

```sh
./setup.sh --dev --client codex --project /path/to/test-project
```

Verfügbar ab v0.5.0; den Checkout verwenden, dessen Skills getestet werden sollen.

`--dev` unterstützt Codex auf Projektebene. Die vollständigen Skill-Ordner `plex`
und `plex-setup` werden nach `.agents/skills/` verlinkt; `pnet-plex@pnet-plex` wird
in der projektlokalen `.codex/config.toml` deaktiviert. Benutzerkonfiguration und
andere Projekte bleiben unverändert. Codex muss dem Projekt vertrauen, um dessen
Konfiguration zu laden. Cloud-Plugins und andere gleichnamige Skills bleiben davon unberührt.

Der verwaltete Block in `AGENTS.md` bzw. der ausgewählten Anweisungsdatei verlangt,
diese beiden Plex-Skills ausschließlich aus dem Projekt zu verwenden. Zuerst die
Symlinks auflösen: Referenzen, Prüfskript, `teams/`, Koordinator und Profile stammen
aus demselben Checkout. BMad bleibt eine separat installierte Abhängigkeit.
Das Arbeitsverzeichnis muss verfügbar bleiben.

Skill-Änderungen sind über die Links verfügbar; eine neue Codex-Sitzung lädt sie.
Nach Änderungen an Rollen, Profilen oder dem Workflow-Katalog Setup erneut starten.
`plex status --client codex` zeigt die konfigurierte Entwicklungsquelle und prüft
Links und lokale Plugin-Deaktivierung, nicht die tatsächliche Modell-Sitzung.
Erneutes Setup behält den Modus bei, sofern `--no-dev` nicht angegeben wird.

```sh
./setup.sh --no-dev --client codex --project /path/to/test-project
```

`--no-dev` entfernt eigene Links und die eigene Plugin-Deaktivierung, aktualisiert
das Team und setzt die gemeinsame Plugin-Installation fort. Auch `plex uninstall`
entfernt den Entwicklungszustand. Fremde Skills und geänderte Links/Overrides
blockieren Änderungen. Vorhandene explizite Plugin-Overrides bleiben erhalten:
`enabled = true` vor `--dev` manuell auf `false` setzen; ein zuvor gesetztes `false`
bleibt nach dem Verlassen bestehen. Persönlicher Anweisungstext bleibt erhalten.
`.plex/dev.json` speichert Quelle und Besitz des Overrides; diesen lokalen Zustand
nicht committen. `--dry-run` schreibt nichts. `--dev` ist unabhängig von
`plex update --development`, das `main` auswählt.

## Terminalausgabe

Setup, Status, Quellupdates und Entfernen verwenden einheitliche Überschriften,
ausgerichtete Einstellungen, Agenten-/Modelltabellen und hervorgehobene Befehle.
Grün kennzeichnet Erfolg, Gelb Warnungen, Rot Fehler; Pfade und Hinweise erscheinen
gedämpft. Der Plan zeigt die Anweisungsdatei ohne vollständige Vorlagenausgabe.
Schmale Terminals zeigen Agenteneinstellungen untereinander statt als Tabelle.

Farben und Hervorhebungen gelten nur im Terminal. Umgeleitete Ausgabe bleibt schlicht;
`NO_COLOR=1` oder `TERM=dumb` aktiviert ebenfalls schlichte Ausgabe und nummerierte Menüs.
`--help` gruppiert Optionen nach Zweck. Status und Entfernen unterstützen `--json`,
auch für Entfernungsvorschauen; stdout enthält dann nur JSON ohne Dekoration oder Fortschrittsmeldungen.

```sh
plex --help
plex status
plex status --json
plex uninstall --dry-run
plex uninstall --dry-run --json
NO_COLOR=1 plex status
```

## Befehle

| Befehl | Verhalten |
|---|---|
| `plex setup` | Setup öffnen; auch Standard ohne Befehl. |
| `plex status` | Konfiguration und Plugin-/Quellenerkennung ohne Änderungen prüfen; --json verfügbar. |
| `plex update` | Ausgewählte Version herunterladen und Setup öffnen. |
| `plex uninstall` | Unveränderte eigene Rollen, Anweisungen und Entwicklungslinks/-Override entfernen; gemeinsame Abhängigkeiten, Checkout und Einstellungen behalten. |

`status` und `uninstall` akzeptieren `--project`, wiederholtes `--client` (oder `--host`) und `--scope`. Entfernen unterstützt `--dry-run` und `--yes`. `--dev`/`--no-dev` gelten nur für Setup; Status und Entfernen erkennen den Modus automatisch.

## Alle Setup-Optionen

Interaktives Setup fragt den Modus einmal für alle ausgewählten Clients ab; vorausgewählt ist der gespeicherte Modus, sonst `balanced`. Jeder angewendete Preset speichert `interaction` ausdrücklich, auch nach Aktualisierung älterer Konfigurationen.

| Option | Verhalten |
|---|---|
| `--project PATH` | Vorhandenes Zielprojekt; interaktives Setup fragt sonst nach dem Pfad. |
| `--client codex\|claude\|antigravity` | Client auswählen; für mehrere Clients wiederholen. |
| `--host CLIENT` | Kompatibilitätsalias für einen Client; unterstützt auch anbieterspezifische Profile. |
| `--scope project\|user` | Rollen und Anweisungsblock auf Projekt- (Standard) oder Benutzerebene; das normale Plugin bleibt benutzerweit. |
| `--team pnet\|bmad` | Rollensatz; gespeicherte Auswahl beibehalten, bei Neuinstallation pnet. |
| `--model-profile PROFILE` | Gemeinsame Stufe: inherit, basic, plus, pro, pro-plus; gespeichertes Profil beibehalten. Anbieter-IDs stehen in der Konfiguration. |
| `--interaction interactive\|balanced\|auto` | Fragerichtlinie der Agenten; gespeicherter Wert, sonst balanced. |
| `--max-agents N` | Positive Grenze gleichzeitiger Aufträge; gespeicherten Wert beibehalten. |
| `--instructions / --no-instructions` | Nur den Plex-Anweisungsblock verwalten (Standard) oder überspringen. |
| `--dev / --no-dev` | Nur Codex auf Projektebene: Live-Links zum Checkout oder Entwicklungsmodus verlassen. Benötigt verwaltete Anweisungen; ohne Option bleibt der Modus erhalten. |
| `--install-bmad` | Ausgewählte offizielle benutzerweite BMad-Skills und fehlende Projekt-Runtime installieren; ausgewählte Skill-Dateien können ersetzt werden. |
| `--init-bmad` | Fehlende BMad-Projekt-Runtime mit installiertem offiziellem Setup initialisieren. |
| `--bmad-skill PATH` | Expliziter Pfad zum installierten offiziellen BMad-Setup-Skill. |
| `--roles-only` | Plex-Plugin-Installation überspringen; explizite BMad-Abhängigkeitsoptionen gelten weiterhin. |
| `--command / --no-command` | Optionalen Befehl ~/.local/bin/plex erstellen (Standard) oder überspringen; Entwicklungsmodus installiert ihn nicht. |
| `--install-command` | Nur den Befehl für diesen Checkout installieren; fremde Befehle bleiben erhalten. Nicht mit --dev kombinierbar. |
| `--dry-run` | Vorschau ohne Schreibzugriffe; nicht mit --install-command kombinierbar. |
| `--yes` | Ohne Rückfragen anwenden; Client und Projektpfad angeben (Pfad bei --scope user optional). BMad verwendet angezeigte Standardwerte. |
| `--json` | Maschinenlesbare Ausgabe für status oder uninstall. |
| `-h / --help` | Verfügbare Argumente anzeigen. |

## Download- und Update-Optionen

Veröffentlichter Tag: `plex update --release TAG`; `main`: `plex update --development`. Der GitHub-Bootstrap akzeptiert dieselben Quelloptionen und `--checkout PATH` (Standard `~/.local/share/plex-ai`); `--checkout` ist keine Setup-Option. Bootstrap/update mit `--dry-run` prüft nur die Quellauswahl. Weitere Setup-Optionen werden weitergereicht. Beispiel:

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --release v0.5.1
```

Prioritäten und verwaltete Dateien: [Konfiguration](../../../docs/translations/de/configuration.md).
