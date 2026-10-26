# Clientkompatibilität

[English](../../host-compatibility.md) · [Русский](../ru/host-compatibility.md) · [Deutsch](host-compatibility.md) · [简体中文](../zh-CN/host-compatibility.md)

Clients führen Agenten aus; Modellanbieter liefern Modelle. Ein Anbieterprofil fügt keinen Clientadapter hinzu.

| Client | Plex-Integration | Verifizierter Umfang |
|---|---|---|
| OpenAI Codex | TOML-Rollen, Plugin, Bereiche und Anweisungen | Isolierte Installation/Konfiguration und Live-Aufgaben |
| Anthropic Claude Code | Markdown-Rollen und Plugininstallationspfad | CLI 2.1.310: Manifestvalidierung, isolierte Plugininstallation und Konfiguration beider Teams; Live-Modelltests unbestätigt |
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

Codex-Subagenten erben Sandbox, Freigaben und MCP-Server vom Hauptchat. Plex lässt
`sandbox_mode` und `approval_policy` in Rollen-TOML weg. Berechtigungen in der
Hauptsitzung einstellen; Nur-Lese-Anweisungen erzeugen keine separate Sandbox.
Siehe die [Codex-Subagentenreferenz](https://learn.chatgpt.com/docs/agent-configuration/subagents).

## Delegation in Claude Code

Plex wählt native Rollen über `Agent.subagent_type`. Aufgabenlabels stehen in
`description` und im Auftrag: `name` kann einen Agent-Teams-Teammate starten.
Für `delegation = false` wird `disallowedTools: Agent` erzeugt. BMad-Rollen behalten
verschachtelte Delegation innerhalb der Rechte und Tiefenbegrenzung des Clients.
Siehe [Claude-Subagentenreferenz](https://code.claude.com/docs/en/sub-agents).

Modell- und Effort-Unterstützung hängen von Client und Modell ab. Sitzungs- und
Anbietervorgaben, darunter `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` und
`CLAUDE_CODE_EFFORT_LEVEL`, können Rolleneinstellungen übersteuern. Tatsächliche
Ausführung prüfen, bevor Routing als bestätigt gilt.

Claude-Setup verwaltet gezielte Allow-Regeln in `.claude/settings.local.json` (Benutzerbereich: `settings.json` im Claude-Konfigurationsordner). Die vollständige Installation ermittelt den tatsächlichen Cache-Pfad aus dem nativen Inventar und aktualisiert einen vorhandenen Plugin-Cache ausdrücklich. Roles-only-Refresh erhält den gespeicherten Paketpfad; ein eigenständiger Resolver verwendet seine eigene Paket-/Quellwurzel. Persönliche Regeln bleiben erhalten. Geänderte verwaltete Regeln gelten als Konflikt; die Deinstallation entfernt nur Plex-eigene Regeln, mit Backup und Rollback. BMad erhält Lesezugriff auf installierte Skill-Verzeichnisse, keine pauschale Runtime-Ausführung. BMad wird für Claude mit `--copy` installiert, getrennt von gemeinsam genutzten Codex-Skills.

Der geprüfte absolute Plugin-Pfad steht in Markdown Inputs. Dateiprüfungen beweisen weder Berechtigungen aktiver Sitzungen noch Modellrouting; Claude nach einem Plugin-Update neu starten. Tests umfassen CLI 2.1.310, Installation, Cache-Updates und Konfiguration, nicht jede Modell-/Profilkombination.
