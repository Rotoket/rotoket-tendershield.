# План развёртывания Tender Shield Pro (черновик)

## 1. Цели

- Развернуть Tender Shield Pro как SaaS:
  - Backend: FastAPI (анализ документов, авторизация, тарифы, интеграции).
  - Frontend: React/Vite (единый экран анализа, хаб, калькулятор, история).
  - LLM: локальная модель `qwen2.5-coder:7b` через Ollama.
  - База данных: PostgreSQL (пользователи, тарифы, история анализов, usage).
  - Хранилище файлов: локальный volume или S3-совместимое хранилище.
- Цель первого этапа: комфортная работа 1–5 одновременных пользователей, возможность масштабирования позже.

## 2. Архитектура сервисов

### 2.1. Компоненты

1. **LLM/AI-нода (GPU)**
   - Ollama + модель `qwen2.5-coder:7b`.
   - REST API на `http://ollama:11434` (доступен только из внутренней сети инфраструктуры).

2. **Backend-нода (API)**
   - Контейнер с FastAPI-приложением (`backend/`).
   - Подключается к:
     - PostgreSQL (через переменные окружения `TENDER_DB_*`).
     - Ollama (через `TENDER_OLLAMA_BASE_URL`).
   - Отдаёт REST API `/api/...` и статику (опционально).

3. **Frontend-нода**
   - Сборка React/Vite (`frontend/`) в статику.
   - Nginx (или любой web-сервер) для раздачи статики и проксирования запросов `/api` на Backend-ноду.

4. **PostgreSQL**
   - Отдельный managed‑инстанс или ВМ.
   - Используется для хранения пользователей, тарифов, истории анализов, usage, пакетных анализов.

5. **Хранилище файлов**
   - На первом этапе можно использовать локальный диск Backend-ноды.
   - В перспективе — S3-совместимое хранилище (Timeweb Object Storage) для долгосрочного хранения документов.

### 2.2. Сетевое взаимодействие

- `Frontend` → `Backend`: HTTP/HTTPS (`/api/...`).
- `Backend` → `PostgreSQL`: TCP (порт 5432 или custom).
- `Backend` → `Ollama`: HTTP (по `TENDER_OLLAMA_BASE_URL`).
- Внешний мир → `Frontend`: HTTPS (через домен, например `app.tendershield.pro`).

## 3. Рекомендуемые ресурсы (Timeweb Cloud, ориентировочно)

### 3.1. GPU-нода (Ollama + LLM)

- **Назначение**: запуск Ollama и модели `qwen2.5-coder:7b`.
- **Минимальные рекомендации**:
  - GPU: 16 ГБ VRAM (лучше 24 ГБ для запаса по параллельным запросам).
  - CPU: 4–8 vCPU.
  - RAM: 16–32 ГБ.
  - Диск: 100–200 ГБ SSD (для модели, логов, кеша анализов).
- На Timeweb Cloud это может быть любой GPU‑сервер уровня RTX A5000 / RTX 4090 / A30 или аналогичный с 16–24 ГБ VRAM.

### 3.2. Backend-нода (API + Nginx)

- **Назначение**: FastAPI-приложение, прокси для Ollama (опционально), отдача статики (опционально).
- **Минимальные рекомендации**:
  - CPU: 2–4 vCPU.
  - RAM: 4–8 ГБ.
  - Диск: 50–100 ГБ SSD.
- Можно совместить Backend и Frontend в одном контейнере/ВМ или держать статику на отдельной VDS.

### 3.3. PostgreSQL-нода

- **Назначение**: основная БД сервиса.
- **Минимальные рекомендации**:
  - CPU: 2–4 vCPU.
  - RAM: 8–16 ГБ.
  - Диск: 100+ ГБ SSD (зависит от объёма истории и логов).
- Для надёжности:
  - включить резервное копирование БД;
  - настроить мониторинг по диску/CPU/RAM.

## 4. Переменные окружения и конфигурация

### 4.1. Backend (`backend/config.py` / `.env`)

Ключевые переменные (с префиксом `TENDER_`):

- LLM/Ollama:
  - `TENDER_OLLAMA_BASE_URL=http://ollama:11434`
  - `TENDER_OLLAMA_MODEL=qwen2.5-coder:7b`
- API:
  - `TENDER_API_HOST=0.0.0.0`
  - `TENDER_API_PORT=8000`
  - `TENDER_CORS_ORIGINS=["https://app.tendershield.pro"]`
- БД:
  - `TENDER_DB_USER=...`
  - `TENDER_DB_PASSWORD=...`
  - `TENDER_DB_HOST=...`
  - `TENDER_DB_PORT=5432`
  - `TENDER_DB_NAME=tender_shield`
- JWT:
  - `TENDER_SECRET_KEY=<случайная_строка_32+ символа>`
  - `TENDER_ALGORITHM=HS256`
  - `TENDER_ACCESS_TOKEN_EXPIRE_MINUTES=43200` (30 дней) или по желанию.
- Платежи (Yookassa):
  - `TENDER_YOOKASSA_SHOP_ID=...`
  - `TENDER_YOOKASSA_SECRET_KEY=...`
  - `TENDER_YOOKASSA_TEST_MODE=true/false`
- SMTP (опционально, для писем):
  - `TENDER_SMTP_HOST=...`
  - `TENDER_SMTP_PORT=587`
  - `TENDER_SMTP_USER=...`
  - `TENDER_SMTP_PASSWORD=...`
  - `TENDER_SMTP_FROM=noreply@tendershield.pro`

### 4.2. Frontend

- Базовый URL API в `.env` фронтенда:
  - `VITE_API_BASE_URL=https://app.tendershield.pro/api`
- CORS и HTTPS должны совпадать с конфигурацией Backend.

## 5. Пошаговый план деплоя

1. **Подготовить Docker-образы**
   - Собрать образ `backend` (FastAPI + зависимости).
   - Собрать образ `frontend` (сборка статики + Nginx-конфиг).

2. **Развернуть PostgreSQL**
   - Создать managed‑инстанс или ВМ с Postgres.
   - Настроить пользователя и БД `tender_shield`.
   - Прописать `TENDER_DB_*` на Backend‑ноде.

3. **Развернуть Ollama на GPU-нODE**
   - Установить Docker и Ollama (или только Ollama, если без Docker).
   - Скачать модель: `ollama pull qwen2.5-coder:7b`.
   - Запустить Ollama-сервис, убедиться, что `/api/tags` доступен.

4. **Развернуть Backend**
   - Поднять контейнер FastAPI с нужными `TENDER_...` переменными.
   - Прогнать инициализацию БД (автоматически через `init_db()` при старте).

5. **Развернуть Frontend**
   - Залить статическую сборку на Nginx/веб‑сервер.
   - Настроить прокси `/api` → Backend.
   - Включить HTTPS (Let’s Encrypt или платный сертификат).

6. **Настроить домен и DNS**
   - Привязать домен (например, `app.tendershield.pro`) к Frontend-нODE.
   - Проверить доступность фронта и API через браузер.

7. **Мониторинг и логирование**
   - Включить сбор логов FastAPI и Ollama.
   - Настроить алерты по:
     - загрузке GPU;
     - ошибкам 5xx в Backend;
     - дисковому пространству БД.

## 6. Дальнейшее масштабирование

- При росте нагрузки:
  - добавить вторую GPU-ноду с Ollama и балансировать запросы LLM;
  - вынести Celery/фоновый воркер для тяжёлых анализов и генераций документов;
  - увеличить лимиты Postgres (vCPU, RAM, диск).

- Для стабильности:
  - настроить регулярные бэкапы БД;
  - хранить конфигурацию в Git (Docker-compose / Helm / Terraform).
