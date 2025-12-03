"""
Тесты для excel_export
"""

import pytest
from excel_export import generate_excel_report


def test_generate_excel_report_basic():
    """Тест генерации базового Excel отчета"""
    analysis_data = {
        "filename": "test.pdf",
        "industry": "UNIVERSAL",
        "score": 75,
        "verdict": "CAUTION",
        "summary": "Test analysis summary",
        "passport": {
            "nmck": "1 000 000 руб.",
            "region": "Москва",
            "fz": "44-ФЗ",
            "deadlineApp": "2025-02-01",
            "guarantee": "5%"
        },
        "issues": [
            {
                "title": "Тестовый риск",
                "severity": "HIGH",
                "description": "Описание риска",
                "quote": "Цитата из документа"
            }
        ],
        "specs": [
            {
                "name": "Товар 1",
                "qty": "10 шт",
                "details": "Характеристики"
            }
        ]
    }
    
    try:
        excel_buffer = generate_excel_report(analysis_data)
        assert excel_buffer is not None
        # Проверяем размер файла
        excel_buffer.seek(0, 2)  # Переходим в конец
        size = excel_buffer.tell()
        assert size > 0  # Файл не пустой
        excel_buffer.seek(0)  # Возвращаемся в начало
    except ImportError:
        pytest.skip("openpyxl не установлен")


def test_generate_excel_report_minimal():
    """Тест генерации минимального Excel отчета"""
    analysis_data = {
        "filename": "test.pdf",
        "score": 50,
        "verdict": "STOP",
        "summary": "Minimal test"
    }
    
    try:
        excel_buffer = generate_excel_report(analysis_data)
        assert excel_buffer is not None
    except ImportError:
        pytest.skip("openpyxl не установлен")

