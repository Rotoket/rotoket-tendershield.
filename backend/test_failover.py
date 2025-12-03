"""
Тесты для системы failover (отказоустойчивости) LLM через Ollama
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import HTTPException
from langchain_ollama import ChatOllama

# Импортируем функцию для тестирования
from main import _safe_ollama_invoke, OLLAMA_MODELS


class TestSafeOllamaInvoke:
    """Тесты для функции _safe_ollama_invoke"""
    
    def test_success_first_model(self):
        """Тест успешного вызова с первой моделью"""
        prompt = "Тестовый промпт"
        expected_response = '{"result": "success"}'
        
        # Мокаем ChatOllama
        mock_response = MagicMock()
        mock_response.content = expected_response
        
        with patch('main.ChatOllama') as mock_chat_ollama:
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.return_value = mock_response
            mock_chat_ollama.return_value = mock_llm_instance
            
            # Вызываем функцию
            result = _safe_ollama_invoke(prompt, format_json=True)
            
            # Проверяем результат
            assert result == expected_response
            # Проверяем, что использовалась первая модель
            mock_chat_ollama.assert_called_once()
            call_kwargs = mock_chat_ollama.call_args[1]
            assert call_kwargs['model'] == OLLAMA_MODELS[0]
            assert call_kwargs['format'] == 'json'
    
    def test_failover_to_second_model(self):
        """Тест переключения на вторую модель при ошибке первой"""
        prompt = "Тестовый промпт"
        expected_response = '{"result": "success from second model"}'
        
        mock_response = MagicMock()
        mock_response.content = expected_response
        
        with patch('main.ChatOllama') as mock_chat_ollama:
            # Первая модель падает с ошибкой
            # Вторая модель успешно отвечает
            mock_llm_instance_fail = MagicMock()
            mock_llm_instance_fail.invoke.side_effect = Exception("Connection error")
            
            mock_llm_instance_success = MagicMock()
            mock_llm_instance_success.invoke.return_value = mock_response
            
            # Настраиваем мок так, чтобы первая попытка падала, вторая успешна
            call_count = 0
            def chat_ollama_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return mock_llm_instance_fail
                else:
                    return mock_llm_instance_success
            
            mock_chat_ollama.side_effect = chat_ollama_side_effect
            
            # Вызываем функцию
            result = _safe_ollama_invoke(prompt, format_json=True)
            
            # Проверяем результат
            assert result == expected_response
            # Проверяем, что было 2 попытки (первая упала, вторая успешна)
            assert mock_chat_ollama.call_count == 2
            # Проверяем, что использовались правильные модели
            first_call_model = mock_chat_ollama.call_args_list[0][1]['model']
            second_call_model = mock_chat_ollama.call_args_list[1][1]['model']
            assert first_call_model == OLLAMA_MODELS[0]
            assert second_call_model == OLLAMA_MODELS[1]
    
    def test_failover_to_third_model(self):
        """Тест переключения на третью модель при ошибке первых двух"""
        prompt = "Тестовый промпт"
        expected_response = '{"result": "success from third model"}'
        
        mock_response = MagicMock()
        mock_response.content = expected_response
        
        with patch('main.ChatOllama') as mock_chat_ollama:
            # Первые две модели падают, третья успешна
            mock_llm_instance_fail = MagicMock()
            mock_llm_instance_fail.invoke.side_effect = Exception("Connection error")
            
            mock_llm_instance_success = MagicMock()
            mock_llm_instance_success.invoke.return_value = mock_response
            
            call_count = 0
            def chat_ollama_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    return mock_llm_instance_fail
                else:
                    return mock_llm_instance_success
            
            mock_chat_ollama.side_effect = chat_ollama_side_effect
            
            # Вызываем функцию
            result = _safe_ollama_invoke(prompt, format_json=True)
            
            # Проверяем результат
            assert result == expected_response
            # Проверяем, что было 3 попытки
            assert mock_chat_ollama.call_count == 3
            # Проверяем, что использовались все три модели
            models_used = [call[1]['model'] for call in mock_chat_ollama.call_args_list]
            assert models_used == OLLAMA_MODELS
    
    def test_all_models_fail(self):
        """Тест что при падении всех моделей выбрасывается HTTPException 503"""
        prompt = "Тестовый промпт"
        
        with patch('main.ChatOllama') as mock_chat_ollama:
            # Все модели падают
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.side_effect = Exception("Connection error")
            mock_chat_ollama.return_value = mock_llm_instance
            
            # Вызываем функцию и ожидаем HTTPException
            with pytest.raises(HTTPException) as exc_info:
                _safe_ollama_invoke(prompt, format_json=True)
            
            # Проверяем статус код
            assert exc_info.value.status_code == 503
            assert "Все AI-сервисы недоступны" in exc_info.value.detail
            # Проверяем, что были попытки со всеми моделями
            assert mock_chat_ollama.call_count == len(OLLAMA_MODELS)
    
    def test_empty_response_handling(self):
        """Тест обработки пустого ответа (переключение на следующую модель)"""
        prompt = "Тестовый промпт"
        expected_response = '{"result": "valid response"}'
        
        mock_response_empty = MagicMock()
        mock_response_empty.content = ""  # Пустой ответ
        
        mock_response_valid = MagicMock()
        mock_response_valid.content = expected_response
        
        with patch('main.ChatOllama') as mock_chat_ollama:
            call_count = 0
            def chat_ollama_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    instance = MagicMock()
                    instance.invoke.return_value = mock_response_empty
                    return instance
                else:
                    instance = MagicMock()
                    instance.invoke.return_value = mock_response_valid
                    return instance
            
            mock_chat_ollama.side_effect = chat_ollama_side_effect
            
            # Вызываем функцию
            result = _safe_ollama_invoke(prompt, format_json=True)
            
            # Проверяем, что использовалась вторая модель
            assert result == expected_response
            assert mock_chat_ollama.call_count == 2
    
    def test_short_response_handling(self):
        """Тест обработки слишком короткого ответа (переключение на следующую модель)"""
        prompt = "Тестовый промпт"
        expected_response = '{"result": "valid long response"}'
        
        mock_response_short = MagicMock()
        mock_response_short.content = "123"  # Слишком короткий (< 10 символов)
        
        mock_response_valid = MagicMock()
        mock_response_valid.content = expected_response
        
        with patch('main.ChatOllama') as mock_chat_ollama:
            call_count = 0
            def chat_ollama_side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    instance = MagicMock()
                    instance.invoke.return_value = mock_response_short
                    return instance
                else:
                    instance = MagicMock()
                    instance.invoke.return_value = mock_response_valid
                    return instance
            
            mock_chat_ollama.side_effect = chat_ollama_side_effect
            
            # Вызываем функцию
            result = _safe_ollama_invoke(prompt, format_json=True)
            
            # Проверяем, что использовалась вторая модель
            assert result == expected_response
            assert mock_chat_ollama.call_count == 2
    
    def test_chat_mode_without_json(self):
        """Тест режима чата без JSON формата"""
        prompt = "Привет, как дела?"
        expected_response = "Привет! У меня всё отлично, спасибо!"
        
        mock_response = MagicMock()
        mock_response.content = expected_response
        
        with patch('main.ChatOllama') as mock_chat_ollama:
            mock_llm_instance = MagicMock()
            mock_llm_instance.invoke.return_value = mock_response
            mock_chat_ollama.return_value = mock_llm_instance
            
            # Вызываем функцию с format_json=False
            result = _safe_ollama_invoke(prompt, format_json=False)
            
            # Проверяем результат
            assert result == expected_response
            # Проверяем, что format не был передан (или не был 'json')
            call_kwargs = mock_chat_ollama.call_args[1]
            assert 'format' not in call_kwargs or call_kwargs.get('format') != 'json'
    
    def test_temperature_setting(self):
        """Тест что temperature установлен в 0.1"""
        prompt = "Тестовый промпт"
        
        with patch('main.ChatOllama') as mock_chat_ollama:
            mock_llm_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.content = '{"result": "success"}'
            mock_llm_instance.invoke.return_value = mock_response
            mock_chat_ollama.return_value = mock_llm_instance
            
            _safe_ollama_invoke(prompt, format_json=True)
            
            # Проверяем, что temperature установлен
            call_kwargs = mock_chat_ollama.call_args[1]
            assert call_kwargs['temperature'] == 0.1
    
    def test_timeout_setting(self):
        """Тест что timeout установлен в 300 секунд"""
        prompt = "Тестовый промпт"
        
        with patch('main.ChatOllama') as mock_chat_ollama:
            mock_llm_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.content = '{"result": "success"}'
            mock_llm_instance.invoke.return_value = mock_response
            mock_chat_ollama.return_value = mock_llm_instance
            
            _safe_ollama_invoke(prompt, format_json=True)
            
            # Проверяем, что timeout установлен
            call_kwargs = mock_chat_ollama.call_args[1]
            assert call_kwargs['timeout'] == 300


if __name__ == "__main__":
    pytest.main([__file__, "-v"])





