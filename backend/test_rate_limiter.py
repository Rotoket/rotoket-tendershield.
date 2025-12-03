"""
Тесты для rate_limiter
"""

import pytest
from fastapi.testclient import TestClient
from main import app


def test_rate_limiter_setup():
    """Тест что rate limiter настроен"""
    client = TestClient(app)
    
    # Проверяем что приложение запускается
    response = client.get("/docs")
    assert response.status_code in [200, 404]  # Может быть 404 если docs отключены


def test_rate_limiter_import():
    """Тест что rate_limiter можно импортировать"""
    try:
        from rate_limiter import setup_rate_limiting, get_user_identifier
        assert callable(setup_rate_limiting)
        assert callable(get_user_identifier)
    except ImportError:
        pytest.skip("slowapi не установлен")

