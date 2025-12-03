# Решение проблемы с кодировкой PostgreSQL на Windows

## Проблема

Ошибка: `'utf-8' codec can't decode byte 0xc2 in position 61`

Это означает, что в пароле или имени пользователя есть символы, которые не могут быть декодированы как UTF-8.

## Быстрое решение

### Шаг 1: Проверьте параметры подключения

Запустите диагностику:
```bash
python check_db_connection.py
```

Скрипт покажет, какой именно параметр вызывает проблему.

### Шаг 2: Создайте/обновите файл .env

Создайте файл `backend/.env` с **правильной кодировкой UTF-8**:

```env
TENDER_DB_USER=postgres
TENDER_DB_PASSWORD=postgres123
TENDER_DB_HOST=localhost
TENDER_DB_PORT=5432
TENDER_DB_NAME=tender_shield
```

**ВАЖНО:**
- Используйте только **латинские буквы** и **цифры** в пароле
- Не используйте русские буквы, спецсимволы (кроме `_`, `-`, `.`)
- Сохраните файл в кодировке **UTF-8** (в Notepad++: Кодировка → Преобразовать в UTF-8)

### Шаг 3: Измените пароль PostgreSQL (если нужно)

#### Вариант A: Через pgAdmin (GUI)

1. Откройте **pgAdmin 4** (устанавливается вместе с PostgreSQL)
2. Подключитесь к серверу
3. Правый клик на пользователе `postgres` → Properties
4. Вкладка Definition → измените пароль на простой (только латиница и цифры)
5. Сохраните

#### Вариант B: Через SQL (если psql доступен)

Найдите `psql.exe` в папке установки PostgreSQL (обычно `C:\Program Files\PostgreSQL\18\bin\`):

```powershell
# Добавьте в PATH или используйте полный путь
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres
```

Затем выполните:
```sql
ALTER USER postgres WITH PASSWORD 'postgres123';
```

#### Вариант C: Через командную строку Windows

```powershell
# Найдите путь к psql
$psqlPath = Get-ChildItem -Path "C:\Program Files\PostgreSQL" -Recurse -Filter "psql.exe" | Select-Object -First 1

# Используйте полный путь
& $psqlPath.FullName -U postgres -c "ALTER USER postgres WITH PASSWORD 'postgres123';"
```

### Шаг 4: Создайте базу данных

#### Через pgAdmin:
1. Правый клик на "Databases" → Create → Database
2. Name: `tender_shield`
3. Encoding: `UTF8`
4. Save

#### Через SQL:
```sql
CREATE DATABASE tender_shield ENCODING 'UTF8';
```

### Шаг 5: Проверьте подключение

```bash
python check_db_connection.py
```

## Альтернативное решение: Использование SQLite для разработки

Если проблема не решается, можно временно использовать SQLite:

1. Удалите или закомментируйте настройки PostgreSQL в `.env`
2. Система автоматически переключится на SQLite
3. Для продакшена все равно нужен PostgreSQL

## Проверка кодировки файла .env

### В Notepad++:
1. Откройте файл `.env`
2. Кодировка → Преобразовать в UTF-8
3. Сохраните

### В VS Code:
1. Откройте файл `.env`
2. В правом нижнем углу нажмите на кодировку
3. Выберите "Save with Encoding" → UTF-8

## Типичные проблемы

### Проблема: Пароль содержит русские буквы
**Решение:** Измените пароль на только латиницу и цифры

### Проблема: Файл .env сохранен в неправильной кодировке
**Решение:** Пересохраните в UTF-8

### Проблема: psql не найден
**Решение:** Используйте pgAdmin или найдите psql.exe в папке установки PostgreSQL

## После исправления

Запустите тесты:
```bash
pytest tests/ -v
```

Все должно работать! 🎉





