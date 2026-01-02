"""
Миграция: добавление поля is_unlimited в таблицу demo_sessions
Запустить один раз: python migrate_add_demo_unlimited.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import get_db, Base, engine
from sqlalchemy import text

def migrate():
    """Добавляет поле is_unlimited в таблицу demo_sessions"""
    db = next(get_db())
    
    try:
        # Проверяем, существует ли уже поле
        result = db.execute(text("PRAGMA table_info(demo_sessions)"))
        columns = [row[1] for row in result]
        
        if 'is_unlimited' in columns:
            print("[INFO] Поле is_unlimited уже существует в таблице demo_sessions")
            return True
        
        # Добавляем поле
        print("[INFO] Добавляю поле is_unlimited в таблицу demo_sessions...")
        db.execute(text("ALTER TABLE demo_sessions ADD COLUMN is_unlimited BOOLEAN DEFAULT 0"))
        db.commit()
        
        print("[OK] Поле is_unlimited успешно добавлено")
        return True
        
    except Exception as e:
        print(f"[ERROR] Ошибка при миграции: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    migrate()






























