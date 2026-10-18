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

## Testablauf

1. Die eingefrorene Focus-Session-Aufgabe in ein neues temporäres Projekt kopieren, Team/Profil anwenden und Quell-/Konfigurationsstände sichern. Keine vorherige Anwendung übernehmen.
2. Den nativen Client mit dokumentiertem Root-Auftrag und 900 Sekunden Laufzeitlimit starten. Umsetzung, Pflichtreview und Korrekturen ohne Weitergabe des unabhängigen Abnahmeskripts durchführen lassen.
3. Tatsächliche Kindmodelle, Kontextübertragung, Workflowzweige und Abschluss prüfen. CLI-Exit-Code null genügt nicht.
4. Unabhängige Browserabnahme über einen lokalen Loopback-Server ausführen, Desktop- und 360px-Mobilbilder prüfen und Befehle/Ergebnisse erhalten.
5. Eigene Nutzung jedes Threads, historische Kostenschätzungen, Ereignisse und Quellhashes erfassen. Anwendungsfehler, Koordinationsfehler und Prüfstandkorrekturen trennen.

Die neuesten Codex-Tests verwendeten Codex CLI 0.163.0, Python 3.14.3 und gecachtes Chromium mit Oberfläche unter Xvfb. Das BMad-Plugininventar meldete 6.13.0-next; der zuletzt aktive Build stammte aus einem globalen Skill ohne exaktes Versionsmanifest. Quellhashes bestätigten die Herkunft. Profilnamen bezeichnen gespeicherte Einstellungen, nicht den aktuellen Modellkatalog.

Die Aufgabe verlangte reines HTML/CSS/JavaScript, Name nach Trim mit mindestens zwei Zeichen, gültige E-Mail, Dauer 25/50 Minuten, Feldfehler und lokale Bestätigung mit erhaltenen Werten. Ohne Backend, Speicherung, Abhängigkeiten oder externe Anfragen. Alle abgeschlossenen Läufe nutzten dieselben zwölf Abnahmekategorien:

| Nr. | Unabhängige Abnahme |
|---|---|
| 1 | Struktur und zugängliche Feldbeschriftungen |
| 2 | Validierung des leeren Formulars |
| 3 | Zuordnung von Feldfehlern |
| 4 | Ungültiger Name und E-Mail |
| 5 | Namensvalidierung nach Trim |
| 6 | Bestätigung, erhaltene Werte und keine Speicherung |
| 7 | Dynamische Dauerübersicht |
| 8 | Tatsächliche Tastaturübermittlung und Fokus |
| 9 | Layout ohne horizontalen Überlauf bei 360px |
| 10 | Reduzierte Bewegung |
| 11 | Keine JavaScript-Fehler |
| 12 | Keine externen Anfragen |

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

Die USD-Schätzung wird je tatsächlichem Modell summiert: `(ungecachte Eingabe × Eingaberate + gecachte Eingabe × Cacherate + Ausgabe × Ausgaberate) / 1,000,000`. Historische Raten stehen unten; Reasoning wird nicht nochmals zur Ausgabe addiert.

## Deskriptive Statistik

Jede neueste Konfiguration hat **n = 1 abgeschlossenen Lauf**. Die Änderungen vergleichen diese Einzelbeobachtungen; die Basis steht nach `/`. Negative Werte bedeuten weniger Zeit, Kosten oder Token. Es sind keine geschätzten mittleren kausalen Effekte.

| Vergleich | Zeitänderung | Kostenänderung | Tokenänderung |
|---|---|---|---|
| BMad Basic / pnet Basic | +13.8% | +2.1% | +14.7% |
| BMad Plus / pnet Plus | +141.5% | +11.6% | +383.5% |
| BMad Basic / pnet Plus | -18.0% | -77.5% | +35.5% |

| Konfiguration | Cacheanteil der Eingabe | Threads inkl. Root |
|---|---|---|
| pnet Basic | 93.8% | 4 |
| pnet Plus | 85.0% | 4 |
| BMad Basic | 94.6% | 3 |
| BMad Plus | 96.6% | 4 |

BMad Basic benötigte in diesem Paar **77.5% weniger geschätzte Kosten** und **18.0% weniger Zeit** als pnet Plus bei einem vom Eigentümer als vergleichbar bewerteten Ergebnis. Gleichzeitig waren es 35.5% mehr Token. Unterschiedliche Modellraten und Cachewiederverwendung verhindern, dass Token Kosten ersetzen.

BMad Plus benötigte 2.41× die Zeit von pnet Plus bei 1.12× den Kosten. Die Ursache ist nicht bestimmt: Reasoning, Untersuchung, Reviews, Kontext und Cache unterschieden sich. Cacheanteil = gecachte / gesamte Eingabe; Threadzahlen enthalten Root und sind keine Spitzenparallelität.

Streuung innerhalb einer Konfiguration, Konfidenzintervalle, Signifikanz oder allgemeine Erfolgswahrscheinlichkeit lassen sich daraus nicht schätzen. Zusammengelegte Revisionen vermischen unterschiedliche Bedingungen. Zwölf Prüfungen an einer Aufgabe sind keine zwölf unabhängigen Aufgabenversuche.

## Historische abgeschlossene Läufe

| Konfiguration | Datum | Zeit | Token (Mio.) | Schätzung USD |
|---|---|---|---|---|
| Codex BMad Basic | 2026-10-16 | 6:26 | 2.882 | $0.0669 |
| Codex BMad Plus | 2026-10-16 | 12:40 | 3.945 | $0.1508 |
| Codex BMad Pro+ | 2026-10-16 | 5:13 | 1.651 | $0.7396 |
| Codex BMad Pro (rev. 1) | 2026-10-16 | 7:58 | 2.865 | $0.1338 |
| Codex BMad Plus (rev. 2) | 2026-10-16 | 9:52 | 3.587 | $0.2232 |
| Codex BMad Pro (rev. 2) | 2026-10-16 | 7:47 | 3.526 | $0.1438 |
| Codex BMad Plus (rev. 3) | 2026-10-16 | 8:45 | 4.448 | $0.1525 |
| Codex BMad Pro (rev. 3) | 2026-10-16 | 12:34 | 5.947 | $0.1876 |
| Antigravity Claude Plus (Sonnet) | 2026-10-17 | 3:19 | 2.308 | $1.5214 |
| Antigravity Claude Pro (Sonnet) | 2026-10-17 | 2:35 | 2.175 | $1.4302 |
| Antigravity Google Basic (Flash) | 2026-10-17 | 10:50 | 4.760 | $0.1878 |

Diese elf historischen und vier neuesten Zeilen beschreiben **15 unterschiedliche abgeschlossene Läufe**, jeweils mit 12/12. Revisionen bleiben getrennt: Prompts, Profile und Workflowquellen änderten sich. Es sind keine Wiederholungen derselben eingefrorenen Konfiguration. Claude Pro verwendete tatsächlich Sonnet; kein erfolgreicher Opus-Test ist belegt.

## Archivabdeckung und abgebrochene Versuche

| Kategorie erhaltener Datensätze | Unterschiedliche Datensätze |
|---|---|
| Abgeschlossen und unabhängig abgenommen | 15 |
| Stopp an unzutreffendem Workflow-Checkpoint | 2 |
| Quotenunterbrechung / Timeout | 1 |
| Sandbox blockiert | 1 |
| Startfehler vor Promptübermittlung | 1 |

21 `run.json`-Dateien entsprechen 20 unterschiedlichen erfassten Versuchen. Ein Sonnet-Lauf liegt mit identischen Run-/Usage-Hashes doppelt vor und zählt einmal. Im Opus-Timeout-Verzeichnis liegen veraltete Sonnet-Abnahme-/Kostendateien; sie belegen weder einen erfolgreichen Opus-Lauf noch dessen Kosten. Google-Quotennotizen ohne eigenen Laufdatensatz sind nicht enthalten.

Dies ist ein Archivinventar, kein vollständiges Versuchsprotokoll oder eine homogene Zuverlässigkeitsstichprobe. Die Haupttabellen wählen abgeschlossene Aufgaben; fehlende/gestoppte Versuche sind keine kostenlosen Erfolge. Die beiden Workflowstopps erzeugten keine Anwendung. Gelöschte ersetzte Materialien werden nicht rekonstruiert oder gezählt.

## Qualitätsbewertung

Nach qualitativer Einschätzung des Projekteigentümers ist **BMad Basic bei der
wahrgenommenen Ergebnisqualität mit pnet Plus vergleichbar**: ungefähr eine Profilstufe
Gewinn durch die Methodik. Das ist eine Expertenbeobachtung und Hypothese für weitere
Tests. BMad-Artefakte umfassen eine minimale Spezifikation und Review-Triage; identische
12/12 messen diesen Qualitätsunterschied nicht und belegen auch nicht seine Ursache.

UX, Vollständigkeit, Wartbarkeit, verbleibende Fehler und Prüfqualität sollten getrennt
von Zeit/Kosten bewertet werden, möglichst blind über mehrere Aufgaben und Wiederholungen.

Es gab weder ein blindes Bewertungsgremium noch ein angewandtes Punkteschema oder numerische subjektive Bewertungen. Nachträglich werden keine 1–10-Punkte oder Qualitätsprozente erfunden.

| Qualitätsdimension | Belegbare Aussage |
|---|---|
| Gefordertes Verhalten | 12/12 bei jedem abgeschlossenen Lauf; die Abnahme ordnet diese Ergebnisse nicht |
| Wahrgenommene Gesamtqualität | Eigentümerurteil: BMad Basic vergleichbar mit pnet Plus; keine belegte subjektive Rangfolge anderer Profile/Clients |
| Prozessvollständigkeit | BMad behielt minimale Spezifikation, Route und Triage; pnet durchlief PM → dev → reviewer → Korrekturen |
| Reviewnutzen | pnet fand Eingaberandfälle und mobiles Abschneiden; BMad dokumentierte Eingabe-, Bestätigungstext- und Live-Region-Befunde vor Korrekturen |
| Wartbarkeit und Restfehler | Keine blinde Vergleichswertung oder vollständige Fehlersuche; Screenreader-Ausgabe ungeprüft |

Reviewbefunde sind Zwischenbeobachtungen, keine endgültigen Abnahmefehler. Ihre Anzahl misst keine Qualität; das BMad-Rezept verlangte selbst eine Mindestanzahl.

## Beobachtungen zur Koordination

- Beide neuesten pnet-Roots starteten PM, dev und reviewer und nutzten denselben Entwickler für eine Korrektur. Alle Kinder erbten die ganze Unterhaltung. In diesen zwei Läufen wurden weder verlorene Aufträge noch blockierende Benutzerfragen beobachtet.
- Basic wiederholte Konfigurations-/Browsererkundung; Plus behielt einen wiederverwendbaren Test mit genauer Ausführung. Umgebungswiederholungen und doppelte Prüfungen verursachten Arbeit ohne belegten Anwendungsfehler.
- BMad Basic nutzte root → dev → Workflowreviewer. Neuester BMad Plus ergänzte einen begrenzten Architekturscan und absolvierte ein anwendbares Blind-Hunter-Review ohne falschen Freigabestopp.
- Tatsächliche Modelle: pnet Basic überall Luna/high; pnet Plus Root Luna/high, PM Sol/low, dev Luna/max, reviewer Sol/medium. BMad Basic überall Luna/high; BMad Plus Root Luna/high, dev/reviewer Luna/max, architect Sol/medium. Sol steht für `gpt-6.1-sol`, Luna für `gpt-6-luna`.
- Der workfloweigene BMad-Reviewer übernahm das eigenständige Reviewerprofil nicht automatisch. Direkte Übergabetexte sind in nativen Logs verschlüsselt; lesbare Antworten, Ziele, Metadaten und Verhalten belegen den Ablauf.

Optimierungskandidaten sind kompakter Auftragskontext, Wiederverwendung funktionierender Prüfbefehle, zweiggerechte Checkpointprüfung und explizites Modellmapping für Workflowkinder. Dies sind Vorschläge aus beobachteten Reibungen, keine gemessenen Einsparungen umgesetzter Änderungen.

## Grenzen und praktische Folgerungen

- Einzelne Läufe mit unterschiedlichen Prompts, Routen, Caches und Werkzeugen erlauben keine statistische Rangfolge von Profilen oder Anbietern.
- Kosten sind API-äquivalente Schätzungen zu historischen Sätzen, keine aktuellen Preise, Abonnementquoten oder Providerrechnungen. USD pro Million Eingabe-/Cache-/Ausgabe-Token: Luna 0.10/0.01/0.50; Sol 2/0.10/10; Astra 10/1/50; Sonnet 3/0.30/15; Flash 0.15/0.015/0.60.
- Erfolgreiches Rendern beweist keine Modellwahl zur Laufzeit. BMad-interne Reviewer nutzten nicht automatisch das eigenständige Reviewer-Profil. Tatsächliche Kindmodelle protokollieren.
- Der letzte Build verwendete einen global installierten BMad-Skill; die Pluginliste allein identifizierte den aktiven Workflow nicht. Ein reiner Pluginbetrieb ist nicht separat verifiziert.
- Codex lief in isolierten Profilen mit einer VM-spezifischen Vollzugriffsanpassung. Normaler Sandboxbetrieb und Screenreader-Ausgabe sind nicht belegt.
- pnet Basic war unter den vier jüngsten abgeschlossenen Läufen am schnellsten und günstigsten. Daraus folgen weder allgemeine Überlegenheit noch garantierte Vorteile höherer Profile.

Neue Vergleiche verwenden den [Versuchsplan](templates/experiment-plan.md) und die [Berichtsvorlage](templates/evaluation-report.md).

## Nächster kontrollierter Vergleich

Basic + BMad gegen Plus + pnet auf mehreren Aufgaben vergleichen: mindestens drei frische Läufe je eingefrorener Konfiguration/Aufgabe mit wechselnder Reihenfolge. Anforderungen, UX, Wartbarkeit, Restfehler und Prüfqualität getrennt blind bewerten; Aufgaben-/Abnahme-/Skill-/Profilhashes, Kontextpolitik und Raten einfrieren.

Alle Versuche und Eingriffe erhalten. Abschlussquote, Median/Spanne erfolgreicher Laufzeiten/Kosten und Gesamtkosten aller Versuche je abgeschlossener Aufgabe berichten. Eine konkrete Effektgröße kann mehr Wiederholungen erfordern; drei sind ein Startprotokoll, keine Powergarantie. Bis dahin bleibt „eine Profilstufe“ eine prüfbare Hypothese.
