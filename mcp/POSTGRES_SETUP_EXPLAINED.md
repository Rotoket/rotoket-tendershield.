# 📝 ОБЪЯСНЕНИЕ: НАСТРОЙКА DATABASE_URL ДЛЯ MCP

## ❓ ЧТО ТАКОЕ DATABASE_URL?

**DATABASE_URL** - это строка подключения к базе данных PostgreSQL. Она содержит:
- **Имя пользователя** (не email!)
- **Пароль**
- **Хост** (где находится база данных)
- **Порт** (обычно 5432)
- **Имя базы данных**

**Формат:**
```
postgresql://ИМЯ_ПОЛЬЗОВАТЕЛЯ:ПАРОЛЬ@localhost:5432/ИМЯ_БАЗЫ_ДАННЫХ
```

---

## 🔍 КАКИЕ ДАННЫЕ ИСПОЛЬЗОВАТЬ?

### ВАРИАНТ 1: Если PostgreSQL установлен локально на компьютере

**Стандартные значения по умолчанию:**
- **Имя пользователя:** `postgres`
- **Пароль:** `postgres` (или тот, который вы задали при установке PostgreSQL)
- **Хост:** `localhost`
- **Порт:** `5432`
- **Имя базы данных:** `tender_shield`

**Пример DATABASE_URL:**
```json
"DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/tender_shield"
```

### ВАРИАНТ 2: Если используется Docker (docker-compose)

**Значения из docker-compose.yml:**
- **Имя пользователя:** `tender_user`
- **Пароль:** `tender_password`
- **Хост:** `localhost` (или `db` если внутри Docker сети)
- **Порт:** `5432`
- **Имя базы данных:** `tender` (или `tender_shield`)

**Пример DATABASE_URL:**
```json
"DATABASE_URL": "postgresql://tender_user:tender_password@localhost:5432/tender"
```

---

## ✅ КАК ПРОВЕРИТЬ, ЧТО ИСПОЛЬЗОВАТЬ?

### Шаг 1: Проверь, запущен ли Docker контейнер

Открой терминал и выполни:
```bash
docker ps
```

Если видишь контейнер `tender_postgres` - используй **ВАРИАНТ 2** (Docker).

Если контейнера нет - используй **ВАРИАНТ 1** (локальный PostgreSQL).

### Шаг 2: Проверь настройки в проекте

Открой файл `backend/.env` (если он есть) или `backend/env.example`:

**Если в файле есть:**
```
TENDER_DB_USER=postgres
TENDER_DB_PASSWORD=postgres
```
→ Используй **ВАРИАНТ 1**

**Если в файле есть:**
```
TENDER_DB_USER=tender_user
TENDER_DB_PASSWORD=tender_password
```
→ Используй **ВАРИАНТ 2**

---

## 📝 КАК ЗАПОЛНИТЬ mcp.json

### Пример для локального PostgreSQL:

Открой файл `mcp/mcp.json` и найди секцию `postgres`:

```json
"postgres": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres"],
  "env": {
    "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/tender_shield"
  },
  "timeout": 30000,
  "description": "PostgreSQL database operations and migrations"
}
```

**Если у тебя другой пароль PostgreSQL:**
Замени `postgres` (второй) на свой пароль:
```json
"DATABASE_URL": "postgresql://postgres:ТВОЙ_ПАРОЛЬ@localhost:5432/tender_shield"
```

### Пример для Docker:

```json
"postgres": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres"],
  "env": {
    "DATABASE_URL": "postgresql://tender_user:tender_password@localhost:5432/tender"
  },
  "timeout": 30000,
  "description": "PostgreSQL database operations and migrations"
}
```

---

## ⚠️ ВАЖНО!

1. **Это НЕ email!** Это имя пользователя базы данных (обычно `postgres` или `tender_user`)

2. **Пароль** - это пароль, который ты задал при установке PostgreSQL, или пароль из docker-compose.yml

3. **Если не помнишь пароль:**
   - Для локального PostgreSQL: попробуй стандартный `postgres`
   - Для Docker: посмотри в `infra/docker-compose.yml` (строка `POSTGRES_PASSWORD`)

4. **Если база данных не существует:**
   - Создай её через `psql` или используй скрипт `backend/create_db.py`

---

## 🧪 ПРОВЕРКА ПОДКЛЮЧЕНИЯ

После настройки проверь подключение:

```bash
# Для локального PostgreSQL
psql -U postgres -d tender_shield -c "SELECT 1;"

# Для Docker
docker exec tender_postgres psql -U tender_user -d tender -c "SELECT 1;"
```

Если команда выполнилась без ошибок - подключение работает!

---

## 📋 БЫСТРАЯ СПРАВКА

| Вариант | Пользователь | Пароль | База данных |
|---------|-------------|--------|-------------|
| Локальный | `postgres` | `postgres` (или твой) | `tender_shield` |
| Docker | `tender_user` | `tender_password` | `tender` |

**Формат DATABASE_URL:**
```
postgresql://ПОЛЬЗОВАТЕЛЬ:ПАРОЛЬ@localhost:5432/БАЗА_ДАННЫХ
```

---

## ✅ ГОТОВО!

После настройки перезагрузи Cursor и проверь, что Postgres MCP работает!























