"""
Миграция: добавление поля decision_at в таблицы analyses и package_analyses

Использование: python migrate_add_decision_at.py
"""

import sys
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_database_url, Base, engine

def run_migration():
    """Добавляет поля decision_at и user_decision в таблицы analyses и package_analyses"""
    print("[INFO] Запуск миграции: добавление полей decision_at и user_decision...")
    
    # Создаем движок
    db_url = get_database_url()
    is_sqlite = db_url.startswith("sqlite")
    
    print(f"[INFO] База данных: {'SQLite' if is_sqlite else 'PostgreSQL'}")
    
    # Создаем сессию
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        inspector = inspect(engine)
        
        # Проверяем таблицу analyses
        if 'analyses' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('analyses')]
            
            # Добавляем user_decision если отсутствует
            if 'user_decision' not in columns:
                print("[INFO] Добавляю поле user_decision в таблицу analyses...")
                if is_sqlite:
                    db.execute(text("ALTER TABLE analyses ADD COLUMN user_decision TEXT"))
                else:
                    db.execute(text("ALTER TABLE analyses ADD COLUMN user_decision JSONB"))
                print("[OK] Поле user_decision добавлено в таблицу analyses")
            else:
                print("[INFO] Поле user_decision уже существует в таблице analyses")
            
            # Добавляем decision_at если отсутствует
            if 'decision_at' not in columns:
                print("[INFO] Добавляю поле decision_at в таблицу analyses...")
                if is_sqlite:
                    # SQLite не поддерживает ADD COLUMN с индексом в одной команде
                    db.execute(text("ALTER TABLE analyses ADD COLUMN decision_at DATETIME"))
                    db.execute(text("CREATE INDEX IF NOT EXISTS ix_analyses_decision_at ON analyses(decision_at)"))
                else:
                    # PostgreSQL
                    db.execute(text("ALTER TABLE analyses ADD COLUMN decision_at TIMESTAMP"))
                    db.execute(text("CREATE INDEX IF NOT EXISTS ix_analyses_decision_at ON analyses(decision_at)"))
                print("[OK] Поле decision_at добавлено в таблицу analyses")
            else:
                print("[INFO] Поле decision_at уже существует в таблице analyses")
        else:
            print("[WARNING] Таблица analyses не найдена")
        
        # Проверяем таблицу package_analyses
        if 'package_analyses' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('package_analyses')]
            
            # Добавляем user_decision если отсутствует
            if 'user_decision' not in columns:
                print("[INFO] Добавляю поле user_decision в таблицу package_analyses...")
                if is_sqlite:
                    db.execute(text("ALTER TABLE package_analyses ADD COLUMN user_decision TEXT"))
                else:
                    db.execute(text("ALTER TABLE package_analyses ADD COLUMN user_decision JSONB"))
                print("[OK] Поле user_decision добавлено в таблицу package_analyses")
            else:
                print("[INFO] Поле user_decision уже существует в таблице package_analyses")
            
            # Добавляем decision_at если отсутствует
            if 'decision_at' not in columns:
                print("[INFO] Добавляю поле decision_at в таблицу package_analyses...")
                if is_sqlite:
                    db.execute(text("ALTER TABLE package_analyses ADD COLUMN decision_at DATETIME"))
                    db.execute(text("CREATE INDEX IF NOT EXISTS ix_package_analyses_decision_at ON package_analyses(decision_at)"))
                else:
                    db.execute(text("ALTER TABLE package_analyses ADD COLUMN decision_at TIMESTAMP"))
                    db.execute(text("CREATE INDEX IF NOT EXISTS ix_package_analyses_decision_at ON package_analyses(decision_at)"))
                print("[OK] Поле decision_at добавлено в таблицу package_analyses")
            else:
                print("[INFO] Поле decision_at уже существует в таблице package_analyses")
        else:
            print("[WARNING] Таблица package_analyses не найдена")
        
        db.commit()
        print("[OK] Миграция успешно завершена")
        
    except Exception as e:
        print(f"[ERROR] Ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()

