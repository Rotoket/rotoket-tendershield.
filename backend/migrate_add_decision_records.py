#!/usr/bin/env python3
"""
Миграция БД: создание таблицы decision_records (ШАГ 11 — Decision Record v1.0)

Создает таблицу для Журнала управленческих решений с каноническими 7 полями.
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text, inspect
from database import get_database_url, Base
from database import DecisionRecord
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_decision_records_table():
    """Создает таблицу decision_records если её нет"""
    try:
        db_url = get_database_url()
        engine = create_engine(db_url, echo=False)
        
        # Проверяем, существует ли таблица
        inspector = inspect(engine)
        if 'decision_records' in inspector.get_table_names():
            logger.info("✅ Таблица decision_records уже существует")
            return True
        
        # Создаем таблицу
        logger.info("📝 Создание таблицы decision_records...")
        DecisionRecord.metadata.create_all(engine)
        logger.info("✅ Таблица decision_records успешно создана")
        
        # Для SQLite проверяем индексы
        if 'sqlite' in db_url:
            with engine.connect() as conn:
                # Проверяем наличие индексов
                indexes = inspector.get_indexes('decision_records')
                logger.info(f"📊 Создано индексов: {len(indexes)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания таблицы decision_records: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = create_decision_records_table()
    sys.exit(0 if success else 1)





























