# Privater iPhone-Zugriff
Tailscale Serve leitet privaten HTTPS-Verkehr auf die weiterhin ausschließlich lokale App 127.0.0.1:8765. Kein Funnel, keine Router-Portfreigabe, keine öffentliche Veröffentlichung. Bestehende Serve-Dienste werden nicht überschrieben.

Einmalig am Windows-PC:
1. Tailscale von https://tailscale.com/download/windows installieren und anmelden.
2. Im Agent-X-Projektordner (gegebenenfalls als Administrator) ausführen: `py app/server.py private-access`
3. Falls Tailscale HTTPS-Freigabe verlangt, angezeigte Freigabe durchführen, Befehl erneut ausführen.
4. Die ausgegebene https://…ts.net-Adresse in Safari verwenden. Tailscale auf dem iPhone installieren, dasselbe Konto verwenden, VPN erlauben. Agent-X-Passwort bleibt nötig. Safari: Compartir → Añadir a pantalla de inicio.

PC und App müssen laufen; Ruhezustand unterbricht den Zugriff. Private Konfiguration außerhalb des Repositories, dynamisch eingelesen ohne weiteren Server-Neustart. Secure-Cookies für den exakt konfigurierten HTTPS-Host; lokale Anmeldung bleibt verfügbar. Google-OAuth-Einrichtung weiter am PC über localhost. Zugriff durch andere Tailnet-Mitglieder hängt von Tailscale-Zugriffsregeln ab: nur eigene Geräte zulassen. HTTPS-Zertifikate können den Rechner-DNS-Namen in Zertifikattransparenzlisten sichtbar machen; keine vertraulichen Namen verwenden.

Status: programmiert, isoliert getestet; Tailscale-Installation/Anmeldung und Ende-zu-Ende-Prüfung auf den persönlichen Geräten ausstehend. Für einen Test WLAN am iPhone ausschalten und über Mobilfunk anmelden. Keine kostenpflichtigen Dienste aktiviert.
