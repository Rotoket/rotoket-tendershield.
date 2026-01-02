# ⚡ БЫСТРАЯ НАСТРОЙКА DATABASE_URL

## 📝 ЧТО НУЖНО ЗНАТЬ

**Это НЕ email и НЕ почта!** Это настройки для подключения к базе данных PostgreSQL.

---

## ✅ ГОТОВОЕ РЕШЕНИЕ (для локального PostgreSQL)

Файл `mcp/mcp.json` уже обновлён с правильными значениями:

```json
"DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/tender_shield"
```

**Что это значит:**
- **postgres** (первый) - имя пользователя базы данных
- **postgres** (второй) - пароль базы данных
- **localhost** - где находится база данных (на твоём компьютере)
- **5432** - порт PostgreSQL
- **tender_shield** - имя базы данных

---

## 🔧 ЕСЛИ У ТЕБЯ ДРУГОЙ ПАРОЛЬ

Если при установке PostgreSQL ты задал другой пароль (не `postgres`), замени второй `postgres` на свой пароль:

```json
"DATABASE_URL": "postgresql://postgres:ТВОЙ_ПАРОЛЬ@localhost:5432/tender_shield"
```

**Пример:**
Если твой пароль `mypassword123`:
```json
"DATABASE_URL": "postgresql://postgres:mypassword123@localhost:5432/tender_shield"
```

---

## 🧪 КАК ПРОВЕРИТЬ ПАРОЛЬ

Открой терминал и попробуй подключиться:

```bash
psql -U postgres -d tender_shield
```

Если попросит пароль - введи свой пароль PostgreSQL.

Если подключилось без пароля или с паролем `postgres` - используй `postgres:postgres`.

---

## 📋 ИТОГО

1. **Открой файл:** `mcp/mcp.json`
2. **Найди секцию:** `"postgres"`
3. **Проверь строку:** `"DATABASE_URL"`
4. **Если пароль не `postgres`** - замени на свой
5. **Скопируй файл** в Cursor: `C:\Users\Dom\AppData\Roaming\Cursor\mcp.json`
6. **Перезагрузи Cursor**

---

## ❓ ЕСЛИ НЕ РАБОТАЕТ

1. Проверь, что PostgreSQL запущен
2. Проверь, что база данных `tender_shield` существует
3. Попробуй подключиться через `psql` вручную
4. Посмотри логи Cursor: `Help > Toggle Developer Tools > Console`

---

## ✅ ГОТОВО!

После настройки Postgres MCP будет работать автоматически!























