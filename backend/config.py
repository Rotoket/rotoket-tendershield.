from pydantic_settings import BaseSettings
from typing import List
import json
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Prefix: TENDER_
    Example:
      TENDER_OLLAMA_BASE_URL=http://ollama-server:11434
      TENDER_OLLAMA_MODEL=qwen2.5-coder:7b
    """

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:0.5b"  # Легкая модель для слабых систем. Для лучшего качества используйте: qwen2.5-coder:7b

    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # Frontend dev origins (Vite default ports etc.)
    # Включаем оба порта, на которых может работать Vite dev server
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    def model_post_init(self, __context) -> None:
        """Обработка CORS_ORIGINS после инициализации модели."""
        # Если CORS_ORIGINS задан как JSON-строка в env, парсим её
        cors_env = os.getenv("TENDER_CORS_ORIGINS")
        if cors_env:
            cors_env = cors_env.strip()
            if cors_env.startswith("["):
                # JSON формат
                try:
                    parsed = json.loads(cors_env)
                    if isinstance(parsed, list):
                        self.CORS_ORIGINS = parsed
                except json.JSONDecodeError:
                    pass  # Используем значение по умолчанию
            elif "," in cors_env:
                # Формат через запятую
                self.CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",") if origin.strip()]

    # Database settings
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "tender_shield"

    # JWT settings
    SECRET_KEY: str = "your-secret-key-change-in-production"  # В продакшене использовать переменную окружения!
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30 * 24 * 60  # 30 дней

    # Payment settings (Yandex Kassa)
    YOOKASSA_SHOP_ID: str = ""  # ID магазина в Yandex Kassa
    YOOKASSA_SECRET_KEY: str = ""  # Секретный ключ Yandex Kassa
    YOOKASSA_TEST_MODE: bool = True  # Тестовый режим

    # Email settings (SMTP)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""  # Email для отправки
    SMTP_PASSWORD: str = ""  # Пароль приложения
    SMTP_FROM: str = "noreply@tendershield.pro"
    SMTP_USE_TLS: bool = True
    
    # Frontend URL для ссылок в email
    FRONTEND_URL: str = "http://localhost:5173"  # Для продакшена заменить на реальный домен

    # Redis settings (для кеширования, опционально)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1  # БД для кеша

    # MCP settings (Model Context Protocol - справочный слой)
    MCP_ENABLED: bool = True  # Включить/выключить MCP
    MCP_BASE_URL: str = ""  # URL внешнего MCP-сервера (если используется)
    MCP_TOKEN: str = ""  # Токен для аутентификации (если требуется)
    MCP_CONTENT_PATH: str = "mcp-content"  # Путь к локальным файлам контента

    model_config = {
        "env_prefix": "TENDER_",
        "env_file": ".env"
    }


settings = Settings()
