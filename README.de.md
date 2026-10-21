# pNet Plex

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [简体中文](README.zh-CN.md)

**Team zusammenstellen. Arbeit koordinieren.**

Plex ist ein **Agent Harness für Multi-Agent-Orchestrierung und Koordination** in
OpenAI Codex, Anthropic Claude Code und Google Antigravity. Ein wiederverwendbares
Team installieren, Modellprofil wählen und Plex mit Umsetzung, Review und Prüfung beauftragen.

**[v0.5.4 Preview](https://github.com/pnetcloud/plex-ai/releases/tag/v0.5.4)** — Open Source, MIT. Zum Ausprobieren; Schnittstellen können sich ändern.

## Schnellstart

Im eigenen Projektverzeichnis ausführen.

**Normale Installation**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

**Entwicklungsmodus — Codex, projektlokale Plex-Skills**

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash -s -- --dev --client codex
```

Die normale Installation öffnet ein interaktives Menü:

1. Clients mit **Leertaste** auswählen, mit **Enter** fortfahren (ohne uv per Nummerneingabe).
2. Installationsbereich wählen (**Project** empfohlen) und den Projektordner bestätigen.
3. Das eigenständige Team **pnet** und **Inherit** für die Modelleinstellungen der Sitzung wählen.
4. **Balanced** für normale Zusammenarbeit wählen, alternativ **Interactive** / **Auto**.
5. Den Installationsplan jedes Clients prüfen und bestätigen.

Die normale Installation ergänzt das gemeinsame Plugin, Teamrollen und einen verwalteten Anweisungsblock.
Denselben Befehl erneut ausführen, um Updates zu laden und Setup zu öffnen.

[Installation und alle Optionen](readme/translations/de/installation.md).

Für bereits eingerichtete Clients im gewählten Bereich: **Update only** behält Einstellungen; **Reconfigure** öffnet die Setup-Menüs erneut.

## Erste Aufgabe ausprobieren

Eine **neue Sitzung** des Coding-Clients im Projekt öffnen.
Bei Bedarf Plugins/Agenten neu laden und folgende Anfrage senden:

```text
Nutze Plex, um eine responsive Buchungsseite für eine Fokussitzung zu erstellen.
Reines HTML, CSS und JavaScript: Name, E-Mail und Dauer 25/50 Minuten.
Eingaben prüfen und lokal bestätigen, ohne Daten zu speichern oder zu senden.
Änderungen reviewen, verfügbare Prüfungen ausführen und tatsächlich Geprüftes nennen.
```

Plex wählt passende Rollen, implementiert die Seite und koordiniert Review/Prüfungen.
Erwartet werden Quelldateien, ein lokaler Vorschaubefehl sowie Prüfergebnisse und offene Lücken.
Installation allein startet keine Orchestrierung — **Plex ausdrücklich anfordern**.

Problem gefunden? [Issue öffnen](https://github.com/pnetcloud/plex-ai/issues) mit Client/Version,
Team/Profil, Befehl oder Anfrage sowie erwartetem und tatsächlichem Verhalten.
Geheimnisse vor dem Anhängen aus Logs entfernen.

## Teams und Modelle

| Team | Einsatz |
|---|---|
| **pnet** | Allgemeine Entwicklung mit PM, explorer, researcher, dev, reviewer und QA; kein BMad nötig |
| **bmad** | BMad-Skills/Workflows mit Rollenmodellen; Setup bietet Installation ausgewählter Skills und Projektinitialisierung |

Profile: **Inherit, Basic, Plus, Pro, Pro+**. Eine Stufe gilt für alle gewählten Clients;
Rollen-Overrides sind möglich. Plex verwaltet nur den markierten Block und erhält umgebende Projektanweisungen.

Zum Ändern der Einstellungen oder Einrichten eines anderen Projekts **im Terminal** aus dessen Ordner starten:

```sh
~/.local/bin/plex
```

Dieser Befehl öffnet Setup; die Plex-Anfrage im Client startet Koordination.
Team-/Profil-Overrides: [Konfiguration](docs/translations/de/configuration.md).

## Prüfen, aktualisieren oder entfernen

```sh
plex status
plex update
plex uninstall --dry-run
```

`plex uninstall` zum Bestätigen starten. Falls `plex` fehlt, stattdessen
`~/.local/share/plex-ai/setup.sh` verwenden, auch nach einer ersten Dev-Installation.
Installation und Updates wählen veröffentlichte Versionen einschließlich Vorschauen.

## Plex lokal entwickeln

Aus dem Plex-Arbeitsverzeichnis ein Codex-Testprojekt verbinden:

```sh
./setup.sh --dev --client codex --project /path/to/test-project
```

Live-Links verwenden diesen Checkout; der verwaltete Anweisungsblock verlangt die projektlokalen Plex-Skills. Das gemeinsame Plugin wird nur in diesem Projekt deaktiviert. Mit `--no-dev` zur normalen Installation zurückkehren. Codex nach Änderungen neu öffnen.

[Installation und alle Optionen](readme/translations/de/installation.md).

## Weiterführend

- [Dokumentation](docs/translations/de/README.md) — Einrichtung und Nutzung.
- [Über Plex](docs/translations/de/product.md) — Zweck und Prinzipien.
- [Kompatibilität](docs/translations/de/host-compatibility.md) — Live-Tests für Codex und ausgewählte Antigravity-Konfigurationen; native Claude-Code-Aufgaben noch ungeprüft.
- [Tests und Effizienz](docs/translations/de/testing.md) — Methodik, Token-/Kostenmessungen und subjektive Qualitätsbewertung.
- [Architektur](docs/translations/de/architecture.md) — Zusammenspiel von Konfiguration und Koordination.

## Lizenz

[MIT](LICENSE). Agentenanweisungen adaptieren [Awesome Codex Subagents](https://github.com/VoltAgent/awesome-codex-subagents);
siehe [Drittanbieterhinweise](THIRD_PARTY_NOTICES.md).
