"""
Интеграционный тест: проверяем, что analyze_single_file вызывает RAG (get_law_snippets)
и корректно обрабатывает ответ LLM (подменённый заглушкой).
"""

import os
from pathlib import Path

import pytest

import main


class DummyLLMResponse:
    def __init__(self, content: str):
        self.content = content


@pytest.mark.asyncio
async def test_analyze_single_file_uses_rag(monkeypatch, tmp_path):
    """Проверяем, что при анализе документа вызывается get_law_snippets и
    что ответ LLM (заглушка) корректно парсится.
    """

    # Флаг, чтобы убедиться, что RAG действительно вызывался
    called = {"rag": False}

    def fake_get_law_snippets(query_text: str, k: int = 5):
        called["rag"] = True
        # Возвращаем один простой фрагмент "закона"
        return [
            {
                "content": "Штраф за просрочку составляет 0.1% за каждый день, но не более 10% НМЦК.",
                "metadata": {"source": "тестовый_закон"},
            }
        ]

    # Заглушка для _safe_ollama_invoke: возвращаем минимально валидный JSON
    def fake_safe_invoke(prompt: str, format_json: bool = True) -> str:
        # Убедимся, что наш фрагмент закона попал в промпт (не прерываем тест, но проверяем)
        assert "Штраф за просрочку составляет 0.1%" in prompt
        return """
        {
            "summary": "Тестовый анализ",
            "score": 70,
            "passport": {
                "nmck": "1 000 000 ₽",
                "region": "Москва",
                "fz": "44-ФЗ",
                "deadlineApp": "01.01.2030",
                "guarantee": "5%"
            },
            "issues": [],
            "specs": [],
            "redFlags": [],
            "financialSummary": {},
            "timelineSummary": {},
            "actions": []
        }
        """

    monkeypatch.setattr(main, "get_law_snippets", fake_get_law_snippets, raising=True)
    monkeypatch.setattr(main, "_safe_ollama_invoke", fake_safe_invoke, raising=True)

    # Создаём временный текстовый файл с "тендером"
    temp_path = tmp_path / "tender_test.txt"
    temp_path.write_text("В случае просрочки поставки предусмотрен штраф 0.1% за каждый день.", encoding="utf-8")

    # Вызываем анализ
    result = await main.analyze_single_file(str(temp_path), temp_path.name, "UNIVERSAL")

    assert called["rag"] is True
    assert isinstance(result, dict)
    assert result.get("summary") == "Тестовый анализ"
    assert result.get("score") == 70
    assert result.get("passport", {}).get("fz") == "44-ФЗ"





