"""
Скрипт для создания индексов в базе данных для оптимизации запросов
"""

from sqlalchemy import create_engine, text
from database import Base, engine
from config import settings
import logging

logger = logging.getLogger(__name__)

# SQL для создания индексов
INDEXES = [
    # Индексы для таблицы users
    "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
    "CREATE INDEX IF NOT EXISTS idx_users_tariff_id ON users(tariff_id);",
    "CREATE INDEX IF NOT EXISTS idx_users_plan_type ON users(plan_type);",
    "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);",
    
    # Индексы для таблицы analyses
    "CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_analyses_industry ON analyses(industry);",
    "CREATE INDEX IF NOT EXISTS idx_analyses_verdict ON analyses(verdict);",
    "CREATE INDEX IF NOT EXISTS idx_analyses_score ON analyses(score);",
    "CREATE INDEX IF NOT EXISTS idx_analyses_session_id ON analyses(session_id);",
    "CREATE INDEX IF NOT EXISTS idx_analyses_is_demo ON analyses(is_demo);",
    
    # Композитные индексы для частых запросов
    "CREATE INDEX IF NOT EXISTS idx_analyses_user_created ON analyses(user_id, created_at DESC);",
    "CREATE INDEX IF NOT EXISTS idx_analyses_industry_created ON analyses(industry, created_at DESC);",
    
    # Индексы для таблицы package_analyses
    "CREATE INDEX IF NOT EXISTS idx_package_analyses_user_id ON package_analyses(user_id);",
    "CREATE INDEX IF NOT EXISTS idx_package_analyses_created_at ON package_analyses(created_at);",
    
    # Индексы для таблицы usage
    "CREATE INDEX IF NOT EXISTS idx_usage_user_month ON usage(user_id, month);",
    
    # Индексы для таблицы demo_sessions
    "CREATE INDEX IF NOT EXISTS idx_demo_sessions_created_at ON demo_sessions(created_at);",
    "CREATE INDEX IF NOT EXISTS idx_demo_sessions_last_analysis ON demo_sessions(last_analysis_at);",
]


def create_indexes():
    """Создает все индексы в базе данных"""
    try:
        with engine.connect() as conn:
            for index_sql in INDEXES:
                try:
                    conn.execute(text(index_sql))
                    conn.commit()
                    logger.info(f"✅ Создан индекс: {index_sql.split('ON')[0].split('INDEX')[1].strip()}")
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка создания индекса: {e}")
        
        logger.info("✅ Все индексы созданы успешно")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка создания индексов: {e}")
        return False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_indexes()

