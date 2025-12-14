# 🐳 Docker Setup для Tender Shield Pro

## Быстрый старт (15 минут)

### Предварительные требования
- Docker и Docker Compose установлены
- Ollama установлен и запущен на хосте (порт 11434)
- Модель `qwen2.5-coder:7b` загружена в Ollama

### Шаг 1: Настройка переменных окружения

Скопируйте пример файла окружения:
```bash
cp backend/env.example backend/.env
```

Отредактируйте `backend/.env` и укажите:
- `TENDER_SECRET_KEY` - сгенерируйте случайный ключ (минимум 32 символа)
- `TENDER_SMTP_USER` и `TENDER_SMTP_PASSWORD` - для отправки email
- Остальные настройки можно оставить по умолчанию для разработки

### Шаг 2: Запуск контейнеров

```bash
cd infra
docker-compose up -d
```

Это запустит:
- PostgreSQL (порт 5432)
- ChromaDB (порт 8001)
- Backend API (порт 8000)
- Frontend (порт 80)

### Шаг 3: Инициализация базы данных

Подождите 10-15 секунд, пока контейнеры запустятся, затем:

```bash
# Инициализация БД (создание таблиц и тарифов)
docker-compose exec backend python init_db.py
```

### Шаг 4: Проверка работы

**Backend API:**
```bash
curl http://localhost:8000/api/health
# Должно вернуть: {"status":"ok"}
```

**Frontend:**
Откройте в браузере: http://localhost

**ChromaDB:**
```bash
curl http://localhost:8001/api/v1/heartbeat
```

### Шаг 5: Загрузка модели Ollama (если еще не загружена)

```bash
ollama pull qwen2.5-coder:7b
```

---

## Структура Docker Compose

```
infra/
├── docker-compose.yml    # Конфигурация всех сервисов
└── nginx.conf            # Конфигурация Nginx для frontend
```

**Сервисы:**
- `db` - PostgreSQL 15
- `chromadb` - ChromaDB для векторного поиска
- `backend` - FastAPI приложение
- `frontend` - React приложение (Nginx)

---

## Полезные команды

### Просмотр логов
```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend
```

### Остановка
```bash
docker-compose down
```

### Полная очистка (с удалением данных)
```bash
docker-compose down -v
```

### Пересборка после изменений
```bash
docker-compose up --build -d
```

### Выполнение команд в контейнере
```bash
# Backend
docker-compose exec backend python init_db.py
docker-compose exec backend python -m pytest

# База данных
docker-compose exec db psql -U tender_user -d tender
```

---

## Troubleshooting

### Backend не подключается к БД
```bash
# Проверьте, что PostgreSQL запущен
docker-compose ps

# Проверьте логи
docker-compose logs db
docker-compose logs backend
```

### Ollama недоступен
Backend использует `host.docker.internal:11434` для подключения к Ollama на хосте.

**Windows/Mac:** Должно работать автоматически.

**Linux:** Может потребоваться добавить в `docker-compose.yml`:
```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

### Frontend не открывается
```bash
# Проверьте, что frontend контейнер запущен
docker-compose ps frontend

# Проверьте логи
docker-compose logs frontend

# Проверьте, что порт 80 свободен
netstat -an | grep :80
```

### ChromaDB не работает
```bash
# Проверьте логи
docker-compose logs chromadb

# Пересоздайте volume
docker-compose down -v
docker-compose up -d
```

---

## Переменные окружения

Основные переменные в `backend/.env`:

| Переменная | Описание | Пример |
|-----------|----------|--------|
| `TENDER_DB_USER` | Пользователь БД | `tender_user` |
| `TENDER_DB_PASSWORD` | Пароль БД | `tender_password` |
| `TENDER_SECRET_KEY` | Секретный ключ JWT | (сгенерируйте случайный) |
| `TENDER_OLLAMA_BASE_URL` | URL Ollama | `http://host.docker.internal:11434` |
| `TENDER_OLLAMA_MODEL` | Модель для анализа | `qwen2.5-coder:7b` |
| `TENDER_SMTP_HOST` | SMTP сервер | `smtp.gmail.com` |
| `TENDER_SMTP_USER` | Email для отправки | `your-email@gmail.com` |
| `TENDER_SMTP_PASSWORD` | Пароль приложения | (16-символьный пароль) |

---

## Production Deployment

Для production рекомендуется:

1. **Изменить секретные ключи** - сгенерируйте новые для production
2. **Настроить SSL** - добавьте SSL сертификаты в nginx.conf
3. **Настроить резервное копирование** - для PostgreSQL и ChromaDB volumes
4. **Мониторинг** - добавьте health checks и логирование
5. **Ограничить доступ** - настройте firewall и CORS

---

**Готово! Система должна работать на http://localhost** 🚀
