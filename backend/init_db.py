"""
Скрипт для инициализации базы данных
Создает таблицы и заполняет начальными данными (тарифы)
"""

import sys
from database import init_db, create_default_tariffs, get_db, engine
from sqlalchemy.exc import OperationalError

def main():
    """Инициализирует БД"""
    print("🚀 Инициализация базы данных...")
    
    try:
        # Проверяем подключение
        with engine.connect() as conn:
            print("✅ Подключение к БД успешно")
        
        # Создаем таблицы
        print("📦 Создание таблиц...")
        init_db()
        print("✅ Таблицы созданы")
        
        # Создаем тарифы
        print("💰 Создание тарифных планов...")
        db = next(get_db())
        create_default_tariffs(db)
        db.close()
        print("✅ Тарифы созданы")
        
        print("\n🎉 База данных успешно инициализирована!")
        print("\nСледующие шаги:")
        print("1. Создайте первого пользователя через /api/auth/register")
        print("2. Или используйте команду: python create_admin.py")
        
    except OperationalError as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        print("\nУбедитесь, что:")
        print("1. PostgreSQL запущен")
        print("2. База данных 'tender_shield' создана")
        print("3. Настройки подключения в .env корректны")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


