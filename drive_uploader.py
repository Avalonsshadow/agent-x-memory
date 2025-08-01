import requests
import base64
import os

# === CONFIG ===
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby9WEo10EcWp9NVytOgjLm-XuCP3JQ7_Fsr_kH0rzQhjzShgB8pAsdJkBJoeqeXVFxh/exec"
BACKUP_DIR = "backups"

def upload_file(filepath):
    filename = os.path.basename(filepath)

    with open(filepath, "rb") as f:
        file_content = f.read()
        encoded = base64.b64encode(file_content).decode("utf-8")

    payload = {
        "file": encoded,
        "filename": filename,
        "mimeType": "application/json"
    }

    response = requests.post(SCRIPT_URL, data=payload)
    print(f"📤 {filename} → Antwort: {response.text}")

def upload_all_backups():
    for file in os.listdir(BACKUP_DIR):
        if file.endswith(".json"):
            filepath = os.path.join(BACKUP_DIR, file)
            upload_file(filepath)

if __name__ == "__main__":
    upload_all_backups()
