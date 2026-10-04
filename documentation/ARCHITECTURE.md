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
