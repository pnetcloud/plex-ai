# pNet Plex

[English](README.md) · [Русский](README.ru.md) · [Deutsch](README.de.md) · [简体中文](README.zh-CN.md)

**Team zusammenstellen. Arbeit koordinieren.**

Plex ist ein **Agent Harness für Multi-Agent-Orchestrierung und Koordination** in
OpenAI Codex, Anthropic Claude Code und Google Antigravity. Ein wiederverwendbares
Team installieren, Modellprofil wählen und Plex mit Umsetzung, Review und Prüfung beauftragen.

**[v0.3.1 Preview](https://github.com/pnetcloud/plex-ai/releases/tag/v0.3.1)** — Open Source, MIT. Zum Ausprobieren; Schnittstellen können sich ändern.

## Schnellstart

Benötigt werden **Git und curl**, die gewählte Client-CLI und **uv oder Python 3.11+**.
Im eigenen Projekt starten oder ein leeres Testprojekt anlegen:

```sh
mkdir plex-demo && cd plex-demo
```

Mit einem Befehl direkt aus GitHub installieren:

```sh
curl -fsSL https://raw.githubusercontent.com/pnetcloud/plex-ai/main/install.sh | bash
```

Der Installer öffnet ein interaktives Menü:

1. Clients mit **Leertaste** auswählen, mit **Enter** fortfahren (ohne uv per Nummerneingabe).
2. Für diesen Test **Project** beibehalten und den Projektordner bestätigen.
3. Das eigenständige Team **pnet** und **Inherit** für die Modelleinstellungen der Sitzung wählen.
4. Den Installationsplan jedes Clients prüfen und bestätigen.

Das installiert das gemeinsame Plugin, native Teamrollen und einen verwalteten Anweisungsblock.
Denselben Befehl erneut ausführen, um Updates zu laden und Setup zu öffnen.

## Erste Aufgabe ausprobieren

Eine **neue Sitzung** des Coding-Clients in `plex-demo` oder dem eigenen Projekt öffnen.
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
| **bmad** | Vorhandene BMad-Skills/Workflows mit Rollenmodellen; separat installiertes BMad und Projekt-Runtime nötig |

Profile: **Inherit, Basic, Plus, Pro, Pro+**. Eine Stufe gilt für alle gewählten Clients;
Rollen-Overrides sind möglich. Plex verwaltet nur den markierten Block und erhält umgebende Projektanweisungen.

Zum Ändern der Einstellungen oder Einrichten eines anderen Projekts **im Terminal** aus dessen Ordner starten:

```sh
~/.local/bin/plex
```

Dieser Befehl öffnet Setup; die Plex-Anfrage im Client startet Koordination.
Updates, Benutzerbereich, Flags und Overrides: [Konfiguration](docs/translations/de/configuration.md).

## Prüfen, aktualisieren oder entfernen

```sh
plex status
plex update
plex uninstall --dry-run
```

`plex uninstall` zum Bestätigen starten. Falls `plex` nicht im PATH liegt, `~/.local/bin/plex` verwenden.
Installation und Updates wählen veröffentlichte Versionen einschließlich Vorschauen.

## Weiterführend

- [Dokumentation](docs/translations/de/README.md) — Einrichtung und Nutzung.
- [Über Plex](docs/translations/de/product.md) — Zweck und Prinzipien.
- [Kompatibilität](docs/translations/de/host-compatibility.md) — Live-Tests für Codex und ausgewählte Antigravity-Konfigurationen; native Claude-Code-Aufgaben noch ungeprüft.
- [Tests und Effizienz](docs/translations/de/testing.md) — Methodik, Token-/Kostenmessungen und subjektive Qualitätsbewertung.
- [Architektur](docs/translations/de/architecture.md) — Zusammenspiel von Konfiguration und Koordination.

## Lizenz

[MIT](LICENSE). Agentenanweisungen adaptieren [Awesome Codex Subagents](https://github.com/VoltAgent/awesome-codex-subagents);
siehe [Drittanbieterhinweise](THIRD_PARTY_NOTICES.md).
