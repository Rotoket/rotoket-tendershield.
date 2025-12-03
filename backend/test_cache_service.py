"""
Тесты для cache_service
"""

import pytest
from cache_service import get_document_hash, get_cached_analysis, cache_analysis, clear_cache


def test_get_document_hash():
    """Тест вычисления хеша документа"""
    content = b"test document content"
    filename = "test.pdf"
    
    hash1 = get_document_hash(content, filename)
    hash2 = get_document_hash(content, filename)
    
    # Одинаковый контент и имя должны давать одинаковый хеш
    assert hash1 == hash2
    
    # Разный контент должен давать разный хеш
    hash3 = get_document_hash(b"different content", filename)
    assert hash1 != hash3


def test_cache_analysis():
    """Тест кеширования результата"""
    content = b"test document"
    file_hash = get_document_hash(content, "test.pdf")
    
    result = {
        "score": 75,
        "verdict": "CAUTION",
        "summary": "Test analysis"
    }
    
    # Кешируем результат
    cache_analysis(file_hash, result, "UNIVERSAL", ttl=3600)
    
    # Получаем из кеша
    cached = get_cached_analysis(file_hash, "UNIVERSAL")
    
    assert cached is not None
    assert cached["score"] == 75
    assert cached["verdict"] == "CAUTION"


def test_cache_different_industries():
    """Тест что разные отрасли дают разные кеши"""
    content = b"test document"
    file_hash = get_document_hash(content, "test.pdf")
    
    result1 = {"score": 75, "industry": "IT"}
    result2 = {"score": 80, "industry": "CONSTRUCTION"}
    
    cache_analysis(file_hash, result1, "IT")
    cache_analysis(file_hash, result2, "CONSTRUCTION")
    
    cached_it = get_cached_analysis(file_hash, "IT")
    cached_const = get_cached_analysis(file_hash, "CONSTRUCTION")
    
    assert cached_it["score"] == 75
    assert cached_const["score"] == 80


def test_clear_cache():
    """Тест очистки кеша"""
    content = b"test document"
    file_hash = get_document_hash(content, "test.pdf")
    
    result = {"score": 75}
    cache_analysis(file_hash, result, "UNIVERSAL")
    
    # Проверяем что есть в кеше
    assert get_cached_analysis(file_hash, "UNIVERSAL") is not None
    
    # Очищаем
    clear_cache(file_hash)
    
    # Проверяем что очистилось
    assert get_cached_analysis(file_hash, "UNIVERSAL") is None

