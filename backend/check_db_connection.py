"""
Скрипт для проверки подключения к PostgreSQL
Помогает диагностировать проблемы с БД
"""

import sys
from config import settings

def get_safe_db_params():
    """Получает параметры БД с безопасной обработкой кодировки"""
    params = {}
    errors = []
    
    try:
        params['host'] = str(settings.DB_HOST)
    except Exception as e:
        errors.append(f"Host: {e}")
        params['host'] = "localhost"
    
    try:
        params['port'] = int(settings.DB_PORT)
    except Exception as e:
        errors.append(f"Port: {e}")
        params['port'] = 5432
    
    try:
        params['database'] = str(settings.DB_NAME)
    except Exception as e:
        errors.append(f"Database: {e}")
        params['database'] = "tender_shield"
    
    try:
        user = str(settings.DB_USER)
        # Проверяем кодировку
        user.encode('utf-8', errors='strict')
        params['user'] = user
    except UnicodeEncodeError as e:
        errors.append(f"User (кодировка): {e}")
        params['user'] = "postgres"
    except Exception as e:
        errors.append(f"User: {e}")
        params['user'] = "postgres"
    
    try:
        password = str(settings.DB_PASSWORD)
        # Проверяем кодировку - это критично!
        password.encode('utf-8', errors='strict')
        params['password'] = password
    except UnicodeEncodeError as e:
        errors.append(f"Password (кодировка): {e}")
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: Проблема с кодировкой пароля!")
        print(f"   Ошибка: {e}")
        print(f"   💡 РЕШЕНИЕ: Измените пароль на только латинские буквы и цифры")
        print(f"   💡 Или создайте файл .env с правильной кодировкой UTF-8")
        params['password'] = "postgres"  # Fallback
    except Exception as e:
        errors.append(f"Password: {e}")
        params['password'] = "postgres"
    
    return params, errors


def check_postgresql_connection():
    """Проверяет подключение к PostgreSQL"""
    print("=" * 60)
    print("Проверка подключения к PostgreSQL")
    print("=" * 60)
    
    # Получаем безопасные параметры
    params, errors = get_safe_db_params()
    
    # Выводим параметры
    print(f"\nПараметры подключения:")
    print(f"  Host: {params['host']}")
    print(f"  Port: {params['port']}")
    print(f"  Database: {params['database']}")
    print(f"  User: {params['user']}")
    print(f"  Password: {'*' * len(params['password'])} (длина: {len(params['password'])})")
    
    if errors:
        print(f"\n⚠️  Обнаружены проблемы:")
        for error in errors:
            print(f"   - {error}")
        print(f"\n💡 См. инструкцию: РЕШЕНИЕ_КОДИРОВКИ_WINDOWS.md")
    
    # Проверка psycopg2
    print("\n1. Проверка psycopg2...")
    try:
        import psycopg2
        print(f"   ✅ psycopg2 установлен (версия: {psycopg2.__version__})")
    except ImportError:
        print("   ❌ psycopg2 не установлен")
        print("   💡 Установите: pip install psycopg2-binary")
        return False
    
    # Проверка подключения
    print("\n2. Проверка подключения к PostgreSQL...")
    try:
        # Используем безопасные параметры
        conn = psycopg2.connect(
            host=params['host'],
            port=params['port'],
            database=params['database'],
            user=params['user'],
            password=params['password'],
            connect_timeout=10
        )
        # Устанавливаем кодировку сразу после подключения
        conn.set_client_encoding('UTF8')
        print("   ✅ Подключение успешно!")
        
        # Проверка кодировки
        print("\n3. Проверка кодировки БД...")
        cur = conn.cursor()
        cur.execute("SHOW client_encoding;")
        encoding = cur.fetchone()[0]
        print(f"   Текущая кодировка: {encoding}")
        
        if encoding.upper() != 'UTF8':
            print("   ⚠️  Кодировка не UTF8! Рекомендуется:")
            print("      ALTER DATABASE tender_shield SET client_encoding = 'UTF8';")
        else:
            print("   ✅ Кодировка UTF8 установлена")
        
        # Проверка версии PostgreSQL
        print("\n4. Версия PostgreSQL...")
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        print(f"   {version}")
        
        cur.close()
        conn.close()
        print("\n✅ Все проверки пройдены!")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"   ❌ Ошибка подключения: {e}")
        print("\n💡 Возможные решения:")
        print("   1. Убедитесь, что PostgreSQL запущен")
        print("   2. Проверьте параметры подключения в .env или config.py")
        print("   3. Убедитесь, что база данных 'tender_shield' существует")
        print("   4. Проверьте права доступа пользователя")
        return False
    except Exception as e:
        print(f"   ❌ Неожиданная ошибка: {e}")
        return False


def check_database_exists():
    """Проверяет существование базы данных"""
    print("\n" + "=" * 60)
    print("Проверка существования базы данных")
    print("=" * 60)
    
    try:
        import psycopg2
        # Убеждаемся, что все параметры в правильной кодировке
        host = str(settings.DB_HOST).encode('utf-8', errors='replace').decode('utf-8')
        port = int(settings.DB_PORT)
        user = str(settings.DB_USER).encode('utf-8', errors='replace').decode('utf-8')
        password = str(settings.DB_PASSWORD).encode('utf-8', errors='replace').decode('utf-8')
        db_name = str(settings.DB_NAME).encode('utf-8', errors='replace').decode('utf-8')
        
        # Подключаемся к системной БД postgres
        conn = psycopg2.connect(
            host=host,
            port=port,
            database="postgres",  # Подключаемся к системной БД
            user=user,
            password=password,
            connect_timeout=10
        )
        # Устанавливаем кодировку сразу после подключения
        conn.set_client_encoding('UTF8')
        
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s;",
            (db_name,)
        )
        exists = cur.fetchone() is not None
        
        if not exists:
            print(f"\n⚠️  База данных '{db_name}' не существует")
            print("\n💡 Создайте базу данных:")
            print(f"   CREATE DATABASE {db_name} ENCODING 'UTF8' LC_COLLATE='ru_RU.UTF-8' LC_CTYPE='ru_RU.UTF-8';")
            print("\n   Или через psql:")
            print(f"   psql -U {user} -c \"CREATE DATABASE {db_name} ENCODING 'UTF8';\"")
        else:
            print(f"✅ База данных '{db_name}' существует")
        
        cur.close()
        conn.close()
        return exists
        
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
        return False


if __name__ == "__main__":
    print("\n🔍 Диагностика подключения к PostgreSQL\n")
    
    # Проверка существования БД
    db_exists = check_database_exists()
    
    # Проверка подключения
    if db_exists:
        success = check_postgresql_connection()
        if success:
            print("\n" + "=" * 60)
            print("✅ Все проверки пройдены успешно!")
            print("=" * 60)
            sys.exit(0)
        else:
            print("\n" + "=" * 60)
            print("❌ Обнаружены проблемы с подключением")
            print("=" * 60)
            sys.exit(1)
    else:
        print("\n⚠️  Сначала создайте базу данных")
        sys.exit(1)

