# 🎯 НАСТРОЙКА MCP ЧЕРЕЗ CURSOR UI

## 📋 СПОСОБ №1 — ЧЕРЕЗ CURSOR UI (РЕКОМЕНДУЕТСЯ)

Это самый простой и безопасный путь для начала работы.

---

## 🚀 ШАГ 1: ОТКРОЙ CURSOR → SETTINGS

1. Открой Cursor
2. Нажми `Ctrl+,` (или `Cmd+,` на Mac) для открытия Settings
3. Или через меню: `File > Preferences > Settings`

4. В поиске настроек введи: **MCP** или **Model Context Protocol**

5. Найди раздел: **MCP / Tools / Model Context Protocol**

> ⚠️ Название может слегка отличаться по версии Cursor

---

## 🚀 ШАГ 2: ДОБАВЬ MCP-СЕРВЕРЫ

Нажми кнопку **"Add MCP Server"** и добавь каждый сервер:

### 📄 MCP Pandoc (для DOCX → Markdown)

**Настройки:**
- **Name:** `pandoc`
- **Command:** `npx`
- **Args:** `@modelcontextprotocol/server-pandoc`
- **Working directory:** (оставь пустым или укажи путь к проекту)

### 📊 MCP XLSX (для чтения Excel)

**Настройки:**
- **Name:** `xlsx`
- **Command:** `npx`
- **Args:** `mcp-server-xlsx`
- **Working directory:** (оставь пустым)

### 🐍 MCP Python (для расчётов)

**Настройки:**
- **Name:** `python`
- **Command:** `npx`
- **Args:** `@modelcontextprotocol/server-python`
- **Working directory:** (оставь пустым)

### 🗄️ MCP Postgres (для базы данных)

**Настройки:**
- **Name:** `postgres`
- **Command:** `npx`
- **Args:** `@modelcontextprotocol/server-postgres`
- **Working directory:** (оставь пустым)

**В разделе ENV добавь:**
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tender_shield
```

> ⚠️ Замени `postgres:postgres` на свои данные, если они отличаются

---

## 🚀 ШАГ 3: ПРОВЕРКА РАБОТЫ MCP

После добавления всех серверов:

1. **Перезагрузи Cursor** (закрой и открой заново)

2. **Проверь, что серверы видны:**
   - Открой Settings → MCP Servers
   - Должны быть видны: pandoc, xlsx, python, postgres

3. **Проверь через тестовые команды:**

### Тест Pandoc:
В Cursor chat напиши:
```
Используй MCP pandoc и преобразуй файл Проект_контракта.docx в Markdown.
```

### Тест XLSX:
```
Используй MCP xlsx и прочитай значение ячейки B12 из файла nmck.xlsx.
```

### Тест Python:
```
Используй MCP python и посчитай: (22440 * 1.2 * 720) * 1.15
```

### Тест Postgres:
```
Используй MCP postgres и покажи список таблиц в базе данных.
```

---

## ✅ ЕСЛИ ВСЁ РАБОТАЕТ

Если Cursor:
- ✅ Делает tool-call к MCP
- ✅ Возвращает результат
- ✅ Не выдаёт ошибок

→ **MCP подключён корректно!**

---

## ❌ ЕСЛИ НЕ РАБОТАЕТ

### Проблема 1: MCP серверы не видны

**Решение:**
1. Проверь, что Node.js установлен: `node --version`
2. Перезагрузи Cursor
3. Проверь логи: `Help > Toggle Developer Tools > Console`

### Проблема 2: Ошибка при вызове MCP

**Решение:**
1. Проверь, что команда правильная (npx должен быть доступен)
2. Проверь интернет-соединение (npx загружает пакеты)
3. Попробуй установить пакет вручную: `npx @modelcontextprotocol/server-pandoc`

### Проблема 3: Postgres MCP не работает

**Решение:**
1. Проверь, что PostgreSQL запущен
2. Проверь DATABASE_URL в настройках
3. Проверь, что база данных существует
4. См. `mcp/POSTGRES_SETUP_EXPLAINED.md`

---

## 📋 БЫСТРЫЙ ЧЕКЛИСТ

- [ ] Cursor Settings открыт
- [ ] Раздел MCP найден
- [ ] Добавлен MCP pandoc
- [ ] Добавлен MCP xlsx
- [ ] Добавлен MCP python
- [ ] Добавлен MCP postgres (с DATABASE_URL)
- [ ] Cursor перезагружен
- [ ] Тестовые команды работают

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

После настройки через UI:

1. Прочитай: `mcp/MCP_TENDER_SHIELD_INTEGRATION.md`
2. Изучи канонический пайплайн с MCP
3. Попробуй обработать реальный документ через MCP

---

## ✅ ГОТОВО!

Теперь MCP настроен через Cursor UI и готов к использованию!

**Время настройки:** 5-10 минут  
**Ускорение обработки документов:** до 14x






















