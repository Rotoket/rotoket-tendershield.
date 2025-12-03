"""
Диагностика проблемы анализа документов
"""

import sys
import traceback

print("=" * 60)
print("ДИАГНОСТИКА АНАЛИЗА ДОКУМЕНТОВ")
print("=" * 60)
print()

# 1. Проверка импортов
print("[1] Проверка импортов...")
try:
    from main import app, analyze_single_file
    print("  [OK] main.py импортируется")
except Exception as e:
    print(f"  [ERROR] Ошибка импорта main.py: {e}")
    traceback.print_exc()
    sys.exit(1)

# 2. Проверка конфигурации
print("\n[2] Проверка конфигурации...")
try:
    from config import settings
    print(f"  [OK] Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"  [OK] Ollama Model: {settings.OLLAMA_MODEL}")
except Exception as e:
    print(f"  [ERROR] Ошибка конфигурации: {e}")

# 3. Проверка LLM клиента
print("\n[3] Проверка LLM клиента...")
try:
    from llm_client import get_analysis_llm, invoke_with_retry
    llm = get_analysis_llm()
    print("  [OK] LLM клиент создан")
except Exception as e:
    print(f"  [ERROR] Ошибка LLM клиента: {e}")
    traceback.print_exc()

# 4. Проверка специализированных анализаторов
print("\n[4] Проверка специализированных анализаторов...")
try:
    from specialized_analyzers import analyze_with_specialized_analyzers
    print("  [OK] Специализированные анализаторы доступны")
except Exception as e:
    print(f"  [WARNING] Специализированные анализаторы недоступны: {e}")

# 5. Проверка registry checker
print("\n[5] Проверка Registry Checker...")
try:
    from registry_checker import RegistryChecker
    print("  [OK] Registry Checker доступен")
except Exception as e:
    print(f"  [WARNING] Registry Checker недоступен: {e}")

# 6. Проверка загрузчиков файлов
print("\n[6] Проверка загрузчиков файлов...")
try:
    from langchain_community.document_loaders import PyMuPDFLoader, Docx2txtLoader
    print("  [OK] Загрузчики файлов доступны")
except Exception as e:
    print(f"  [ERROR] Ошибка загрузчиков: {e}")

# 7. Проверка БД
print("\n[7] Проверка подключения к БД...")
try:
    from database import get_db, engine
    from sqlalchemy import text
    db = next(get_db())
    db.execute(text("SELECT 1"))
    db.close()
    print("  [OK] БД доступна")
except Exception as e:
    print(f"  [WARNING] БД недоступна (будет использован SQLite): {e}")

print("\n" + "=" * 60)
print("ДИАГНОСТИКА ЗАВЕРШЕНА")
print("=" * 60)

