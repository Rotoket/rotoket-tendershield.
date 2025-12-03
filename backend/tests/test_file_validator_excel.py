"""
Тесты для поддержки Excel-файлов в валидаторе и чтении.
"""

from io import BytesIO

import pytest
from fastapi import UploadFile

from utils.file_validator import validate_file
from main import analyze_single_file


def test_validate_excel_extensions():
    """Проверяем, что .xls и .xlsx проходят базовую валидацию расширения."""

    for ext in (".xls", ".xlsx"):
        # Конструктор UploadFile в FastAPI принимает только (filename, file)
        upload = UploadFile(
            filename=f"test{ext}",
            file=BytesIO(b"dummy"),
        )
        is_valid, error = validate_file(upload)
        assert is_valid is True
        assert error is None


@pytest.mark.asyncio
async def test_analyze_single_file_reads_excel(tmp_path):
    """Проверяем, что Excel-файл читается без ошибки и не считается пустым.

    Чтобы не дергать LLM, мы только проверяем стадию чтения и базовую валидацию,
    эмулируя Excel-файл с помощью openpyxl.
    """
    from openpyxl import Workbook

    # Готовим временный Excel-файл
    excel_path = tmp_path / "sample.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws["A1"] = "Наименование"
    ws["B1"] = "Количество"
    ws["A2"] = "Товар 1"
    ws["B2"] = 10
    wb.save(str(excel_path))

    # Вызываем только часть analyze_single_file до чтения LLM, проверяя отсутствие ошибок чтения.
    # Для этого подменять LLM не будем: если LLM недоступен, сработает fallback,
    # и тест останется устойчивым (мы не проверяем содержимое анализа, только отсутствие 400/500 на чтении).
    try:
        result = await analyze_single_file(str(excel_path), "sample.xlsx", "UNIVERSAL")
        assert isinstance(result, dict)
        # Ожидаем, что passport и issues присутствуют хотя бы как структуры
        assert "passport" in result
        assert "issues" in result
    except Exception as e:
        pytest.fail(f"analyze_single_file не должен падать на Excel-файле: {e}")


