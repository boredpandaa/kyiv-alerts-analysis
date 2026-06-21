import os
import requests
import sys

# Скрипт сам забере токен із терміналу, нічого хардкодити не треба
TOKEN = os.environ.get("ALERTS_IN_UA_TOKEN")

if not TOKEN:
    print("Помилка: змінна середовища ALERTS_IN_UA_TOKEN порожня.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

URL = "https://api.alerts.in.ua/v1/regions"

def fetch_regions():
    try:
        response = requests.get(URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        print("З'єдналися успішно. Структура першого елемента:")
        
        if isinstance(data, list) and len(data) > 0:
            print(data[0])
        elif isinstance(data, dict):
            print(list(data.keys())[:5])
        else:
            print(data)
            
    except requests.exceptions.HTTPError as e:
        if response.status_code == 429:
            print("Спіймали ліміт запитів (rate limit).")
        elif response.status_code == 401:
            print("API відхилило запит (unauthorized). Перевір токен.")
        else:
            print(f"HTTP помилка: {e}")
    except Exception as e:
        print(f"Неочікувана помилка (unexpected error): {e}")

if __name__ == "__main__":
    fetch_regions()