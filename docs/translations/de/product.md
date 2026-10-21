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

## Hauptchat und Team

Der **Root-Koordinator ist der aktuelle Chat**. Dort `plex` mit Aufgabe,
Rahmenbedingungen und erwartetem Ergebnis aufrufen. Er wählt sinnvolle Aufträge,
liefert Kontext, ordnet Abhängigkeiten und integriert geprüfte Ergebnisse.
Subagenten bearbeiten begrenzte Aufträge; der PM übernimmt Planungsaufgaben,
statt den Root-Koordinator zu ersetzen. Die Rollen sind ein Werkzeugkasten,
keine Pflichtstationen für jede Aufgabe.

Das Modell des Hauptchats wird im Client gewählt. Setup zeigt die Empfehlung
des gewählten Profils für die Koordination, stellt dieses Modell aber nicht ein.
Je nach Profil können Modell und Denkaufwand abweichen. Bei `inherit` bleibt
die Sitzungswahl ohne konkrete Empfehlung bestehen.
Leichtere Modelle können die Umsetzung übernehmen, während der Root koordiniert.

Das Profil konfiguriert **nur Subagenten**. Der Installationsplan trennt die
Empfehlung für den Hauptchat von den effektiven Rolleneinstellungen einschließlich
lokaler Overrides. Eine Rolle mit `inherit` folgt den Client-/Sitzungsvorgaben;
die Wahl im Hauptchat kann daher auch diese Kinder beeinflussen. Empfehlungen
sind Ausgangspunkte, kein gemessenes Optimum für Qualität oder Kosten.

Siehe [Rollenzuständigkeiten](role-contracts.md) und
[Installation](installation.md).

## Grenzen

Plex hat keinen eigenen Daemon oder UI. Ausgewählte BMad-Skills werden nur mit ausdrücklicher Zustimmung installiert. Plex ersetzt dessen
Workflows nicht, deployt keine Anwendungen und garantiert kein Modellrouting für
Workflow-Kinder. Gemini-Modelle über Antigravity bedeuten keine Gemini-CLI-Unterstützung.

Siehe [Konfiguration](configuration.md), [Kompatibilität](host-compatibility.md)
und [Messergebnisse](testing.md).
