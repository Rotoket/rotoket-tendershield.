# Настройка PostgreSQL для Tender Shield

## Проблемы с кодировкой

Если вы видите ошибку:
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc2 in position 61
```

Это означает проблему с кодировкой при подключении к PostgreSQL.

## Решение

### Вариант 1: Настройка существующей БД (рекомендуется)

1. **Подключитесь к PostgreSQL:**
   ```bash
   psql -U postgres
   ```

2. **Создайте базу данных с правильной кодировкой:**
   ```sql
   CREATE DATABASE tender_shield 
   ENCODING 'UTF8' 
   LC_COLLATE='ru_RU.UTF-8' 
   LC_CTYPE='ru_RU.UTF-8';
   ```

3. **Или если база уже существует, измените кодировку:**
   ```sql
   ALTER DATABASE tender_shield SET client_encoding = 'UTF8';
   ```

4. **Проверьте кодировку:**
   ```sql
   \l tender_shield
   ```

### Вариант 2: Переустановка PostgreSQL (если проблема не решается)

1. **Экспортируйте данные (если есть):**
   ```bash
   pg_dump -U postgres tender_shield > backup.sql
   ```

2. **Удалите PostgreSQL 18**

3. **Установите PostgreSQL 16 или 15** (более стабильная версия):
   - Скачайте с официального сайта: https://www.postgresql.org/download/windows/
   - При установке выберите:
     - Encoding: UTF8
     - Locale: Russian, Russia
     - Port: 5432

4. **Создайте базу данных:**
   ```sql
   CREATE DATABASE tender_shield ENCODING 'UTF8';
   ```

5. **Восстановите данные (если были):**
   ```bash
   psql -U postgres tender_shield < backup.sql
   ```

### Вариант 3: Использование SQLite для тестов (временное решение)

Если PostgreSQL не работает, система автоматически переключится на SQLite для тестов.

## Проверка подключения

Запустите скрипт проверки:

```bash
python check_db_connection.py
```

Скрипт проверит:
- Установлен ли psycopg2
- Подключение к PostgreSQL
- Кодировку БД
- Версию PostgreSQL

## Настройка переменных окружения

Создайте файл `.env` в папке `backend/`:

```env
TENDER_DB_USER=postgres
TENDER_DB_PASSWORD=ваш_пароль
TENDER_DB_HOST=localhost
TENDER_DB_PORT=5432
TENDER_DB_NAME=tender_shield
```

## Устранение проблем

### Проблема: "База данных не существует"

```sql
CREATE DATABASE tender_shield ENCODING 'UTF8';
```

### Проблема: "Пользователь не имеет прав"

```sql
GRANT ALL PRIVILEGES ON DATABASE tender_shield TO postgres;
```

### Проблема: "Не удается подключиться"

1. Проверьте, запущен ли PostgreSQL:
   ```bash
   # Windows
   services.msc
   # Найдите "PostgreSQL" и убедитесь, что служба запущена
   ```

2. Проверьте порт:
   ```bash
   netstat -an | findstr 5432
   ```

3. Проверьте настройки `pg_hba.conf`:
   - Найдите файл в папке установки PostgreSQL
   - Убедитесь, что есть строка:
     ```
     host    all             all             127.0.0.1/32            md5
     ```

## Проверка после настройки

После настройки запустите тесты:

```bash
pytest tests/ -v
```

Если все настроено правильно, тесты должны пройти без ошибок кодировки.





