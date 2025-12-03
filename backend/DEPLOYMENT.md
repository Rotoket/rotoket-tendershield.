# Руководство по развертыванию Tender Shield Pro

## Предварительные требования

### Backend
- Python 3.10 или выше
- pip
- Ollama установлен и запущен (по умолчанию на `http://localhost:11434`)

### Frontend
- Node.js 18 или выше
- npm или yarn

## Установка Ollama

### Windows
1. Скачайте установщик с https://ollama.ai
2. Установите Ollama
3. Запустите Ollama
4. Загрузите модель:
```bash
ollama pull qwen2.5-coder:7b
```

### Linux/Mac
```bash
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5-coder:7b
```

## Развертывание Backend (без Docker)

### 1. Настройка окружения

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
.\venv\Scripts\Activate.ps1  # Windows PowerShell
```

### 2. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 3. Конфигурация

Создайте файл `.env` в папке `backend`:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
TENDER_OLLAMA_BASE_URL=http://localhost:11434
TENDER_OLLAMA_MODEL=qwen2.5-coder:7b
TENDER_API_HOST=0.0.0.0
TENDER_API_PORT=8000
```

### 4. Запуск

#### Режим разработки
```bash
python main.py
```

#### Production режим (через uvicorn)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### Production с gunicorn (рекомендуется)
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Развертывание Frontend (без Docker)

### 1. Установка зависимостей

```bash
cd frontend
npm install
```

### 2. Конфигурация

Создайте файл `.env` в папке `frontend`:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
VITE_API_URL=http://localhost:8000/api
```

Если backend на другом хосте, укажите правильный URL.

### 3. Запуск

#### Режим разработки
```bash
npm run dev
```

#### Production сборка
```bash
npm run build
```

Собранные файлы будут в папке `dist/`. Для развертывания используйте любой веб-сервер (nginx, Apache, и т.д.).

### 4. Развертывание на nginx (без Docker)

Пример конфигурации nginx:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/tender-shield-pro/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Docker / Docker Compose (рекомендуемый способ для сервера)

В репозитории уже подготовлены:

- `backend/Dockerfile` — как собирать образ backend;
- `frontend/Dockerfile` — как собирать образ frontend + nginx;
- `infra/docker-compose.yml` — как запускать всё вместе (PostgreSQL, ChromaDB, backend, frontend);
- `infra/nginx.conf` — конфигурация nginx внутри frontend-контейнера.

### 1. Предварительные шаги на сервере

1. Установите Docker и Docker Compose (обычно это пакет `docker` и `docker-compose-plugin` в репозитории вашего дистрибутива Linux).  
2. Скопируйте весь проект `tender-shield-pro` на сервер (через `git clone` или SFTP).
3. Убедитесь, что на сервере установлен и запущен Ollama, и он доступен по порту `11434`:
   ```bash
   ollama serve
   ```
   По умолчанию backend в Docker будет ходить к Ollama по адресу `http://host.docker.internal:11434`.

### 2. Запуск через docker-compose

1. Подключитесь к серверу по SSH.
2. Перейдите в папку `infra` внутри проекта:
   ```bash
   cd tender-shield-pro/infra
   ```
3. Запустите сборку и старт всех сервисов:
   ```bash
   docker compose up -d --build
   ```
   Это поднимет:
   - PostgreSQL (`db`);
   - ChromaDB (`chromadb`);
   - backend (`tender_backend`);
   - frontend + nginx (`tender_frontend`).

4. Проверьте, что контейнеры запустились:
   ```bash
   docker ps
   ```

5. Откройте в браузере адрес сервера (по умолчанию `http://<ip-сервера>/`) — вы должны увидеть интерфейс TenderShield.

### 3. Переменные окружения для продакшена

В `infra/docker-compose.yml` уже заданы базовые значения:

- База данных:
  - `POSTGRES_DB=tender`
  - `POSTGRES_USER=tender_user`
  - `POSTGRES_PASSWORD=tender_password`
- Backend:
  - `DATABASE_URL=postgresql+psycopg2://tender_user:tender_password@db:5432/tender`
  - `TENDER_OLLAMA_BASE_URL=http://host.docker.internal:11434`
  - `TENDER_OLLAMA_MODEL=qwen2.5-coder:7b`

**Рекомендуется** для продакшена вынести пароли и секреты в отдельный `.env` файл и подключать его в `docker-compose.yml` через ключ `env_file`, чтобы не оставлять чувствительные данные в репозитории.

## Переменные окружения

### Backend

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `TENDER_OLLAMA_BASE_URL` | URL Ollama сервера | `http://localhost:11434` |
| `TENDER_OLLAMA_MODEL` | Модель Ollama | `qwen2.5-coder:7b` |
| `TENDER_API_HOST` | Хост API сервера | `0.0.0.0` |
| `TENDER_API_PORT` | Порт API сервера | `8000` |
| `DATABASE_URL` | URL подключения к базе данных | `sqlite:///./tender.db` (по умолчанию) |
| `SECRET_KEY` | Секретный ключ для JWT | **обязательно переопределить в продакшене** |

### Frontend

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `VITE_API_URL` | URL backend API | `http://localhost:8000/api` |

## Проверка работоспособности

### Backend
```bash
curl http://localhost:8000/docs
```

Должна открыться документация Swagger.

### Frontend
Откройте `http://localhost:5173` в браузере.

## Безопасность

- Используйте HTTPS в production
- Настройте CORS правильно для вашего домена (в `settings.CORS_ORIGINS` или через переменные окружения)
- Храните секреты в переменных окружения, не в коде
- Регулярно обновляйте зависимости
- Настройте firewall для ограничения доступа

### Пример базовой схемы HTTPS

Самый простой вариант для HTTPS:

1. На сервере поднять внешний nginx (или использовать nginx от хостинга) c сертификатом Let’s Encrypt.  
2. Настроить этот внешний nginx так, чтобы он:
   - принимал HTTPS-запросы от пользователей;
   - проксировал их внутрь на `http://127.0.0.1:80` (frontend-контейнер).

В этом случае:

- Внутренний nginx в контейнере (`infra/nginx.conf`) остаётся простым и работает только по HTTP;
- Внешний nginx занимается SSL/сертификатами и может автоматически обновлять их через Certbot.

## Мониторинг

Рекомендуется настроить:
- Логирование (например, через logging в Python)
- Мониторинг производительности
- Алерты при ошибках

## Поддержка

При возникновении проблем:
1. Проверьте логи backend и frontend
2. Убедитесь, что Ollama запущен и доступен
3. Проверьте конфигурацию `.env` файлов
4. Убедитесь, что все порты свободны


