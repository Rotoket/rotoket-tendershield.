"""
Скрипт для тестирования анализа документов
"""

import requests
import os
import sys

# Тестовый файл
test_file_path = "temp_Проект контракта.doc"

if not os.path.exists(test_file_path):
    print(f"❌ Файл {test_file_path} не найден")
    print("Создайте тестовый файл или укажите путь к существующему файлу")
    sys.exit(1)

# URL API
api_url = "http://localhost:8000/api/analyze"

print("Тестирование анализа документов...")
print(f"Файл: {test_file_path}")
print(f"API: {api_url}")
print()

# Проверка доступности API
try:
    response = requests.get("http://localhost:8000/docs", timeout=2)
    print("[OK] Backend API доступен")
except:
    print("[ERROR] Backend API недоступен. Запустите: uvicorn main:app --reload")
    sys.exit(1)

# Проверка Ollama
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=2)
    if response.status_code == 200:
        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]
        print(f"[OK] Ollama доступен. Модели: {', '.join(model_names)}")
    else:
        print("[WARNING] Ollama недоступен")
except:
    print("[WARNING] Ollama недоступен. Запустите: ollama serve")

print()

# Отправка файла
try:
    with open(test_file_path, 'rb') as f:
        files = {'file': (os.path.basename(test_file_path), f, 'application/msword')}
        data = {'industry': 'UNIVERSAL'}
        
        print("Отправка файла на анализ...")
        response = requests.post(api_url, files=files, data=data, timeout=300)
        
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("[SUCCESS] Анализ успешен!")
            print(f"   Вердикт: {result.get('verdict', 'N/A')}")
            print(f"   Оценка: {result.get('score', 'N/A')}")
            print(f"   Резюме: {result.get('summary', 'N/A')[:100]}...")
        else:
            print(f"[ERROR] Ошибка: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Детали: {error_detail}")
            except:
                print(f"   Ответ: {response.text[:500]}")
            
except Exception as e:
    print(f"[ERROR] Ошибка при отправке: {e}")
    import traceback
    traceback.print_exc()

