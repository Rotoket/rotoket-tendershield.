"""
Общие фикстуры для всех тестов
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db, SessionLocal
from config import settings
import os


@pytest.fixture(scope="function")
def db_session():
    """
    Фикстура для сессии БД для тестов.
    Создает транзакцию, которая откатывается после теста.
    """
    try:
        # Используем существующую сессию из database.py
        db = next(get_db())
        
        # Начинаем транзакцию
        trans = db.begin()
        
        try:
            yield db
        finally:
            # Откатываем транзакцию после теста
            trans.rollback()
            db.close()
    except Exception as e:
        # Если БД недоступна, пропускаем тест
        pytest.skip(f"База данных недоступна: {e}")


@pytest.fixture(scope="function")
def test_db_session():
    """
    Альтернативная фикстура для тестов с использованием тестовой БД.
    Использует SQLite для тестов, если PostgreSQL недоступен.
    """
    # Пытаемся использовать PostgreSQL
    try:
        db = next(get_db())
        trans = db.begin()
        try:
            yield db
        finally:
            trans.rollback()
            db.close()
    except Exception:
        # Fallback на SQLite для тестов
        test_db_path = "test_tender_shield.db"
        test_engine = create_engine(
            f"sqlite:///{test_db_path}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=test_engine)
        TestSessionLocal = sessionmaker(bind=test_engine)
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
            # Удаляем тестовую БД после теста
            if os.path.exists(test_db_path):
                os.remove(test_db_path)





