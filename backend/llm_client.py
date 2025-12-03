from langchain_ollama import ChatOllama
import time
import logging
from typing import Optional

from config import settings

logger = logging.getLogger(__name__)


def get_analysis_llm() -> ChatOllama:
    """Return a ChatOllama client configured for structured JSON analysis.

    Uses a low temperature and JSON output format by default.
    """

    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.1,
        format="json",
        timeout=300,  # 5 минут таймаут
    )


def get_chat_llm() -> ChatOllama:
    """Return a ChatOllama client for general chat with default settings."""

    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        timeout=300,
    )


def invoke_with_retry(
    llm: ChatOllama,
    prompt: str,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    backoff_factor: float = 2.0
) -> str:
    """
    Вызывает LLM с повторными попытками при ошибках
    
    Args:
        llm: Экземпляр ChatOllama
        prompt: Промпт для отправки
        max_retries: Максимальное количество попыток
        retry_delay: Начальная задержка между попытками (секунды)
        backoff_factor: Множитель для увеличения задержки
        
    Returns:
        Содержимое ответа от LLM
        
    Raises:
        Exception: Если все попытки исчерпаны
    """
    last_error = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Попытка {attempt + 1}/{max_retries} вызова Ollama...")
            response = llm.invoke(prompt)
            content = response.content
            
            if content and len(content) > 10:  # Проверка на валидный ответ
                logger.info(f"✅ Успешный ответ от Ollama (попытка {attempt + 1})")
                return content
            else:
                raise ValueError("Пустой или слишком короткий ответ от Ollama")
                
        except Exception as e:
            last_error = e
            error_msg = str(e)
            logger.warning(f"⚠️ Попытка {attempt + 1} не удалась: {error_msg[:100]}")
            
            # Не повторяем при определенных ошибках
            if "CUDA" in error_msg or "memory" in error_msg.lower():
                logger.error("Ошибка памяти GPU - не повторяем")
                raise
            
            if attempt < max_retries - 1:
                delay = retry_delay * (backoff_factor ** attempt)
                logger.info(f"Повтор через {delay:.1f} секунд...")
                time.sleep(delay)
            else:
                logger.error(f"❌ Все {max_retries} попыток исчерпаны")
    
    # Если все попытки не удались
    raise Exception(f"Не удалось получить ответ от Ollama после {max_retries} попыток: {last_error}")
