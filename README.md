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
In Systems & Security JSON exportieren; private Exportdateien sicher verwahren. JSON-Import ist nur in einen leeren Datenbestand möglich. Keine bestehenden Einträge werden überschrieben. Eintragslöschungen sind endgültig; vorher bei Bedarf exportieren.

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
