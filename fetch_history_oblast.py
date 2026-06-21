import os
import requests
import json
import sys

TOKEN = os.environ.get("ALERTS_IN_UA_TOKEN")
if not TOKEN:
    sys.exit("Помилка: змінна середовища ALERTS_IN_UA_TOKEN порожня.")

url = "https://api.alerts.in.ua/v1/regions/14/alerts/month_ago.json"
headers = {"Authorization": f"Bearer {TOKEN}"}

DATA_DIR = "raw_data"

print("Стукаємо в UID 14 (Київська область)...")
try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    alerts = data.get("alerts", [])
    print(f"Отримали {len(alerts)} записів історії.")
    
    if alerts:
        # Створюємо директорію, якщо її немає
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            
        file_path = os.path.join(DATA_DIR, "Kyiv_Oblast_14.json")
        
        # Записуємо дані у файл
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"Файл успішно збережено: {file_path}")
    else:
        print("Масив alerts порожній. Зберігати нічого.")
        
except Exception as e:
    print(f"Помилка: {e}")