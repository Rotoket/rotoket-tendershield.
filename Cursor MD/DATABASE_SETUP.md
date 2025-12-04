# 🗄️ Настройка базы данных

## Быстрый старт

### 1. Установка PostgreSQL

**Windows:**
- Скачайте и установите PostgreSQL с [официального сайта](https://www.postgresql.org/download/windows/)
- Или используйте Docker:
```bash
docker run --name tender-shield-db -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=tender_shield -p 5432:5432 -d postgres:15
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Mac (Homebrew)
brew install postgresql
brew services start postgresql
```

### 2. Создание базы данных

```sql
-- Подключитесь к PostgreSQL
psql -U postgres

-- Создайте базу данных
CREATE DATABASE tender_shield;

-- Создайте пользователя (опционально)
CREATE USER tender_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE tender_shield TO tender_user;
```

### 3. Настройка переменных окружения

Создайте файл `.env` в папке `backend/`:

```env
TENDER_DB_USER=postgres
TENDER_DB_PASSWORD=postgres
TENDER_DB_HOST=localhost
TENDER_DB_PORT=5432
TENDER_DB_NAME=tender_shield

TENDER_SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars
TENDER_ACCESS_TOKEN_EXPIRE_MINUTES=43200
```

### 4. Установка зависимостей

```bash
cd backend
pip install -r requirements.txt
```

### 5. Инициализация базы данных

```bash
# Создание таблиц и тарифов
python init_db.py
```

Или используйте Alembic для миграций:

```bash
# Создание первой миграции
alembic revision --autogenerate -m "Initial migration"

# Применение миграций
alembic upgrade head
```

## Структура базы данных

### Таблицы:

1. **users** - Пользователи системы
2. **tariffs** - Тарифные планы (Start, Pro, Enterprise)
3. **analyses** - Анализы отдельных документов
4. **package_analyses** - Пакетные анализы
5. **usage** - Учет использования (квоты по месяцам)

## Проверка работы

```bash
# Запустите сервер
uvicorn main:app --reload

# Проверьте эндпоинты
curl http://localhost:8000/api/tariffs
```

## Создание первого пользователя

Через API:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "secure_password",
    "name": "Администратор",
    "company": "Моя компания"
  }'
```

Или создайте скрипт `create_admin.py`:
```python
from database import get_db, User
from auth import get_password_hash

db = next(get_db())
admin = User(
    email="admin@example.com",
    hashed_password=get_password_hash("admin123"),
    name="Администратор",
    is_superuser=True,
    tariff_id=3  # Enterprise
)
db.add(admin)
db.commit()
print("✅ Администратор создан")
```

## Миграции

При изменении моделей:

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1
```

## Резервное копирование

```bash
# Создать бэкап
pg_dump -U postgres tender_shield > backup.sql

# Восстановить из бэкапа
psql -U postgres tender_shield < backup.sql
```


