# Entwicklung

[English](../../development.md) · [Русский](../ru/development.md) · [Deutsch](development.md) · [简体中文](../zh-CN/development.md)

## Quellstruktur

| Pfad | Zuständigkeit |
|---|---|
| `install.sh` | Download/Update aus GitHub |
| `setup.sh`, `setup.py` | Installer und optionale `plex`-Verknüpfung |
| `skills/plex/` | Expliziter Koordinationseinstieg und Preflight |
| `skills/plex-setup/` | Setup, Resolver und Anweisungsblockvorlage |
| `teams/<team>/` | Team, Root-Vertrag, Rollen und Profile |
| `plugins/<host>/` | Native Manifestvorlagen |
| `.build/plugins/<host>/` | Generierte eigenständige Pakete |
| `tests/` | Konfiguration, Pakete und isolierte Installation |
| `docs/` | Englische Quelle und Übersetzungen |
| `_bmad/custom/` | BMad-Anpassungen für die Entwicklung |

Vor Verhaltensänderungen Produkt, Architektur und Konfiguration lesen; vor Prompt- oder
Teamänderungen die Rollenverträge. Fremde Arbeitsänderungen bewahren.
Ohne Auftrag weder committen noch veröffentlichen.

## Prüfungen

Portable Tests liegen in `tests/`. CI prüft Python 3.11/3.14 auf Linux/macOS;
Veröffentlichung erfordert erfolgreiche Jobs. Native Prüfungen werden ohne passende
CLI übersprungen. Modellläufe/private Benchmarks bleiben separat. Im Repository-Stamm ausführen:

```sh
uv run --with pyyaml --with questionary==2.1.1 python -m unittest discover -s tests -v
```

Tests decken Auflösung, Bereiche, Blöcke, Overrides, Konflikte, Rollback, Rendering,
Pakete und temporäre Installationen bei verfügbarem CLI ab. Keine Modellaufrufe.
Konfigurationsprüfungen belegen kein Live-Routing, Qualität, Latenz oder Einsparungen;
dafür das [Prüfprotokoll](../../../EVALUATION.md) verwenden. Messübersichten stehen unter
[Tests](testing.md), Rohbelege werden getrennt aufbewahrt.

## BMad für die Repository-Entwicklung

Die vorgesehenen offiziellen BMad-Skills/Plugins über den Clientmanager installieren,
dann den Setup-Ablauf des installierten Toolbox-`bmad` aus dem Repository nutzen.
Er erzeugt `_bmad/`; gemeinsame Anpassungen verweisen auf `docs/` und `_bmad-output/`.
Keine Runtime aus Vendor-Checkouts kopieren und keinen zweiten Bootstrap erfinden.

Mit vorhandener Runtime die Konfiguration prüfen:

```sh
uv run _bmad/scripts/resolve_config.py --project-root .
```

Bei globalen und Plugin-Kopien die tatsächlich aktive Skillidentität auflösen.
Projekt-Setup darf globale Skills nicht nebenbei löschen oder aktualisieren.

## Pakete und Dokumentation

Öffentliche Verzeichnisse und Dateitypmuster in `.gitignore` bestimmen den Export. Entwicklungs-Runtime, Maschinenpfade,
Registries und rohe Experimente gehören nicht in Clientpakete. Manager installieren
`.build/plugins/<host>`, nicht allein Manifestvorlagen. Registrierte lokale Quellen
erhalten. Installeränderungen nutzen den bestehenden Resolver/Anwendungspfad.

Englische Seiten liegen in `docs/`; `translations/ru`, `translations/de` und
`translations/zh-CN` spiegeln Dateinamen und Vorlagenordner. Versionen und Navigation
zusammen aktualisieren. Benchmarkzahlen gleich halten, qualitative Bewertungen
kennzeichnen und veraltete Forschungs-/Migrationsnotizen aus aktuellen Anleitungen entfernen.

Die `README.md` im Stamm ist der englische Projektüberblick. Übersetzungen liegen
in `docs/translations/<Sprache>/README.md`, ihre Anleitungsübersichten in `index.md`.
Die Installationsanleitung liegt mit den anderen Anleitungen in `docs/`.
