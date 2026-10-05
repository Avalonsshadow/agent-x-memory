# Validierung · Meilenstein 1

Datum: 2026-10-04. Alle Tests ausschließlich mit temporären Beispieldaten; keine persönlichen Inhalte importiert.

## Bestanden
- 28 Python-Tests: geschützte Datenendpunkte; CRUD/Persistenz nach Neuöffnung der Datenbank; Sitzungen nach Neuöffnung; CSRF und fremder Origin; Login-Begrenzung; Datums-/Quellen-/Linkvalidierung; Projektverknüpfung und Löschung; atomarer JSON-Restore; Importanweisungen bleiben Text; Logout; Integrations-/Jobstatus; Pfad-/Headerprüfung; Passwortwechsel; Secure-Cookie.
- `node --check app/web/app.js` und Python-Kompilierung.
- Frontend-Funktionstest im Node-VM-Testadapter gegen echtes Python/SQLite-Backend: neun Module, Anmeldung, Anlegen, Bearbeitungsformular, Datenabruf, Suche, HTML-Escaping, Quellenantworten, errechneter Aufgabenfortschritt, Export, ergänzender Import inklusive Wiederholung, Verbindungsfehler und Abmeldung. **DOM-Adapter, kein echter Browser.**
- Lokaler HTTP-Start erfolgreich. Beispielvorschau wird als eigenständige HTML-Datei aus denselben Oberflächenquellen generiert. Sie hat keinen Zugriffsschutz und speichert Änderungen nur bis zum Neuladen; deutlich markiert.

## Offen / blockiert
- Automatisierter Playwright-Browsertest liegt in `app/tests/browser.cjs`, konnte in dieser Umgebung nicht ausgeführt werden: Chromium fehlt; Download liefert kein gültiges Browserarchiv.
- Cloud-Browser blockiert lokale HTTP- und Datei-URLs. Kein Umgehen dieser Sperre.
- Visuelle Prüfung, echte iPhone-/Safari-Bedienung, Installation, Keyboard-/Screenreader-Prüfung und tatsächliche Offline-Darstellung sind daher **nicht bestätigt**.
- Persistenz nach Datenbank-Neuöffnung und erneuten Abrufen bestätigt; Browser-Neuladen nicht als echter Browsertest bestätigt.
- Noch kein HTTPS-Hosting, OAuth-End-to-End-Test, Scheduler oder Produktiv-Sicherheitsaudit. Die App ist für lokalen Einzelbenutzerbetrieb vorbereitet.

## Reproduktion

```bash
python -m unittest discover -s app/tests -v
node --check app/web/app.js
python app/tests/run_frontend.py
```

Optionale Browserprüfung mit installiertem Playwright/Chromium: Testserver starten und `node app/tests/browser.cjs` ausführen. Screenshots werden unter `AGENTX_TEST_ARTIFACTS` oder aktuellem Arbeitsverzeichnis erzeugt. Export und Demo-Screenshots niemals mit echten persönlichen Daten in Git einchecken.

## Ergänzender Import
Geprüft: Vorschau ohne Änderungen, atomarer Import in vorhandene Daten, Erhalt bearbeiteter vorhandener IDs mit Konfliktzählung, wiederholter Import ohne Duplikate, neue Projektverknüpfungen, ungültige Verknüpfungen und doppelte IDs mit vollständigem Rollback, Zugriffsschutz und CSRF für Vorschau/Import. Keine privaten Chatdaten als Testfixtures im Repository.

## Lokale Automatisierung
Neue Tests mit isolierten Datenbanken/Dateien: stabile Dateierkennung, automatischer Import, Backup vor Import, Wiederholung, Quarantäne fehlerhafter JSON; Update mit festem Commit, Codebackup, Prüfung gleicher Version, Offline-Fallback, ungültige Python-Syntax und Pfadtraversal ohne Codeverlust. Hintergrundthread mit echtem temporärem SQLite-Bestand gestartet, Import und Ende geprüft. Update-Download wird im Test simuliert. Kein Nachweis einer Windows-End-to-End-Installation oder dauerhafter Ausführung auf dem Nutzerrechner. Die neue Anzeige ist Teil des Frontend-Funktionstests; weitere Hintergrundaufgaben bleiben inaktiv.

## Dokumentausbau
Geprüft: authentifizierter Upload und Download, CSRF, unzulässige Dateinamen/-typen und Base64, Quellenpflicht, PDF-Seitenextraktion mit synthetischem PDF, DOCX-Absätze, Textzeilen, neueste Version in Volltexttreffern, Originalintegrität/SHA-256, Persistenz nach Datenbank-Neuöffnung, Löschung aller Versionen, atomarer Export/Restore einschließlich beschädigtem Hash, ergänzender Import samt Vorschau und Wiederholung. PDF-Test mit verfügbarer pypdf-Laufzeit; automatischer Paketdownload auf Windows bleibt eine Laufzeitprüfung. Frontend-Adapter prüft zusätzlich echtes Uploadformular, Suchtreffer mit Quellenstelle und Export der Originaldatei. Kein echter Browser-/iPhone-Test.

## Drive und laufende Updates
Fünf zusätzliche Tests: Zugriffsschutz/CSRF und Desktop-Konfigurationsvalidierung; OAuth-State/PKCE, Einmaligkeit, Ablauf und Scopeprüfung; Tokenpersistenz ohne Eintragsexport-Leak; Refresh und gewählte Dateien mit unveränderten/aktualisierten Originalversionen; Backups, API-Fehlerstatus, Paging und lokales Trennen; tatsächlicher periodischer Worker gegen simulierten Google-Transport; Update-Prüfung gegen simulierte Commitantwort, Shutdown und Backup/Exec-Aufruf. Bestehende 23 Tests und Frontend-Adapter weiterhin bestanden. Google-Antworten sind **simuliert**; OAuth-Projekt, echte Benutzeranmeldung, echte Drive-End-to-End-Synchronisation und Windows-Exec-Neustart sind noch nicht bestätigt. Diese Phase ist implementiert und isoliert geprüft, auf dem Nutzerrechner ohne ersten Starterlauf nicht aktiviert.

## Assistent, Kalender, Windows-Start (2026-10-04)
37 Python-Tests und Frontend-Adapter bestanden. Neue Testfälle: Quellen und Dokumentinhalte, reale Projektkennzahlen, offene Lernaufgaben, leere Antworten, Auth/CSRF/Origin, separater Kalender-OAuth-Scope, Tokenpersistenz ohne Exportleck, Ereignisänderungen und Absagen, Projektzuordnung, Export/Restore, zu viele Seiten ohne Teilübernahme, Quelloffset-Datum, keine Wiederanlage lokal gelöschter Termine, persistierte Tagesübersicht, Startup-Dateien/Runner mit Leerzeichen und Entfernung. Google-Antworten simuliert; Windows-Anmeldung, reales Kalender-OAuth und Browserlayout bleiben unbestätigt.

### Windows-Startkorrektur
Fehlender sys-Import im Windows-Startpfad korrigiert. Regressionstest führt den tatsächlichen Windows-Installationszweig aus dem AST von main mit isolierten Plattform-/Prozess-Doubles aus. Kein Windows-Rechnerzugriff und keine echte Anmeldung behauptet.

## Gemeinsamer Kalender und manuelle Uhrzeiten
Frontend-Adapter gegen echten HTTP/SQLite-Server bestätigt: gemeinsame Health-/Lounge-Termine, Quellenherkunft, HTML-Escaping, Monats-/Wochenbereich mit Montagbeginn, Monatswechsel ab 31. Januar, ganztägiges exklusives Enddatum, Bereichsfilter, Dialogöffnung/-schließen, Zeitformular-Serialisierung, Speicherung und Zeit-Roundtrip sowie Zurückweisung von fehlendem Datum und Ende vor Beginn. Keine echte Browser-/iPhone-Layoutprüfung. Kalender nutzt gespeicherte Termine aller Module, archivierte Termine ausgeblendet. Manuelle Start-/Endzeiten werden mit UTC-Offset als ISO im Eintragsinhalt gespeichert; UI stellt lokale Zeitfelder bereit. Bestehende Daten benötigen keine Migration. Kein Schreiben nach Google.

## LCARS Cockpit · 2026-10-04
Gewählte Variante 1 umgesetzt. JavaScript-Syntaxprüfung und isolierter Frontend/API-Test bestanden: Anmeldung, neun Module, Anlegen/Bearbeiten/Neuladen, Suche, Quellen, Export, Kalender und Uhrzeiten; zusätzlich Cockpit-Bereiche und maskierte bereichsübergreifende Termine geprüft. Responsive CSS für Desktop und kleine Displays implementiert. Erneute echte Browser-/Screenshotprüfung in dieser Phase blockiert: Chromium fehlt, Download liefert ungültiges ZIP. Daher keine Behauptung einer abgeschlossenen visuellen iPhone-Prüfung. Veröffentlichte Webdateien per GitHub wieder abgerufen und vollständig mit lokalem Inhalt verglichen.

## Referenzgetreues Cockpit · zweite Prüfung 2026-10-04
Die zuvor blockierte visuelle Prüfung ist jetzt möglich: Chrome Headless Shell separat bereitgestellt. Browser-Test bei 1440×1000 und 390×844 bestanden. Screenshots beider Ansichten kontrolliert; mobile Navigationsüberlagerung korrigiert und erneut geprüft. Durchgehender orangefarbener Rahmen, schlanke SVG-Navigation, drei echte Kennzahlen, Heute/Fokus nebeneinander, rechte Wochenleiste mit sieben Tagen, Projektkarten, Schnellzugriff und datenbasierte Verbindungsstatusleiste. Keine Referenz-Beispieldaten in Nutzerdaten übernommen.

40 Python-Tests bestanden, Frontend/API-Test bestanden. Echter Browser prüft Anmeldung, neun Module, Anlegen/Bearbeiten/Neuladen, Suche, maskierte Inhalte, Fortschritt, Quellenantwort, Export, Wochenleisten-Kalenderöffnung, Dokumentdialog, mobile Navigation und Abmeldung. Kein horizontaler Überlauf bei 390 px. Physisches iPhone/Safari bleibt separat ungeprüft. Änderungen vor GitHub-Bereitstellung geprüft.

## Prioritäten & farbige Module · 2026-10-04
43 Python-Tests einschließlich Migration, gültigen/ungültigen Prioritäten, Bestandserhalt, Speicherung, Export/Restore und alten Bearbeitungsaufrufen bestanden. Frontend/API-Suite und echter Headless-Browser bei 1440×1000 / 390×844 bestanden. Browser prüft neun verschiedene berechnete Iconfarben, sichtbare Hoch-Priorität, Auswahl Mittel im Editor und erneute Anzeige nach Neuladen, sechs Modulübersichten, Bibliothek-/Lounge-/Health-/Laboratory-Screenshots, mobile Navigation und fehlenden horizontalen Überlauf. Desktop und mobile Screenshots visuell geprüft; enge Kartenumbrüche korrigiert. Testdaten ausschließlich isolierte temporäre SQLite-Dateien. Physisches Safari-iPhone weiterhin separat ungeprüft.

## Reference alignment · 2026-10-05

Aligned the implemented cockpit with the supplied navy/orange reference: saturated cyan controls, orange continuous frame, distinct module icon colors, blue project progress, compact desktop twin panels and responsive mobile stacking. Added explicit design version `Cockpit 2026.10.05` and versioned stylesheet/script URLs to distinguish stale installations and refresh cached assets. Connection dots reflect real offline/connected/error states; no demonstration figures or fake connections enter personal storage.

Validation: all 43 Python tests passed; frontend functional checks passed; headless Chromium passed login, nine module colors, exact cyan/orange CSS values, desktop twin columns, versioned stylesheet, edit/reload, search, export, source answers, logout and mobile overflow/navigation. Visual inspection used the real rendered app at desktop and 390px mobile widths with a disposable fixture database. The separately generated image is only a design reference, not verification evidence. Physical iPhone and Patrick's running Windows installation were not remotely verified.

## Priority editor · 2026-10-05

Priority is shown separately from work status for every record kind, with explicit text and icons: ⇈ Hoch, ↑ Mittel, ↓ Niedrig, ○ Nicht festgelegt. Removed ambiguous “Priorität offen”. The editor offers both an accessible select and four synchronized shortcut buttons with aria-pressed; importance remains user-assigned and durable in SQLite. Existing unset values are not inferred from open/active status.

Validation: three priority persistence/export/restore/migration tests passed; frontend functional checks and Chromium desktop/mobile suite passed. Browser coverage selects high/medium/low, clears priority, verifies select/button synchronization and reopens a saved medium-priority record after reload. Both priority and status remain editable independently. No physical Windows/iPhone verification claimed.

## Work organization · 2026-10-05

Tasks and projects are grouped independently by blocked, active, open, done and archived status; done/archive groups collapse with visible counts. Mixed overviews first separate record kinds. Within work groups, importance then due date and title determine order. Source evidence is explicitly labelled “Angabe” and never treated as completion status. Events are grouped into today/ongoing, future, undated, past, completed and archive; each group is date/time sorted. Past, completed and archived events collapse. Ongoing multi-day events use their actual end date. Card borders indicate work or event group in addition to text. The ideas bulb has a yellow interior with the existing module outline.

Frontend checks cover confirmed-but-open tasks, separate completed records, empty-date events and past/future dates. Chromium checks task groups, expand/collapse, today/future events, the yellow bulb and normal desktop/mobile CRUD/search/export flows. Existing data is reorganized for display without changing stored status, priority or evidence.

## Seven main areas · 2026-10-05

Frontend and Chromium checks cover seven main links and seven distinct icon colors, retained legacy routes, Laboratory entry from the project workspace, a shared task view containing tasks from all areas, assistant Crew access with four explicit perspectives, editor save/reload, export, source answers and mobile navigation/overflow. All persistent backend identifiers and records remain unchanged; no migration or duplicate data is introduced. Browser tests use disposable example data, not personal records.
