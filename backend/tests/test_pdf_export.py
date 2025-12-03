"""
Тесты для экспорта в PDF
"""

import pytest
from io import BytesIO
from pdf_export import generate_pdf_report


class TestPDFExport:
    """Тесты для экспорта в PDF"""
    
    def test_generate_pdf_basic(self):
        """Тест базовой генерации PDF"""
        analysis_data = {
            "filename": "test_tender.pdf",
            "industry": "IT",
            "score": 75,
            "verdict": "PARTICIPATE",
            "summary": "Тестовый анализ тендера",
            "passport": {
                "nmck": "1 000 000 ₽",
                "region": "Москва",
                "fz": "44-ФЗ",
                "deadlineApp": "01.02.2025",
                "guarantee": "5%"
            },
            "issues": [
                {
                    "title": "Тестовый риск",
                    "severity": "MEDIUM",
                    "description": "Описание риска",
                    "quote": "Цитата из документа"
                }
            ],
            "specs": [
                {
                    "name": "Тестовый товар",
                    "qty": "10 шт",
                    "details": "Характеристики"
                }
            ],
            "actions": []
        }
        
        try:
            pdf_buffer = generate_pdf_report(analysis_data)
            assert isinstance(pdf_buffer, BytesIO)
            # Проверяем, что в буфере есть данные (даже если курсор в начале)
            content = pdf_buffer.getvalue()
            assert isinstance(content, (bytes, bytearray))
            assert len(content) > 0  # Файл не пустой
        except ImportError:
            pytest.skip("reportlab не установлен")
    
    def test_generate_pdf_with_red_flags(self):
        """Тест генерации PDF с красными флагами"""
        analysis_data = {
            "filename": "test.pdf",
            "score": 30,
            "verdict": "STOP",
            "summary": "Низкая оценка",
            "passport": {},
            "issues": [],
            "specs": [],
            "redFlags": [
                {
                    "code": "IT_BRAND_ONLY",
                    "title": "Ограничение конкуренции",
                    "severity": "HIGH",
                    "lawReference": "ст. 33 44-ФЗ",
                    "explanation": "Требование конкретного бренда",
                    "quote": "Только Intel"
                }
            ],
            "actions": []
        }
        
        try:
            pdf_buffer = generate_pdf_report(analysis_data)
            assert isinstance(pdf_buffer, BytesIO)
        except ImportError:
            pytest.skip("reportlab не установлен")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

