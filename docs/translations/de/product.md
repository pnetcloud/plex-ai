# Über Plex

[English](../../product.md) · [Русский](../ru/product.md) · [Deutsch](product.md) · [简体中文](../zh-CN/product.md)

**Team zusammenstellen. Arbeit koordinieren.**

Plex ist ein Agent Harness für Softwareentwicklung mit OpenAI Codex, Anthropic
Claude Code und Google Antigravity. Es verbindet wiederverwendbare Skills, native
Agentenrollen, Teamkonfiguration und Modellprofile im bereits verwendeten Client.
Der Name stammt von *multiplex*: mehrere Beiträge teilen einen koordinierten Prozess.

## Zweck

Ein Team braucht klare Aufträge, passenden Kontext, eindeutige Schreibzuständigkeit
und Prüfungen des Ergebnisses. Plex macht diese Verantwortlichkeiten über Projekte
hinweg nachvollziehbar und wiederholbar. Orchestrierung wählt Rollen und ordnet
Abhängigkeiten; Koordination stimmt die Beiträge ab; der Harness stellt die Konfiguration.

## Prinzipien

- Sinnvolle Arbeit mit begrenztem Ergebnis und klarer Zuständigkeit delegieren.
- Rollen von Modellen trennen; Einstellungen der Root-Sitzung beibehalten.
- Benötigte Fähigkeiten wählen, statt jede Rolle obligatorisch aufzurufen.
- Projektanweisungen, Clientberechtigungen und echte Benutzerentscheidungen beachten.
- Verhalten und tatsächliches Routing prüfen, bevor Qualität oder Einsparungen behauptet werden.

## Zwei Vorgänge

1. **Konfigurieren:** Checkout-Installer oder `plex-setup` installiert gemeinsame Skills
   und wendet Team/Profil auf Projekt- oder Benutzerebene an.
2. **Koordinieren:** `plex` ausdrücklich aufrufen, wenn Teamarbeit sinnvoll ist.
   Installation und Aufgabenkomplexität allein aktivieren keine Koordination.

`pnet` arbeitet eigenständig. `bmad` aktiviert vorhandene BMad-Personas und Workflows;
BMad steuert Planung, Umsetzung, Reviews und anwendbare Freigaben.

## Grenzen

Plex hat keinen eigenen Daemon oder UI. Ausgewählte BMad-Skills werden nur mit ausdrücklicher Zustimmung installiert. Plex ersetzt dessen
Workflows nicht, deployt keine Anwendungen und garantiert kein Modellrouting für
Workflow-Kinder. Gemini-Modelle über Antigravity bedeuten keine Gemini-CLI-Unterstützung.

Siehe [Konfiguration](configuration.md), [Kompatibilität](host-compatibility.md)
und [Messergebnisse](testing.md).
