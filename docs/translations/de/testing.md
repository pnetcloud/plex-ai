# Tests und Effizienz

[English](../../testing.md) · [Русский](../ru/testing.md) · [Deutsch](testing.md) · [简体中文](../zh-CN/testing.md)

## Umfang und Methode

Zeitraum: 16.–18. Oktober 2026. Die Entwicklungsproben verwenden eine Aufgabe:
Focus Session, ein responsives lokales HTML/CSS/JS-Formular mit Validierung,
Dauerübersicht, Tastaturbedienung und reduzierter Bewegung, ohne Backend oder Speicherung.
Die unabhängige Chromium-Abnahme umfasst 12 Prüfungen. Die Laufzeit enthält Agentenarbeit,
eigene Tests und Reviews, jedoch weder Einrichtung noch unabhängige Abnahme.
Zeiten sind auf die nächste Sekunde gerundet.

Die Tabellen zeigen erhaltene abgeschlossene Läufe, nicht alle Versuche oder eine
Erfolgsquote. Quoten- und Workflowabbrüche gelten nicht als Abschluss. Rohsitzungen und Auditbelege liegen
außerhalb dieser Dokumentation; hier stehen nur geprüfte Zusammenfassungen.

## Neueste Codex-Ergebnisse

| Konfiguration | Zeit | Token gesamt (Mio.) | Schätzung USD | Prüfungen |
|---|---|---|---|---|
| pnet Basic | 4:20 | 1.751 | $0.0396 | 12/12 |
| pnet Plus | 6:01 | 1.482 | $0.1799 | 12/12 |
| BMad Basic | 4:56 | 2.007 | $0.0404 | 12/12 |
| BMad Plus | 14:32 | 7.165 | $0.2007 | 12/12 |

## Tokenzählung

| Konfiguration | Eingabe ohne Cache | Eingabe aus Cache | Ausgabe | Davon Reasoning |
|---|---|---|---|---|
| pnet Basic | 106,523 | 1,618,560 | 25,550 | 7,770 |
| pnet Plus | 217,927 | 1,233,280 | 30,712 | 13,421 |
| BMad Basic | 106,604 | 1,878,912 | 21,980 | 7,769 |
| BMad Plus | 238,379 | 6,842,752 | 84,355 | 58,210 |

Token werden über Modellantworten und alle Kindersitzungen summiert; sie beschreiben
nicht die Größe eines einzelnen Kontexts. Nur die eigene Nutzung jeder Sitzung zählt
einmal; wiederholte geerbte Historie bleibt ausgeschlossen. Gesamt = Eingabe ohne Cache
+ Cache-Eingabe + Ausgabe. Reasoning ist bereits in der Ausgabe enthalten.
Die neuesten Codex-Summen wurden mit Tokscale abgeglichen.

## Weitere abgeschlossene Tests

| Konfiguration | Datum | Zeit | Token (Mio.) | Schätzung USD |
|---|---|---|---|---|
| Codex BMad Pro | 2026-10-16 | 12:34 | 5.947 | $0.1876 |
| Codex BMad Pro+ | 2026-10-16 | 5:13 | 1.651 | $0.7396 |
| Antigravity Claude Pro (Sonnet) | 2026-10-17 | 2:35 | 2.175 | $1.4302 |
| Antigravity Claude Plus (Sonnet) | 2026-10-17 | 3:19 | 2.308 | $1.5214 |
| Antigravity Google Basic (Flash) | 2026-10-17 | 10:50 | 4.760 | $0.1878 |

Alle aufgeführten Läufe bestanden 12/12. Diese älteren Konfigurationen unterscheiden
sich von den aktuellen Profilen. Claude Pro verwendete hier tatsächlich Sonnet;
dies ist kein abgeschlossener Opus-Test. Historische Quotenabbrüche belegen keine aktuellen Kontolimits.

## Qualitätsbewertung

Nach qualitativer Einschätzung des Projekteigentümers ist **BMad Basic bei der
wahrgenommenen Ergebnisqualität mit pnet Plus vergleichbar**: ungefähr eine Profilstufe
Gewinn durch die Methodik. Das ist eine Expertenbeobachtung und Hypothese für weitere
Tests. BMad-Artefakte umfassen eine minimale Spezifikation und Review-Triage; identische
12/12 messen diesen Qualitätsunterschied nicht und belegen auch nicht seine Ursache.

UX, Vollständigkeit, Wartbarkeit, verbleibende Fehler und Prüfqualität sollten getrennt
von Zeit/Kosten bewertet werden, möglichst blind über mehrere Aufgaben und Wiederholungen.

## Grenzen und praktische Folgerungen

- Einzelne Läufe mit unterschiedlichen Prompts, Routen, Caches und Werkzeugen erlauben keine statistische Rangfolge von Profilen oder Anbietern.
- Kosten sind API-äquivalente Schätzungen zu historischen Sätzen, keine aktuellen Preise, Abonnementquoten oder Providerrechnungen. USD pro Million Eingabe-/Cache-/Ausgabe-Token: Luna 0.10/0.01/0.50; Sol 2/0.10/10; Astra 10/1/50; Sonnet 3/0.30/15; Flash 0.15/0.015/0.60.
- Erfolgreiches Rendern beweist keine Modellwahl zur Laufzeit. BMad-interne Reviewer nutzten nicht automatisch das eigenständige Reviewer-Profil. Tatsächliche Kindmodelle protokollieren.
- Der letzte Build verwendete einen global installierten BMad-Skill; die Pluginliste allein identifizierte den aktiven Workflow nicht. Ein reiner Pluginbetrieb ist nicht separat verifiziert.
- Codex lief in isolierten Profilen mit einer VM-spezifischen Vollzugriffsanpassung. Normaler Sandboxbetrieb und Screenreader-Ausgabe sind nicht belegt.
- pnet Basic war unter den vier jüngsten abgeschlossenen Läufen am schnellsten und günstigsten. Daraus folgen weder allgemeine Überlegenheit noch garantierte Vorteile höherer Profile.

Neue Vergleiche verwenden den [Versuchsplan](templates/experiment-plan.md) und die [Berichtsvorlage](templates/evaluation-report.md).
