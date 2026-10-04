# Agent X 2.0

Erster funktionierender Meilenstein einer privaten Kommandozentrale. Neun Module, Projekte/Aufgaben/Notizen, Suche, Quellen, SQLite-Speicherung und serverseitiger Zugriffsschutz.

Die Altversion befindet sich unverändert in den bisherigen Root-Dateien. **Die neue App ist `app/`; Root-`index.html` bleibt das historische Dashboard.**

## Start auf deinem Computer
Voraussetzung: Python 3.12 oder neuer. Der Kern läuft ohne zusätzliche Python-Pakete. Für PDF-Volltext versucht der automatische Starter, die freie Bibliothek `pypdf==6.19.0` lokal zu installieren; ohne sie bleiben PDF-Originale speicherbar.

1. Diesen Entwicklungszweig herunterladen/auschecken.
2. Im Repository-Ordner ein Terminal öffnen.
3. Ein persönliches Passwort einrichten (mindestens 12 Zeichen):

```bash
python app/server.py init
```

4. App starten:

```bash
python app/server.py serve
```

5. `http://127.0.0.1:8765` im Browser öffnen und anmelden.

Daten werden standardmäßig im Benutzerverzeichnis unter `.local/share/agent-x-2/data.sqlite3` gespeichert, **außerhalb** des Repositorys. Auch nach Neuladen und Neustart erhalten. Für andere Datenorte `--data /absoluter/privater/pfad/data.sqlite3` bei jedem Befehl verwenden.
Windows: falls `python` nicht verfügbar, `py -3` verwenden. Mac/Linux: gegebenenfalls `python3`.

## Backup und Wiederherstellung
In Systems & Security JSON exportieren; private Exportdateien sicher verwahren. „Einträge ergänzen“ importiert JSON-Pakete auch in den bestehenden Datenbestand: Vorschau, neue Einträge, vorhandene IDs überspringen. Abweichender Inhalt derselben ID wird als Konflikt gezählt und nicht übernommen. Keine bestehenden Einträge werden überschrieben. „Backup einlesen“ bleibt auf einen leeren Datenbestand beschränkt. Eintragslöschungen sind endgültig; vorher bei Bedarf exportieren.

Komplette SQLite-Sicherung (enthält Zugangskonfiguration, privat aufbewahren):

```bash
python app/server.py backup --output /privater/pfad/agent-x-backup.sqlite3
```

Zum Wiederherstellen des kompletten SQLite-Backups Server stoppen, Backup an privaten Datenpfad kopieren und Server mit diesem `--data` starten. Bei öffentlichem Verlust der Datei Passwort wechseln (`init`) und bestehende Sitzungen damit invalidieren.

## iPhone und Netzbetrieb
Ein Server auf deinem Desktop ist nur erreichbar, solange er läuft. Für iPhone und dauerhaft geräteübergreifenden Betrieb wird eine private HTTPS-Laufzeit benötigt; sie wurde nicht eingerichtet oder öffentlich veröffentlicht.
Netzbetrieb erfordert einen HTTPS-Reverse-Proxy, exakten Ursprung und geschützten Backendport:

```bash
python app/server.py serve --host 0.0.0.0 --origin https://DEIN-PRIVATER-HOST
```

Das Beispiel konfiguriert **kein TLS**: HTTPS muss durch den Proxy bereitgestellt werden. Backendport nicht direkt im Internet freigeben. Vor persönlicher Online-Nutzung Hosting-/Sicherheitsprüfung abschließen. Bei HTTPS: iPhone Safari → Teilen → Zum Home-Bildschirm. Die Installation auf einem echten iPhone ist noch nicht geprüft.

## Tests (isolierte Datenbanken)

```bash
python -m unittest discover -s app/tests -v
node --check app/web/app.js
python app/tests/run_frontend.py
```

Optionaler Browser-Test (Playwright + Chromium in deiner Entwicklungsumgebung installieren):

```bash
python app/tests/preview_server.py
# separates Terminal:
node app/tests/browser.cjs
```

`preview_server.py` ist ausschließlich eine Wegwerf-Testumgebung mit öffentlichen Beispieldaten und einem Testpasswort. Nicht für persönliche Daten verwenden. Ausgaben siehe [TEST_RESULTS.md](documentation/TEST_RESULTS.md).

## Ehrlicher Funktionsstand
Fachmodule erlauben bereits manuelle Einträge, sind aber noch keine Finanzrechner, Health-Diagramme oder strukturierten Auditwerkzeuge. Dokument-Upload, Originalversionen und Volltextsuche sind verfügbar. Google-/GitHub-Verbindungen in der App nicht eingerichtet; Der lokale Importworker ist beim automatischen Start aktiv; weitere Hintergrundaufgaben sind inaktiv. Rollen sind Perspektiven, keine separaten KI-Agenten. Fragen werden regelbasiert aus gespeicherten Einträgen beantwortet.

[Bestandsprüfung & Architektur](documentation/ARCHITECTURE.md) · [Anforderungen & weitere Meilensteine](documentation/REQUIREMENTS.md)

## Update einer vorhandenen Installation
Server mit Strg+C stoppen. Den Ordner `app/` durch die neue Version ersetzen, Server wieder starten (`py app/server.py serve` unter Windows) und Browser neu laden. Kein erneutes `init` nötig. Standard-Datenbank liegt außerhalb dieses Ordners. Bei einem eigenen `--data` denselben Pfad weiterverwenden. Vor Updates JSON exportieren oder SQLite sichern. Private Importpakete gehören nicht in dieses öffentliche Repository.

## Automatischer Start und Updates

Einmal diese Version vollständig entpacken (auch die beiden Starter im Root sind nötig). Vorhandenen Server mit Strg+C stoppen. Danach unter Windows **Agent-X-starten.cmd** doppelklicken; alternativ `py start_agent_x.py`. Der Starter prüft bei jedem Start den autorisierten Entwicklungszweig `agent-x-2/milestone-1` dieses Repositorys und übernimmt `app/` aus einem festen GitHub-Commit. Er ersetzt keine Root-Dateien und aktualisiert sich selbst nicht. HTTPS-Download, Größenbegrenzung, Pfadprüfung und Python-Syntaxprüfung; bei Download-/Validierungsfehler läuft die vorhandene Version weiter. Lokale Änderungen in `app/` werden dabei ersetzt und als Codebackup erhalten. Codeupdates erfolgen beim Start, nicht während einer laufenden Sitzung. Der Starter nutzt den Standard-Datenpfad und Port 8765. Für eigene Datenpfade weiterhin die manuelle CLI verwenden.

Codebackups: `.local/share/agent-x-2/code-backups/` im Benutzerordner. SQLite-Sicherung vor Serverstart und vor neuen automatischen Importen: `.local/share/agent-x-2/backups/`. Sicherungen enthalten private Daten, bleiben auf dem Rechner und werden nicht automatisch gelöscht. Zur Wiederherstellung Server stoppen und das benötigte App-Codebackup zurückkopieren; bei Bedarf SQLite wie oben wiederherstellen. Liegen private Daten in `app/`, wird das Codeupdate vorsorglich nicht angewandt.

## Automatischer Importordner

Der Starter aktiviert `--automate`. Neue JSON-Pakete nach `.local/share/agent-x-2/imports/inbox/` im Benutzerordner speichern. Unter Windows standardmäßig `%USERPROFILE%\.local\share\agent-x-2\imports\inbox`. Alle 15 Sekunden Prüfung; zwei unveränderte Prüfungen vor dem Import. Erfolgreiche Pakete wandern nach `processed`, fehlerhafte nach `failed`. Wiederholungen werden anhand bestehender IDs übersprungen; manuelle Korrekturen bleiben erhalten. Pakete bleiben reine Daten, Anweisungen darin werden nicht ausgeführt. Letzter Abruf/Import und Fehler sind in Systems & Security sichtbar.

Dies ist **keine direkte ChatGPT-Synchronisation**. Chatwissen muss weiterhin als zulässiges Importpaket bereitgestellt werden. Google-Verbindungen sowie Mail-, Fristen- und Turnier-Scheduler bleiben nicht eingerichtet. Worker nur aktiv, solange der lokale Server läuft. Windows-Autostart und Onlinehosting sind nicht eingerichtet. Die Windows-End-to-End-Prüfung auf deinem Rechner steht aus.

## Dokumente und Volltext

In der Bibliothek „Dokument hochladen“ wählen. PDF, DOCX, UTF-8-Text, Markdown, CSV und JSON: maximal 5 MB je Datei, insgesamt 20 MB Originale und 20 MB Textindex. Quellenangabe und Datum sind Pflicht; Projektverknüpfungen sind optional. Originale liegen als BLOBs in der privaten SQLite-Datenbank. Neue Versionen bewahren alte Originale; die Suche durchsucht die neueste Version mit PDF-Seite, DOCX-Absatz oder Textzeile. Keine automatische Norminterpretation und keine Ausführung von Dokumentanweisungen.

PDF-Extraktion läuft lokal in einem zeitlich begrenzten Unterprozess. Maximal 200 PDF-Seiten und 500.000 Textzeichen pro Datei. DOCX verarbeitet Absatztext; eingebettete Dateien und Bilder werden nicht indexiert. Scans benötigen noch nicht eingerichtete OCR. Extraktionsfehler werden angezeigt; das Original bleibt erhalten. Nach Beheben der PDF-Abhängigkeit eine neue Version hochladen, um die Extraktion erneut auszuführen.

JSON-Export enthält Originale (Base64) und Textindizes; Import/Restore unterstützt sie atomar, ohne vorhandene Versionen zu überschreiben. Importierte Indizes sind bereitgestellter Dokumentinhalt, keine unabhängig bestätigten Fakten. Die Importgrenze beträgt 50 MB; komplette SQLite-Backups sichern auch größere Bestände. Das Löschen eines Dokumenteintrags entfernt alle zugehörigen Originalversionen aus der aktiven Datenbank. Bestehende Backups und exportierte Kopien bleiben bestehen und müssen bei gewünschter vollständiger Entfernung separat gelöscht werden. Persönliche und berufliche Originale niemals in Git ablegen.

## Google Drive (lokaler Desktop)

In Systems & Security die Desktop-OAuth-JSON-Datei einlesen, mit Google verbinden, Dateien auswählen und einmal „Jetzt abrufen“ wählen. Danach synchronisiert der automatische Starter ausgewählte Dateien alle 15 Minuten. PDF/DOCX/Text wie beim manuellen Upload; Google Docs als Text, Sheets als CSV (nur erstes Tabellenblatt), Slides als PDF. Neue Inhalte erzeugen Originalversionen; unveränderte Dateien werden übersprungen. Fehler und letzter erfolgreicher Abruf sind sichtbar. Lokale Änderungen an Eintragsmetadaten bleiben erhalten. Löschung einer lokalen verknüpften Dokumentkarte beendet deren Synchronisation beim nächsten Lauf.

Einmalige externe Einrichtung: eigenes Google-Cloud-Projekt, Drive API aktivieren, OAuth-Zustimmungsbildschirm für private Tests konfigurieren, eigene Google-E-Mail als Testnutzer hinzufügen, OAuth-Client **Desktop-App** erstellen und JSON herunterladen. Es werden keine kostenpflichtigen Dienste eingerichtet. Die App verlangt ausschließlich `drive.readonly`: Google erlaubt damit Lesen aller Drive-Dateien; Agent X lädt nur die ausgewählten Dateien (maximal 50). Google kann bei Test-Apps Anmeldung/Refresh-Tokens zeitlich begrenzen. Die Anmeldung erfolgt im Browser mit State und PKCE über Loopback; keine ChatGPT-Zugriffstoken werden übernommen. Nur am lokalen Desktop erreichbar; gehostete/iPhone-Anmeldung ist noch nicht implementiert.

OAuth-Konfiguration und Tokens stehen in `google-drive-private.json` neben der privaten Datenbank, nicht in Git, JSON-Eintragsexport oder Browserantworten. Datei wird mit eingeschränkten Dateimodi angelegt, aber **nicht verschlüsselt**; Windows-Benutzerordner/ACLs und Geräteschutz bleiben erforderlich. Vollständige Sicherung benötigt zusätzlich diese Datei; exportierte Originale benötigen die Verbindung nicht. „Verbindung lokal entfernen“ löscht diese Konfiguration und Tokens, bewahrt importierte Dokumente und widerruft Google-Berechtigungen nicht automatisch. Widerruf bei Google unter den Kontoberechtigungen möglich.

## Updates ohne manuelles Terminal-Neustarten

Nach einmaligem Laden dieser Phase prüft der automatische Starter nun auch im laufenden Server alle 15 Minuten den festen Entwicklungszweig. Bei neuer Version: HTTP-Server geordnet stoppen, aktive Anfragen/Importe/Drive-Abrufe abschließen, SQLite sichern, validiertes App-Update mit Codebackup einspielen, Server mit gleichen Argumenten neu starten. Bei ungültigem Download wird die vorhandene App wieder gestartet. Der Browser erkennt eine neue Revision alle 30 Sekunden und lädt nach Ende offener Dialoge neu. Manuelle Updateprüfung ist in Systems & Security möglich. Betrieb wird kurz unterbrochen; kein Zero-Downtime-Hosting.

Eine bereits laufende **ältere** App besitzt diesen Updateworker noch nicht. Sie muss diese Phase einmal über den bisherigen Starter laden. Das lässt sich aus der Entwicklungsumgebung ohne Fernzugriff auf den Rechner nicht nachträglich einschalten. Windows-Prozessneustart und echte Google-Anmeldung sind erst nach lokaler Einrichtung vollständig prüfbar.
