# Agent X 2.0

Erster funktionierender Meilenstein einer privaten Kommandozentrale. Neun Module, Projekte/Aufgaben/Notizen, Suche, Quellen, SQLite-Speicherung und serverseitiger Zugriffsschutz.

Die Altversion befindet sich unverändert in den bisherigen Root-Dateien. **Die neue App ist `app/`; Root-`index.html` bleibt das historische Dashboard.**

## Start auf deinem Computer
Voraussetzung: Python 3.12 oder neuer. Keine zusätzlichen Python-Pakete erforderlich.

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
Fachmodule erlauben bereits manuelle Einträge, sind aber noch keine Finanzrechner, Health-Diagramme oder strukturierten Auditwerkzeuge. Dokumente aktuell als Quellenverweise. Google-/GitHub-Verbindungen in der App nicht eingerichtet; Hintergrundaufgaben inaktiv. Rollen sind Perspektiven, keine separaten KI-Agenten. Fragen werden regelbasiert aus gespeicherten Einträgen beantwortet.

[Bestandsprüfung & Architektur](documentation/ARCHITECTURE.md) · [Anforderungen & weitere Meilensteine](documentation/REQUIREMENTS.md)

## Update einer vorhandenen Installation
Server mit Strg+C stoppen. Den Ordner `app/` durch die neue Version ersetzen, Server wieder starten (`py app/server.py serve` unter Windows) und Browser neu laden. Kein erneutes `init` nötig. Standard-Datenbank liegt außerhalb dieses Ordners. Bei einem eigenen `--data` denselben Pfad weiterverwenden. Vor Updates JSON exportieren oder SQLite sichern. Private Importpakete gehören nicht in dieses öffentliche Repository.

## Automatischer Start und Updates

Einmal diese Version vollständig entpacken (auch die beiden Starter im Root sind nötig). Vorhandenen Server mit Strg+C stoppen. Danach unter Windows **Agent-X-starten.cmd** doppelklicken; alternativ `py start_agent_x.py`. Der Starter prüft bei jedem Start den autorisierten Entwicklungszweig `agent-x-2/milestone-1` dieses Repositorys und übernimmt `app/` aus einem festen GitHub-Commit. Er ersetzt keine Root-Dateien und aktualisiert sich selbst nicht. HTTPS-Download, Größenbegrenzung, Pfadprüfung und Python-Syntaxprüfung; bei Download-/Validierungsfehler läuft die vorhandene Version weiter. Lokale Änderungen in `app/` werden dabei ersetzt und als Codebackup erhalten. Codeupdates erfolgen beim Start, nicht während einer laufenden Sitzung. Der Starter nutzt den Standard-Datenpfad und Port 8765. Für eigene Datenpfade weiterhin die manuelle CLI verwenden.

Codebackups: `.local/share/agent-x-2/code-backups/` im Benutzerordner. SQLite-Sicherung vor Serverstart und vor neuen automatischen Importen: `.local/share/agent-x-2/backups/`. Sicherungen enthalten private Daten, bleiben auf dem Rechner und werden nicht automatisch gelöscht. Zur Wiederherstellung Server stoppen und das benötigte App-Codebackup zurückkopieren; bei Bedarf SQLite wie oben wiederherstellen. Liegen private Daten in `app/`, wird das Codeupdate vorsorglich nicht angewandt.

## Automatischer Importordner

Der Starter aktiviert `--automate`. Neue JSON-Pakete nach `.local/share/agent-x-2/imports/inbox/` im Benutzerordner speichern. Unter Windows standardmäßig `%USERPROFILE%\.local\share\agent-x-2\imports\inbox`. Alle 15 Sekunden Prüfung; zwei unveränderte Prüfungen vor dem Import. Erfolgreiche Pakete wandern nach `processed`, fehlerhafte nach `failed`. Wiederholungen werden anhand bestehender IDs übersprungen; manuelle Korrekturen bleiben erhalten. Pakete bleiben reine Daten, Anweisungen darin werden nicht ausgeführt. Letzter Abruf/Import und Fehler sind in Systems & Security sichtbar.

Dies ist **keine direkte ChatGPT-Synchronisation**. Chatwissen muss weiterhin als zulässiges Importpaket bereitgestellt werden. Google-Verbindungen sowie Mail-, Fristen- und Turnier-Scheduler bleiben nicht eingerichtet. Worker nur aktiv, solange der lokale Server läuft. Windows-Autostart und Onlinehosting sind nicht eingerichtet. Die Windows-End-to-End-Prüfung auf deinem Rechner steht aus.
