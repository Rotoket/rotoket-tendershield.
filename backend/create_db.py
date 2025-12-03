import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import sys

# --- НАСТРОЙКИ ---
DB_NAME = "tender_shield"  # Имя нашей будущей базы
DB_USER = "postgres"       # Стандартный пользователь
DB_HOST = "localhost"
DB_PORT = "5432"

def create_database():
    print(f"🚀 Начинаем создание базы данных '{DB_NAME}'...")
    
    # Спрашиваем пароль, чтобы не хранить его в коде
    # Если ты устанавливал Postgres без пароля, просто нажми Enter
    db_password = input("Введите пароль от PostgreSQL (который задавали при установке): ").strip()

    try:
        # 1. Подключаемся к системной базе 'postgres'
        con = psycopg2.connect(
            dbname='postgres',
            user=DB_USER,
            host=DB_HOST,
            password=db_password,
            port=DB_PORT
        )
        con.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = con.cursor()
        
        # 2. Проверяем, существует ли база
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        
        if not exists:
            # 3. Создаем базу
            print(f"🛠 База '{DB_NAME}' не найдена. Создаю...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"✅ УСПЕХ! База данных '{DB_NAME}' успешно создана.")
        else:
            print(f"ℹ️ База данных '{DB_NAME}' уже существует. Ничего делать не нужно.")

        cursor.close()
        con.close()

    except Exception as e:
        print("\n❌ ОШИБКА:")
        # Трюк для Windows, чтобы не было кракозябр
        try:
            print(str(e).encode('cp1251').decode('utf-8', 'ignore'))
        except:
            print(e)
        print("\n💡 СОВЕТ: Проверьте правильность пароля.")

if __name__ == "__main__":
    create_database()