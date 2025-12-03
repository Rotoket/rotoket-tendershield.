"""
Скрипт для проверки подключения к Ollama
"""

import requests
import sys
from config import settings

def check_ollama():
    """Проверяет подключение к Ollama"""
    print("🔍 Проверка подключения к Ollama...")
    print(f"URL: {settings.OLLAMA_BASE_URL}")
    print(f"Модель: {settings.OLLAMA_MODEL}")
    print()
    
    # Проверка доступности сервера
    try:
        response = requests.get(f"{settings.OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama сервер доступен")
            models = response.json().get("models", [])
            if models:
                print(f"✅ Найдено моделей: {len(models)}")
                model_names = [m.get("name", "") for m in models]
                print(f"   Доступные модели: {', '.join(model_names)}")
                
                # Проверка нужной модели
                if settings.OLLAMA_MODEL in model_names:
                    print(f"✅ Модель '{settings.OLLAMA_MODEL}' установлена")
                else:
                    print(f"❌ Модель '{settings.OLLAMA_MODEL}' НЕ найдена")
                    print(f"   Установите: ollama pull {settings.OLLAMA_MODEL}")
                    return False
            else:
                print("⚠️ Модели не найдены")
                print(f"   Установите: ollama pull {settings.OLLAMA_MODEL}")
                return False
        else:
            print(f"❌ Ollama сервер вернул код: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Не удалось подключиться к Ollama")
        print("   Убедитесь, что Ollama запущен:")
        print("   - Windows: Запустите Ollama из меню Пуск")
        print("   - Linux/Mac: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False
    
    # Тест вызова модели
    print()
    print("🧪 Тестирование вызова модели...")
    try:
        from llm_client import get_analysis_llm
        llm = get_analysis_llm()
        test_response = llm.invoke("Ответь одним словом: работает?")
        print(f"✅ Модель отвечает: {test_response.content[:50]}")
        return True
    except Exception as e:
        print(f"❌ Ошибка при вызове модели: {e}")
        return False

if __name__ == "__main__":
    success = check_ollama()
    if not success:
        print()
        print("📋 Инструкция по установке:")
        print("1. Скачайте Ollama: https://ollama.ai")
        print("2. Установите и запустите Ollama")
        print(f"3. Установите модель: ollama pull {settings.OLLAMA_MODEL}")
        print("4. Проверьте: python check_ollama.py")
        sys.exit(1)
    else:
        print()
        print("✅ Все проверки пройдены! Ollama готов к работе.")

