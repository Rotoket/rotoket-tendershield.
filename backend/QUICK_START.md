# 🚀 Быстрый старт: База данных и авторизация

## Что было сделано

✅ **Создана структура базы данных:**
- Модели: User, Tariff, Analysis, PackageAnalysis, Usage
- SQLAlchemy ORM для работы с PostgreSQL
- Миграции через Alembic

✅ **Реализована авторизация:**
- JWT токены
- Регистрация и вход
- Хеширование паролей (bcrypt)

✅ **Система тарифов:**
- 3 тарифа: Start, Pro, Enterprise
- Проверка лимитов использования
- Учет анализов по месяцам

## Установка и настройка

### 1. Установите зависимости

```bash
cd backend
pip install -r requirements.txt
```

### 2. Настройте PostgreSQL

**Вариант A: Docker (рекомендуется для разработки)**
```bash
docker run --name tender-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=tender_shield -p 5432:5432 -d postgres:15
```

**Вариант B: Локальная установка**
- Установите PostgreSQL
- Создайте БД: `CREATE DATABASE tender_shield;`

### 3. Создайте файл `.env`

```env
TENDER_DB_USER=postgres
TENDER_DB_PASSWORD=postgres
TENDER_DB_HOST=localhost
TENDER_DB_PORT=5432
TENDER_DB_NAME=tender_shield
TENDER_SECRET_KEY=your-super-secret-key-min-32-chars
```

### 4. Инициализируйте БД

```bash
python init_db.py
```

Или через Alembic:
```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### 5. Запустите сервер

```bash
uvicorn main:app --reload
```

## Тестирование API

### Регистрация пользователя

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "name": "Тестовый пользователь",
    "company": "ООО Тест"
  }'
```

### Вход в систему

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123"
  }'
```

Ответ:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "test@example.com",
    "name": "Тестовый пользователь",
    "company": "ООО Тест",
    "tariff_id": 1
  }
}
```

### Использование токена

```bash
TOKEN="your-access-token"

# Получить информацию о себе
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Получить тарифы
curl http://localhost:8000/api/tariffs

# Анализ документа (с авторизацией)
curl -X POST http://localhost:8000/api/analyze \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf" \
  -F "industry=IT"
```

## Следующие шаги

1. ✅ База данных - ГОТОВО
2. ⏳ Обновить frontend для работы с авторизацией
3. ⏳ Интегрировать платежную систему
4. ⏳ Добавить rate limiting
5. ⏳ Оптимизировать backend (асинхронность, кеширование)

## Проблемы?

**Ошибка подключения к БД:**
- Проверьте, что PostgreSQL запущен
- Проверьте настройки в `.env`
- Убедитесь, что БД `tender_shield` создана

**Ошибки импорта:**
- Убедитесь, что все зависимости установлены: `pip install -r requirements.txt`
- Проверьте, что вы в виртуальном окружении

**Миграции не работают:**
- Проверьте `alembic.ini` - URL БД должен быть правильным
- Убедитесь, что `alembic/env.py` импортирует модели из `database.py`


