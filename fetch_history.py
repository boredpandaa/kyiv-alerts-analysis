import os
import time
import json
import requests
import sys

TOKEN = os.environ.get("ALERTS_IN_UA_TOKEN")
if not TOKEN:
    sys.exit("Помилка: змінна середовища ALERTS_IN_UA_TOKEN порожня.")

HEADERS = {"Authorization": f"Bearer {TOKEN}"}
DATA_DIR = "raw_data"

# Нам потрібні лише два макро-запити
TARGETS = {
    "Kyiv_City_31": 31,
    "Kyiv_Oblast_14": 14
}

def fetch_and_cache():
    os.makedirs(DATA_DIR, exist_ok=True)

    for name, uid in TARGETS.items():
        file_path = os.path.join(DATA_DIR, f"{name}.json")
        if os.path.exists(file_path):
            print(f"[{name}] Файл існує, пропускаємо.")
            continue
            
        url = f"https://api.alerts.in.ua/v1/regions/{uid}/alerts/month_ago.json"
        print(f"[{name}] Викачуємо історію...")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, ensure_ascii=False, indent=2)
            print(f"[{name}] Збережено.")
            
        except Exception as e:
            print(f"[{name}] Помилка: {e}")
            
        # Пауза між макро-запитами для безпеки лімітів
        if uid != list(TARGETS.values())[-1]:
            time.sleep(35)

if __name__ == "__main__":
    fetch_and_cache()