import os
import shutil
from datetime import datetime

# Konfiguration
SOURCE_FILE = "autonomy.json"
BACKUP_DIR = "backups"

# Erstelle Backup-Verzeichnis, falls nicht vorhanden
os.makedirs(BACKUP_DIR, exist_ok=True)

# Zeitstempel generieren
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Zielpfad definieren
backup_filename = f"autonomy_backup_{timestamp}.json"
backup_path = os.path.join(BACKUP_DIR, backup_filename)

# Datei kopieren
try:
    shutil.copyfile(SOURCE_FILE, backup_path)
    print(f"✅ Backup erfolgreich: {backup_path}")
except FileNotFoundError:
    print(f"❌ Quelle {SOURCE_FILE} nicht gefunden.")
except Exception as e:
    print(f"⚠️ Fehler beim Backup: {e}")
