
import os
import json
import csv
from datetime import datetime

def import_conversation(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".txt":
        return import_txt(filepath)
    elif ext == ".md":
        return import_md(filepath)
    elif ext == ".json":
        return import_json(filepath)
    elif ext == ".csv":
        return import_csv(filepath)
    else:
        raise ValueError("Nicht unterstütztes Format.")

def import_txt(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    messages = [{"role": "user" if i % 2 == 0 else "assistant", "content": line.strip()} for i, line in enumerate(lines) if line.strip()]
    return wrap_conversation(messages, filepath)

def import_md(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    messages = []
    for line in lines:
        if line.startswith("**User**:"):
            messages.append({"role": "user", "content": line.replace("**User**:", "").strip()})
        elif line.startswith("**Assistant**:"):
            messages.append({"role": "assistant", "content": line.replace("**Assistant**:", "").strip()})
    return wrap_conversation(messages, filepath)

def import_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    messages = data.get("messages", data if isinstance(data, list) else [])
    return wrap_conversation(messages, filepath)

def import_csv(filepath):
    messages = []
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            messages.append({"role": row.get("role", "user"), "content": row.get("message", "")})
    return wrap_conversation(messages, filepath)

def wrap_conversation(messages, source):
    return {
        "id": f"conv_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "messages": messages,
        "metadata": {
            "source": os.path.basename(source),
            "imported_by": "Vince",
            "tags": ["archiviert", "reimport"]
        }
    }
