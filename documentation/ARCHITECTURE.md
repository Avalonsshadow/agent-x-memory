# Agent X 2.0 · technische Entscheidungen

## Bestandsprüfung (2026-10-04)
Basis: Commit `ef94572f5ee4b10a64b5e431ef1b17a164a749b0`, Branch `main`.
Das Repository ist öffentlich. Der bisherige Stand bleibt unverändert erhalten.
- `agent_x.py`: ausschließlich Platzhalter; kein ausführbarer Agent.
- `index.html`, `main_dashboard_optimized.html`, `docs/index.html`: statische LCARS-Oberflächen mit Apps-Script-Endpunkten. Keine eigene authentifizierte CRUD-App.
- `index.html:percentFromCounts`: Prozent aus `fileCount % 87 + 8`, begrenzt auf 20–95. Keine fachliche Aussage.
- `Code.gs`: Sheet-basierte Daten-/KPI-Verarbeitung. Nicht in der neuen Version aktiviert; vorhandene Deployments und Berechtigungen wurden nicht geändert.
- Memory-Dateien, `memory_backup.py`, `conversation_importer.py`, Uploadskripte: historischer Bestand, keine automatisch bestätigten aktuellen Fakten. Importer leitet bei Textdateien Sprecher aus Zeilenposition ab; kein verlässlicher automatischer Import.
- Übernommen: neun Modulideen, LCARS-Farbrichtung, Rollen als Perspektiven, Grundidee Quelle/Memory/Backup. Keine privaten Altinhalte oder alten Endpunkt-URLs in die neue App übernommen.
- Altdateien und alte Anzeigen bleiben als historische Version erhalten; ausschließlich `app/` ist Agent X 2.0. Das Root-Dashboard wurde absichtlich nicht durch ungeschützte persönliche Daten ersetzt.

## Architekturentscheidung ADR-001
Einzelbenutzer-App: Python 3.12 Standardbibliothek, SQLite, buildlose HTML/CSS/JS-Oberfläche.
Keine kostenpflichtigen Dienste, keine npm-Abhängigkeit für den Appbetrieb. Kein Zugriff auf Mercedes-Benz-Systeme.
Der Backendprozess wird lokal gebunden. Netzbetrieb nur explizit hinter HTTPS-Reverse-Proxy mit festem Ursprung; Hosting nicht eingerichtet.
Das ist ein funktionsfähiger lokaler Meilenstein, kein geprüfter Internet-Produktivbetrieb.

Warum: Der Ausgangsstand hat keinen funktionsfähigen Backendkern. SQLite ermöglicht nachvollziehbare dauerhafte Speicherung, atomare Änderungen und einfache Sicherungen ohne externe Einrichtung. Die kleine Oberfläche bleibt leicht wartbar. Eine spätere Hostingentscheidung kann den Datenspeicher und Transport ersetzen, ohne Modulkonzept und Datenmodell zu ändern.

## Datenmodell ADR-002
Einträge: Projekt, Aufgabe, Notiz, Fakt, Dokumentverweis, Termin. Jeder Eintrag hat ID, Modul, Titel, Inhalt, Status, Frist, Projektverknüpfung, Quelle, Verlässlichkeitsstatus, Standdatum, Tags, Original-Link und technische Zeitstempel.
Projekte können beliebige Einträge bündeln. Beim Löschen eines Projekts bleiben zugeordnete Einträge ohne Projekt erhalten. Projektfortschritt = erledigte Aufgaben / alle zugeordneten nicht archivierten Aufgaben. Ohne Aufgaben keine Prozentzahl.
Globale Suche durchsucht Titel, Inhalt, Tags, Quelle und Typ. Dokumentverweise sind editierbar und durchsuchbar; Original-URL im Bearbeitungsdialog. Upload und Volltextimport noch nicht implementiert.
JSON-Export enthält Daten und Schema-Version, keine Passwörter oder Sitzungstoken. Wiederherstellung nur in leere Datenbank, atomar und mit validierten IDs/Querverweisen.
Aktivitätsprotokoll enthält Aktionen, IDs und Zeitstempel, keine früheren Inhalte. Kein unveränderliches Compliance-Protokoll.

## Zugriff ADR-003
Passwort wird ausschließlich lokal im Terminal angelegt, scrypt mit zufälligem Salt. Keine offenen HTTP-Setup-Endpunkte und kein Standardpasswort für echte Daten.
12 Stunden Sitzung, zufälliges Cookie, HttpOnly, SameSite Strict, Secure bei HTTPS. SQLite speichert nur Session-Hash. Logout/Passwortwechsel invalidieren Sitzungen.
Alle Datenendpunkte geschützt, schreibende Endpunkte CSRF-geprüft. Fremde Origin bei Änderungen abgelehnt. Login begrenzt (5 Versuche/15 Minuten/IP, im Prozessspeicher). Kein MFA und kein Passwort-Recovery-Service.
Keine HTML-Ausführung aus gespeicherten Inhalten; HTTP(S)-Original-URLs validiert. CSP, Frame-Schutz und no-store für API. Service Worker speichert nur öffentliche statische Assets, keine privaten Daten; Offline-Änderungen werden nicht unterstützt.
Datenträgerverschlüsselung und sichere OS-Benutzerkonten sind Aufgabe der Laufzeitumgebung. SQLite-Datei liegt außerhalb des Repositorys mit eingeschränkten Dateirechten.
Für Internetbetrieb: HTTPS, Firewall, persistentes Volume, Zugriff nur via Proxy, sorgfältige Proxy/IP-Konfiguration, Backup/Restore-Prüfung und zusätzliche Sicherheitsprüfung vor persönlicher Nutzung.

## Verbindungen ADR-004
Entwicklungszugriff: GitHub-Lese-/Schreibberechtigungen bestätigt; harmlose Leseaufrufe für Gmail, Google Kalender, Google Drive erfolgreich (2026-10-04). Keine E-Mail-/Kalender-/Dokumentinhalte in das Repository kopiert.
Appzugriff: Google Drive, Gmail, Google Kalender und GitHub **nicht eingerichtet**. Kein OAuth-Code, keine Übernahme von ChatGPT-Tokens. Anzeige letzter Erfolg: keiner; Fehler: keiner, weil noch kein Abruf möglich.
Nächster Meilenstein: eigenes serverseitiges OAuth (Authorization Code + PKCE/state), minimale Lesescopes, verschlüsselte Refresh-Tokens außerhalb des Repositorys, Status/Fehler pro Provider; Browser erhält keine Provider-Geheimnisse. Google Cloud-Projekt und OAuth-Zustimmung müssen vom Eigentümer eingerichtet werden. Anleitungen erst passend zur gewählten Laufzeit konkretisieren.
Scheduler-/Queue-/Benachrichtigungs-Laufzeit fehlt. Hintergrundaufgaben sind **inaktiv**, nicht durch ChatGPT-Automationen simuliert.

## Assistent ADR-005
Version 1 enthält regelbasierte Datenabfragen und Textsuche mit Quellen; keine generative KI und keine getrennten Agenten. Vince, Data, Picard, Treu sind transparent als Perspektiven dargestellt.
Importierte Anweisungen bleiben Text. Es gibt keinen Tool-Ausführungsweg aus Dokumentinhalten. Berufliche Kommunikation und Auditbewertungen sind nicht implementiert.

## Persönliche Inhalte
Kein vorbefülltes persönliches Profil und keine Gesundheits-/Finanzdaten im öffentlichen Code. Private Startdaten ausschließlich separat exportieren und nach Anmeldung importieren. Historische Angaben nicht automatisch übernehmen; Ausbildung nicht als Zertifizierung darstellen.

## Entscheidung: lokale Update-/Importautomatisierung (04.10.2026)
Fester Starter prüft den bereits autorisierten GitHub-Entwicklungszweig beim Start. Download wird an einen Commit gebunden; Anwendungscode per Staging/Umbenennung ersetzt, vorher lokales Codebackup. Vertrauensgrenze: Schreibzugriff auf den freigegebenen Entwicklungszweig bedeutet auslieferbaren Code. Keine beliebigen Update-URLs, keine Geheimnisse in GitHub. Laufender Server auf Standardport blockiert einen zweiten Starter. Syntax-/Archivvalidierung ist kein vollständiger Sicherheitsnachweis. Root-Starter bleibt stabil und wird nicht aus dem Archiv ersetzt.
ImportWorker verarbeitet ausschließlich lokale JSON-Datenpakete aus einem privaten Inbox-Ordner, mit stabiler Dateigröße/Zeitstempel über zwei Scans, atomarem additiven DB-Import, SQLite-Backup, Quellenstatus und Fehlerquarantäne. Keine Befehlsausführung aus Importen. Zugriffsschutz gilt für Statusendpunkte; kein privater API-Cache. Aktivierung explizit per --automate oder Starter. Alle anderen Scheduler weiter inaktiv.

## Dokumente (zweiter Ausbau, 2026-10-04)
Additive SQLite-Tabelle `documents`: versionierte Original-BLOBs, SHA-256, Extraktionsstatus und Textstellen; Verknüpfung mit bestehenden Dokumenteinträgen. Bestehende Eintragsdaten bleiben erhalten. Bewusst lokale Speicherung statt externer Dateidienste. Downloads nur nach Anmeldung, als Attachment und ohne Cache. Volltextsuche durchsucht neueste Versionen und zeigt Fundstellen; kein externer KI-Aufruf. PDF über optionales pypdf im begrenzten Unterprozess; DOCX über begrenztes ZIP/XML; UTF-8-Texte zeilenweise. SQLite- und JSON-Backups enthalten Originalversionen. Keine OCR, Google-OAuth oder gehostete Laufzeit in diesem Ausbau.

## Drive und laufende Updates (2026-10-04)
Desktop-OAuth Authorization Code mit PKCE/State, 10-Minuten-State und gültiger ursprünglicher Sitzung. Fest vorgegebene Google-Endpunkte, Backend-Tokenrefresh, ausschließlich Drive-Lesezugriff. Lokale private Konfiguration separat von Record-Export; SQLite Drive-Verknüpfungen für Änderungsvergleich. Hintergrundworker 15 Minuten, Originalversionen vor Übernahme gesichert. Kein OAuth-Cloud-Projekt automatisch verfügbar. Updater im laufenden Server verwendet bisherigen vertrauensgebundenen Root-Updater erst nach geordnetem Shutdown und Backup; danach gleicher Serverprozessaufruf. Initiale ältere Laufzeit benötigt einen ersten Starterlauf. Kein Nachweis von Windows-/Google-End-to-End vorhanden.

## Assistent / Kalender / Windows-Start (2026-10-04)
Serverseitige deterministische Antwort-API, keine LLM-Aufrufe oder Toolausführung aus Dokumenten. Latest-Version-Textfundstellen mit Originaldownload und Provenienz. Kalender übernimmt Drive-PKCE-Protokoll über instanzbezogenen Scope, getrennte private OAuth-Datei. Begrenzter vollständiger Abruffensterabgleich, Seiten vollständig vor Übernahme prüfen, pro Kalender atomarer SQLite-Import und Backup. Kalenderlinks getrennt vom portablen Eintragsexport, stabile IDs; lokale Projektverknüpfung bleibt. Tagesübersicht regenerierbar, privater SQLite-Cache. Windows-Benutzerautostart via VBS und privatem Python-Runner, exklusiver Dateilock, kein Administrator/Remotezugriff. Automatische Installation ist durch Benutzerauftrag autorisiert; Entfernung wird beim folgenden Start respektiert. Status installed ist kein Windows-End-to-End-Nachweis. Details und Grenzen: ASSISTANT_CALENDAR_RELEASE.md.

## Prioritäten und Modulgestaltung · 2026-10-04
Records erhalten die optionale SQLite-Spalte priority mit Werten leer/high/medium/low. Idempotente ALTER-TABLE-Migration erhält vorhandene IDs und Inhalte; ältere Importe bleiben kompatibel. PUT ohne Priorität erhält den vorhandenen Wert, expliziter Leerwert entfernt die Priorität. Export/Restore enthalten den Wert. Keine automatisch erfundenen Prioritäten. Fokus sortiert erst nach gesetzter Priorität, dann Blockade und Datum. Modulfarben und SVG-Icons sind statische lokale UI-Assets; keine externe Icon-Bibliothek oder CDN-Abhängigkeit.
