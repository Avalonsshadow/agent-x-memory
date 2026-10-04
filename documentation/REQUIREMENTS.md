# Anforderungen und Meilensteine

## M1 umgesetzt
- Neun navigierbare Module, dunkles responsives LCARS-Design, deutsche Oberfläche.
- Zentrale mit offenen Aufgaben, heutigen/überfälligen Fristen, aktiven Projekten, Notizen, letzten Änderungen; Eintragslisten öffnen die Originaleinträge.
- CRUD für Projekte, Aufgaben, Notizen, Fakten, Termine und Dokumentverweise; Tags und Projektverknüpfung.
- Quelle, Standdatum, bestätigt/geschätzt/zu prüfen; Suche, Export, Löschen.
- SQLite-Persistenz, Passwort-/Sitzungsschutz, CSRF, validierte Eingaben.
- Regelbasierte Quellenantworten als klar begrenzte erste Assistenzfunktion.
- Systemstatus mit ehrlich nicht eingerichteten Integrationen und inaktiven Hintergrundaufgaben.
- Manifest und Service Worker, Home-Bildschirm vorbereitet. Tatsächliche Installation auf iOS/Safari noch nicht geprüft.

## Weitere Meilensteine
M2: Dokumentupload, sichere Extraktion, Versionen, Volltextsuche, VDA-Wissensbereich anhand eigener zulässiger Quellen.
M3: private Laufzeit mit persistentem Storage, TLS und Restore-Prüfung; Google/GitHub-OAuth und reale Abruf-/Fehlerprotokolle.
M4: Assistent mit Quellen und strukturierten Ergebnissen; ausdrückliche Freigabe für externen Versand/Löschungen/Kosten; berufliche Entwürfe mit menschlicher Prüfung.
M5: Economics-Tabellen und nachvollziehbare Szenarien; Health-Messreihen; Laboratory-Experimentformular; Billardtraining; Auditpläne/Feststellungen/Nachweise/Maßnahmen mit ausschließlich Beispieldaten.
M6: echter Scheduler, Fristen und Tagesübersicht; dringende Nachrichten und Pool-Termine erst nach verbundenen Quellen und überprüften Läufen.

## Grenzen
Keine Bank-/Handelsaktionen. Keine Therapieentscheidungen. Keine erfundenen Messwerte oder Normtexte. Kein automatischer Zugriff auf andere Chats. Keine echten Unternehmensdaten ohne freigegebene Umgebung. Öffentliche Veröffentlichung und kostenpflichtige Dienste benötigen separate Zustimmung.
Deutsch aktiv; ES/EN-Labelkatalog als Ausgangspunkt, noch keine vollständige Umschaltung.

## Designentscheidung 2026-10-04
Variante 1 „LCARS Cockpit“ wurde vom Nutzer gewählt: dunkles Navy, orange Strukturbänder, Cyan als Fokus und Grün für ergänzende Statushinweise. Zentrale mit heutigen Terminen (alle Bereiche), echten Kennzahlen, Prioritäten, Projekten und kommenden sieben Tagen. Status bleibt als Text erkennbar. Varianten 2 „Tagesplaner“ und 3 „Analytische Zentrale“ bleiben mögliche spätere Ansichten; noch nicht implementiert. Keine Beispieldaten in produktiven Bestand übernommen.

### Konkretisierte Cockpit-Anordnung
Referenzbild als Layoutbasis: drei Kennzahlen, Heute/Fokus parallel, rechts sieben Tage und Schnellzugriff, darunter aktive Projekte und Verbindungsstatus. Zusätzliche Änderungsübersicht und Datenabfrage bleiben aufklappbar. Mobile Ansicht stapelt die Bereiche und verbirgt die Navigation bis zum Menüaufruf. Ausgegebene Status und Zahlen basieren ausschließlich auf gespeicherten Datensätzen und Integrationsstatus.
