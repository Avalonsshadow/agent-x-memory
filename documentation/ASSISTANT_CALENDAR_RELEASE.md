# Assistent, Kalender und Windows-Start

RELEASE_STATUS: DEVELOPMENT_TESTED

Stand: 2026-10-04. Entwicklung und isolierte Tests abgeschlossen; echte Kalenderanmeldung und Windows-Anmeldestart sind noch nicht bestätigt.

## Nutzung nach automatischem Update
- Oben „Frag Agent X“ öffnen. Tagesprioritäten, Fristen, Projekte, Lernaufgaben und passende Dokumentauszüge mit Quellen. Regelbasiert, kein generatives KI-Modell und keine Kosten.
- Systems & Security → Google Kalender: im bisherigen Google-Projekt die Google Calendar API aktivieren, „Kalender verbinden“, bei Google persönlich zustimmen, Kalender auswählen und Termine abrufen. Die Desktop-OAuth-Konfiguration wird aus der bestehenden Drive-Konfiguration übernommen; getrennte Tokens, Drive bleibt verbunden.
- Kalender ausschließlich lesend. Zeitraum 30 Tage zurück bis 180 Tage voraus; Abruf alle 15 Minuten bei laufendem Server. Zeiten mit Quelloffset im Inhalt, Fristdatum in lokaler Serverzeitzone; ganztägige Ereignisse behalten ihr Quelldatum. Absagen archivieren lokale Einträge. Projektzuordnung und Tags bleiben erhalten. Lokale Löschungen werden nicht automatisch wieder angelegt.
- Lokale Fristen-/Tagesübersicht alle 60 Sekunden; Anzeige in App, keine integrierte Handy-Push-Zustellung.
- Windows-Autostart wird beim Start der aktualisierten App mit --automate auf Standardport/default Datenpfad eingerichtet. Benutzer-Startup-Eintrag, keine Administratorrechte. Hintergrundstarter wartet auf Ende der Vordergrundinstanz, startet ohne Terminal und hält einen exklusiven Windows-Dateilock. Status unterscheidet Einrichtung von tatsächlich gestartetem Hintergrundprozess. Ordner darf nicht verschoben werden. Entfernen über Systems & Security.

## Validierung und Grenzen
37 Python-Tests sowie Frontend-Node-Adapter gegen echten lokalen HTTP/SQLite-Server: Quellen, Aufgabenfortschritt, Dokumentfundstellen, leere Antworten, Zugriffsschutz, CSRF, OAuth-State/PKCE/getrennte Scopes, Google-Fehler, Kalenderänderungen/Absagen, unvollständige Seiten ohne Teilübernahme, Zeitoffset, Export/Restore, lokale Löschung, Tagesübersicht und Windows-Pfade mit Leerzeichen.
Google-Transport simuliert. Windows-VBS/Runner-Erzeugung geprüft, keine echte Windows-Anmeldung ausführbar. Kein echter Browser-/iPhone-Test. Private OAuth-Dateien liegen lokal unverschlüsselt außerhalb Git und JSON-Eintragsexport. Kalenderfreigabe durch Kontoinhaber erforderlich. Automatisches Update auf fremdem PC kann hier nicht bestätigt werden. Fachliche KI-Zusammenfassung, Mail-, Pool- und Push-Integration folgen.

Offizielle Grundlagen: https://developers.google.com/calendar/api/v3/reference/events/list und https://support.microsoft.com/en-gb/windows/experience/startup-boot/configure-startup-applications-in-windows .
