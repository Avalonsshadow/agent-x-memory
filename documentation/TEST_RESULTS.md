# Validierung · Meilenstein 1

Datum: 2026-10-04. Alle Tests ausschließlich mit temporären Beispieldaten; keine persönlichen Inhalte importiert.

## Bestanden
- 12 Python-Tests: geschützte Datenendpunkte; CRUD/Persistenz nach Neuöffnung der Datenbank; Sitzungen nach Neuöffnung; CSRF und fremder Origin; Login-Begrenzung; Datums-/Quellen-/Linkvalidierung; Projektverknüpfung und Löschung; atomarer JSON-Restore; Importanweisungen bleiben Text; Logout; Integrations-/Jobstatus; Pfad-/Headerprüfung; Passwortwechsel; Secure-Cookie.
- `node --check app/web/app.js` und Python-Kompilierung.
- Frontend-Funktionstest im Node-VM-Testadapter gegen echtes Python/SQLite-Backend: neun Module, Anmeldung, Anlegen, Bearbeitungsformular, Datenabruf, Suche, HTML-Escaping, Quellenantworten, errechneter Aufgabenfortschritt, Export, Verbindungsfehler und Abmeldung. **DOM-Adapter, kein echter Browser.**
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
