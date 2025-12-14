# 📋 ДЕНЬ 1: DOCKER + ENV SETUP (15 минут на запуск)

## ШАГ 1: Создай `docker-compose.yml` в корне проекта

```yaml
version: '3.9'

services:
  # PostgreSQL 16
  postgres:
    image: postgres:16-alpine
    container_name: tender_postgres
    environment:
      POSTGRES_USER: tender_user
      POSTGRES_PASSWORD: tender_pass_dev
      POSTGRES_DB: tender_shield
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U tender_user -d tender_shield"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - tender_network

  # Ollama (LLM сервис)
  ollama:
    image: ollama/ollama:latest
    container_name: tender_ollama
    ports:
      - "11434:11434"
    environment:
      OLLAMA_HOST: 0.0.0.0:11434
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - tender_network
    # GPU поддержка (раскомментируй если есть NVIDIA GPU)
    # deploy:
    #   resources:
    #     reservations:
    #       devices:
    #         - driver: nvidia
    #           count: 1
    #           capabilities: [gpu]

  # Backend (FastAPI)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: tender_backend
    ports:
      - "8000:8000"
    environment:
      # Database
      TENDER_DB_USER: tender_user
      TENDER_DB_PASSWORD: tender_pass_dev
      TENDER_DB_HOST: postgres
      TENDER_DB_PORT: 5432
      TENDER_DB_NAME: tender_shield
      
      # LLM
      TENDER_OLLAMA_BASE_URL: http://ollama:11434
      TENDER_OLLAMA_MODEL: llama2
      
      # JWT
      TENDER_SECRET_KEY: dev_secret_key_change_in_production_12345678901234567890
      TENDER_ALGORITHM: HS256
      TENDER_ACCESS_TOKEN_EXPIRE_MINUTES: 43200
      
      # Email (Gmail)
      TENDER_SMTP_HOST: smtp.gmail.com
      TENDER_SMTP_PORT: 587
      TENDER_SMTP_USER: ${SMTP_USER:-noreply@tendershield.pro}
      TENDER_SMTP_PASSWORD: ${SMTP_PASSWORD:-dev_password}
      TENDER_SMTP_FROM: ${SMTP_FROM:-noreply@tendershield.pro}
      
      # Payment (YooKassa)
      TENDER_YOOKASSA_SHOP_ID: ${YOOKASSA_SHOP_ID:-test_shop_id}
      TENDER_YOOKASSA_SECRET_KEY: ${YOOKASSA_SECRET_KEY:-test_secret_key}
      TENDER_YOOKASSA_TEST_MODE: "true"
      
      # Server
      TENDER_API_HOST: 0.0.0.0
      TENDER_API_PORT: 8000
      
      # CORS
      TENDER_CORS_ORIGINS: "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    
    depends_on:
      postgres:
        condition: service_healthy
      ollama:
        condition: service_started
    
    volumes:
      - ./backend:/app
      - /app/__pycache__
    
    networks:
      - tender_network
    
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend (React + Vite)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    container_name: tender_frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_URL: http://localhost:8000
    volumes:
      - ./frontend/src:/app/src
      - /app/node_modules
    networks:
      - tender_network
    command: npm run dev -- --host

volumes:
  postgres_data:
  ollama_data:

networks:
  tender_network:
    driver: bridge
```

## ШАГ 2: Создай `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Зависимости для PDF, DOCX чтения
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python зависимости
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## ШАГ 3: Создай `frontend/Dockerfile.dev`

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY frontend/package*.json .
RUN npm install

COPY frontend .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

## ШАГ 4: Создай `.env.example`

```env
# ═══════════════════════════════════════════════════════════════
# БАЗА ДАННЫХ (PostgreSQL)
# ═══════════════════════════════════════════════════════════════
TENDER_DB_USER=tender_user
TENDER_DB_PASSWORD=tender_pass_dev
TENDER_DB_HOST=localhost
TENDER_DB_PORT=5432
TENDER_DB_NAME=tender_shield

# ═══════════════════════════════════════════════════════════════
# БЕЗОПАСНОСТЬ (JWT)
# ═══════════════════════════════════════════════════════════════
# Команда для генерации: python -c "import secrets; print(secrets.token_urlsafe(64))"
TENDER_SECRET_KEY=dev_secret_key_change_in_production_12345678901234567890
TENDER_ALGORITHM=HS256
TENDER_ACCESS_TOKEN_EXPIRE_MINUTES=43200

# ═══════════════════════════════════════════════════════════════
# OLLAMA (LLM)
# ═══════════════════════════════════════════════════════════════
TENDER_OLLAMA_BASE_URL=http://localhost:11434
TENDER_OLLAMA_MODEL=llama2
# Альтернативные модели (если есть):
# mistral, qwen:0.5b, neural-chat

# ═══════════════════════════════════════════════════════════════
# EMAIL (SMTP)
# ═══════════════════════════════════════════════════════════════
TENDER_SMTP_HOST=smtp.gmail.com
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=your_email@gmail.com
TENDER_SMTP_PASSWORD=your_app_password
TENDER_SMTP_FROM=noreply@tendershield.pro
TENDER_SMTP_USE_TLS=true

# ═══════════════════════════════════════════════════════════════
# YOOKASSA (ПЛАТЕЖИ)
# ═══════════════════════════════════════════════════════════════
# Для разработки используй тестовые ключи
TENDER_YOOKASSA_SHOP_ID=test_shop_id
TENDER_YOOKASSA_SECRET_KEY=test_secret_key
TENDER_YOOKASSA_TEST_MODE=true

# ═══════════════════════════════════════════════════════════════
# СЕРВЕР
# ═══════════════════════════════════════════════════════════════
TENDER_API_HOST=0.0.0.0
TENDER_API_PORT=8000

# ═══════════════════════════════════════════════════════════════
# CORS (для фронтенда)
# ═══════════════════════════════════════════════════════════════
TENDER_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000

# ═══════════════════════════════════════════════════════════════
# REDIS (опционально, для кеширования)
# ═══════════════════════════════════════════════════════════════
TENDER_REDIS_HOST=localhost
TENDER_REDIS_PORT=6379
TENDER_REDIS_DB=1
```

## ШАГ 5: Создай `backend/init_db.sql`

```sql
-- Инициализация БД с нужной кодировкой
CREATE DATABASE tender_shield 
  ENCODING 'UTF8' 
  LOCALE 'C'
  TEMPLATE template0;

COMMENT ON DATABASE tender_shield IS 'Tender Shield - AI analysis of tenders';
```

## ШАГ 6: Запуск (одна команда!)

```bash
# Копируй .env.example в .env
cp .env.example .env

# Стартуй контейнеры
docker-compose up -d

# Подожди 30 сек, потом инициализируй БД
docker-compose exec -T postgres psql -U tender_user -d tender_shield < backend/init_db.sql

# Применить миграции (если используешь Alembic)
docker-compose exec backend alembic upgrade head

# Проверка здоровья
curl http://localhost:8000/api/health

# Frontend откроется на http://localhost:5173
```

---

## ВАЖНОЕ: Инициализация Ollama с нужной моделью

После запуска контейнера, Ollama нужно скачать модель:

```bash
# Внутри контейнера Ollama
docker-compose exec ollama ollama pull llama2

# Или через API (после инициализации)
curl -X POST http://localhost:11434/api/pull -d '{"name":"llama2"}'
```

Модель llama2 будет скачана (~3.8 GB) при первом запуске.

---

## ПРОВЕРКА: ВСЕ ЛИ РАБОТАЕТ?

### Тест 1: PostgreSQL
```bash
docker-compose exec postgres psql -U tender_user -d tender_shield -c "SELECT version();"
```

### Тест 2: Ollama
```bash
curl http://localhost:11434/api/tags
# Должно вернуть список доступных моделей
```

### Тест 3: Backend API
```bash
curl http://localhost:8000/api/health
# Должно вернуть { "status": "ok" }
```

### Тест 4: Frontend
```bash
# Откройся в браузере
http://localhost:5173
```

---

## ОЧИСТКА И ПЕРЕЗАГРУЗКА

```bash
# Остановить контейнеры
docker-compose down

# Полная очистка (с удалением volumes)
docker-compose down -v

# Пересоздать всё с нуля
docker-compose up --build -d
```

---

## TROUBLESHOOTING

### "Connection refused" на PostgreSQL
```bash
# Проверить логи
docker-compose logs postgres

# Перезагрузить PostgreSQL
docker-compose restart postgres
```

### Ollama не скачивает модель
```bash
# Увеличить timeout
docker-compose exec ollama ollama pull llama2 --timeout 600

# Проверить интернет соединение внутри контейнера
docker-compose exec ollama ping 8.8.8.8
```

### Backend не подключается к БД
```bash
# Проверить что PostgreSQL запущен
docker-compose ps

# Посмотреть логи Backend
docker-compose logs backend

# Убедиться, что порт 5432 свободен
netstat -an | grep 5432
```

**Все готово! Система запустится за 15 минут на чистой машине. 🚀**
