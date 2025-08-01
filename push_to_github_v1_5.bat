@echo off
echo 🌐 Starte GitHub-Push von Agent_X Mutterkorn v1.5...

cd /d "C:\Users\patri\Desktop\DesktopAgentXUploader"

:: Initialisiere Git (nur einmal notwendig)
git init

:: Füge Remote hinzu (überspringt, falls bereits vorhanden)
git remote remove origin >nul 2>&1
git remote add origin https://github.com/Avalonsshadow/agent-x-memory.git

:: Dateien hinzufügen und committen
git add .
git commit -m "🚀 Push: MutterkornTest v1.5 - initial public release"
git branch -M main

:: Push an GitHub senden
git push -u origin main

echo ✅ Push abgeschlossen!
pause
