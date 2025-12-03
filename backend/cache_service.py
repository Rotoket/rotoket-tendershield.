"""
Сервис кеширования результатов анализа
Использует Redis для кеширования (если доступен) или in-memory кеш
"""

import hashlib
import json
import logging
from typing import Optional, Dict, Any
from datetime import timedelta

logger = logging.getLogger(__name__)

# In-memory кеш (fallback если Redis недоступен)
_memory_cache: Dict[str, tuple] = {}  # {hash: (result, timestamp)}


def get_document_hash(file_content: bytes, filename: str = "") -> str:
    """
    Вычисляет хеш документа для кеширования
    
    Args:
        file_content: Содержимое файла
        filename: Имя файла (опционально)
        
    Returns:
        SHA256 хеш документа
    """
    content_hash = hashlib.sha256(file_content).hexdigest()
    if filename:
        filename_hash = hashlib.md5(filename.encode()).hexdigest()
        return f"{content_hash}:{filename_hash}"
    return content_hash


def get_cached_analysis(file_hash: str, industry: str = "UNIVERSAL") -> Optional[Dict[str, Any]]:
    """
    Получает закешированный результат анализа
    
    Args:
        file_hash: Хеш документа
        industry: Отрасль (для различения кешей)
        
    Returns:
        Результат анализа или None
    """
    cache_key = f"analysis:{file_hash}:{industry}"
    
    # Пытаемся использовать Redis
    try:
        import redis
        from config import settings
        
        redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 1),
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        cached = redis_client.get(cache_key)
        if cached:
            logger.info(f"✅ Найден кеш в Redis для {file_hash[:16]}...")
            return json.loads(cached)
    except (ImportError, Exception) as e:
        # Redis недоступен, используем in-memory кеш
        if cache_key in _memory_cache:
            result, timestamp = _memory_cache[cache_key]
            # Проверяем срок действия (24 часа для in-memory)
            from datetime import datetime
            if (datetime.now() - timestamp).total_seconds() < 86400:
                logger.info(f"✅ Найден кеш в памяти для {file_hash[:16]}...")
                return result
            else:
                # Удаляем устаревший кеш
                del _memory_cache[cache_key]
    
    return None


def cache_analysis(
    file_hash: str,
    result: Dict[str, Any],
    industry: str = "UNIVERSAL",
    ttl: int = 86400  # 24 часа
) -> None:
    """
    Сохраняет результат анализа в кеш
    
    Args:
        file_hash: Хеш документа
        result: Результат анализа
        industry: Отрасль
        ttl: Время жизни кеша в секундах
    """
    cache_key = f"analysis:{file_hash}:{industry}"
    
    # Пытаемся использовать Redis
    try:
        import redis
        from config import settings
        
        redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 1),
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(result, ensure_ascii=False)
        )
        logger.info(f"✅ Результат закеширован в Redis: {file_hash[:16]}...")
        return
    except (ImportError, Exception) as e:
        # Redis недоступен, используем in-memory кеш
        from datetime import datetime
        _memory_cache[cache_key] = (result, datetime.now())
        logger.info(f"✅ Результат закеширован в памяти: {file_hash[:16]}...")
        # Ограничиваем размер кеша (макс 100 записей)
        if len(_memory_cache) > 100:
            # Удаляем самую старую запись
            oldest_key = min(_memory_cache.keys(), key=lambda k: _memory_cache[k][1])
            del _memory_cache[oldest_key]


def clear_cache(file_hash: Optional[str] = None) -> None:
    """
    Очищает кеш
    
    Args:
        file_hash: Хеш документа (если None - очищает весь кеш)
    """
    if file_hash:
        # Очищаем конкретный документ
        patterns = [f"analysis:{file_hash}:*"]
    else:
        # Очищаем весь кеш
        patterns = ["analysis:*"]
    
    try:
        import redis
        from config import settings
        
        redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 1),
            decode_responses=True,
            socket_connect_timeout=2
        )
        
        for pattern in patterns:
            keys = redis_client.keys(pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"✅ Очищено {len(keys)} записей из Redis кеша")
    except (ImportError, Exception):
        # Очищаем in-memory кеш
        if file_hash:
            keys_to_delete = [k for k in _memory_cache.keys() if k.startswith(f"analysis:{file_hash}:")]
            for key in keys_to_delete:
                del _memory_cache[key]
        else:
            _memory_cache.clear()
        logger.info("✅ In-memory кеш очищен")

