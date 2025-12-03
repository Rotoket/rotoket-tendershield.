"""
Rate Limiting для API эндпоинтов
"""

import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from typing import Callable

logger = logging.getLogger(__name__)

# Создаем лимитер
limiter = Limiter(key_func=get_remote_address)


def setup_rate_limiting(app):
    """Настраивает rate limiting для приложения"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("✅ Rate limiting настроен")


def get_user_identifier(request: Request) -> str:
    """Получает идентификатор пользователя для rate limiting"""
    # Пытаемся получить email из токена
    try:
        from fastapi.security import OAuth2PasswordBearer
        from auth import get_current_user
        from database import get_db
        from typing import Optional
        
        oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)
        token: Optional[str] = None
        if hasattr(request, 'headers'):
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if token:
            db = next(get_db())
            try:
                user = get_current_user(token, db)
                if user:
                    return f"user:{user.email}"
            except:
                pass
            finally:
                db.close()
    except Exception as e:
        pass
    
    # Иначе используем IP адрес
    return get_remote_address(request)


# Декораторы для разных типов эндпоинтов
def limit_analysis_requests(func: Callable):
    """Rate limit для анализа документов"""
    return limiter.limit("10/minute", key_func=get_user_identifier)(func)


def limit_chat_requests(func: Callable):
    """Rate limit для чата"""
    return limiter.limit("30/minute", key_func=get_user_identifier)(func)


def limit_api_requests(func: Callable):
    """Rate limit для общих API запросов"""
    return limiter.limit("100/minute", key_func=get_user_identifier)(func)

