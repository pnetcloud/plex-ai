# Clientkompatibilität

[English](../../host-compatibility.md) · [Русский](../ru/host-compatibility.md) · [Deutsch](host-compatibility.md) · [简体中文](../zh-CN/host-compatibility.md)

Clients führen Agenten aus; Modellanbieter liefern Modelle. Ein Anbieterprofil fügt keinen Clientadapter hinzu.

| Client | Plex-Integration | Verifizierter Umfang |
|---|---|---|
| OpenAI Codex | TOML-Rollen, Plugin, Bereiche und Anweisungen | Isolierte Installation/Konfiguration und Live-Aufgaben |
| Anthropic Claude Code | Markdown-Rollen und Plugininstallationspfad | Rendering/Konfiguration; native Live-Ausführung noch unbestätigt |
| Google Antigravity | Markdown-Rollen und Pluginpaket | Installation/Konfiguration und ausgewählte Live-Modelltests |

Die Abdeckung gilt nur für getestete Versionen/Einstellungen; siehe [Tests](testing.md).
Gemini CLI ist ein separater, nicht unterstützter Client. Weitere Adapter liegen außerhalb des aktuellen Umfangs.

## Modell- und Berechtigungsgrenzen

Codex rendert `model` und `model_reasoning_effort`; Claude Code/Antigravity rendern
`model` und `effort`. Verfügbarkeit hängt vom tatsächlichen Client/Modell ab.
Antigravity-Rendering akzeptiert `inherit`, `flash_lite`, `flash`, `pro`. Eine explizite
Familien-ID im Profil beweist keine native Ausführbarkeit; nicht unterstütztes Routing
wird gemeldet statt still ersetzt. `inherit` folgt der Elternsitzung und kann nicht
für jedes Kind unabhängig Sonnet oder Opus wählen.

Native Rechte und Limits bleiben maßgeblich. Rollennamen, Profile und erfolgreiches
Rendering belegen weder Werkzeugisolation noch Parallelität oder Modellwahl. Plex
aktiviert keinen anderen Client und lockert keine globalen Rechte, um Adapter nutzbar zu machen.
