"""
Скрипт для миграции: добавление полей триалов в таблицу users
Выполните этот скрипт, если в БД еще нет полей для триалов
"""

import sys
from sqlalchemy import text
from database import engine, get_db

def migrate_trial_fields():
    """Добавляет поля триалов в таблицу users"""
    print("🔄 Начало миграции: добавление полей триалов...")
    
    try:
        # Определяем тип БД
        db_url = str(engine.url)
        is_sqlite = "sqlite" in db_url.lower()
        is_postgres = "postgresql" in db_url.lower() or "postgres" in db_url.lower()
        
        print(f"📊 Тип БД: {'SQLite' if is_sqlite else 'PostgreSQL' if is_postgres else 'Неизвестно'}")
        
        with engine.connect() as conn:
            # Проверяем, существуют ли поля
            if is_postgres:
                check_query = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'plan_type'
                """)
            else:  # SQLite
                check_query = text("PRAGMA table_info(users)")
            
            result = conn.execute(check_query)
            
            if is_postgres:
                exists = result.fetchone() is not None
            else:  # SQLite
                columns = [row[1] for row in result.fetchall()]
                exists = 'plan_type' in columns
            
            if exists:
                print("✅ Поля триалов уже существуют в БД")
                return
            
            print("📝 Добавление полей...")
            
            # Добавляем поля (разный синтаксис для разных БД)
            if is_postgres:
                migrations = [
                    ("plan_type", "ALTER TABLE users ADD COLUMN IF NOT EXISTS plan_type VARCHAR DEFAULT 'trial'"),
                    ("trial_start", "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_start TIMESTAMP"),
                    ("trial_end", "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_end TIMESTAMP"),
                    ("trial_extended", "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_extended BOOLEAN DEFAULT FALSE"),
                    ("subscription_start", "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_start TIMESTAMP"),
                    ("subscription_end", "ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_end TIMESTAMP"),
                ]
            else:  # SQLite
                migrations = [
                    ("plan_type", "ALTER TABLE users ADD COLUMN plan_type VARCHAR DEFAULT 'trial'"),
                    ("trial_start", "ALTER TABLE users ADD COLUMN trial_start TIMESTAMP"),
                    ("trial_end", "ALTER TABLE users ADD COLUMN trial_end TIMESTAMP"),
                    ("trial_extended", "ALTER TABLE users ADD COLUMN trial_extended INTEGER DEFAULT 0"),
                    ("subscription_start", "ALTER TABLE users ADD COLUMN subscription_start TIMESTAMP"),
                    ("subscription_end", "ALTER TABLE users ADD COLUMN subscription_end TIMESTAMP"),
                ]
            
            for field_name, migration in migrations:
                try:
                    # Проверяем, существует ли поле (для SQLite)
                    if is_sqlite:
                        check_result = conn.execute(text("PRAGMA table_info(users)"))
                        existing_columns = [row[1] for row in check_result.fetchall()]
                        if field_name in existing_columns:
                            print(f"   ℹ️  Поле {field_name} уже существует, пропускаем")
                            continue
                    
                    conn.execute(text(migration))
                    conn.commit()
                    print(f"   ✅ {field_name}")
                except Exception as e:
                    error_msg = str(e).lower()
                    # Если поле уже существует, пропускаем
                    if any(keyword in error_msg for keyword in ["already exists", "duplicate", "duplicate column"]):
                        print(f"   ℹ️  Поле {field_name} уже существует, пропускаем")
                    else:
                        print(f"   ⚠️  Ошибка при добавлении {field_name}: {e}")
                        # Для PostgreSQL пробуем без IF NOT EXISTS
                        if is_postgres and "IF NOT EXISTS" in migration:
                            try:
                                migration_alt = migration.replace(" IF NOT EXISTS", "")
                                conn.execute(text(migration_alt))
                                conn.commit()
                                print(f"   ✅ {field_name} добавлено (без IF NOT EXISTS)")
                            except Exception as e2:
                                print(f"   ❌ Не удалось добавить {field_name}: {e2}")
            
            print("\n✅ Миграция завершена успешно!")
            print("\nТеперь можно регистрировать пользователей с триалами.")
            
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    migrate_trial_fields()

