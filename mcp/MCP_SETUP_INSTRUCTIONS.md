# 🚀 ИНСТРУКЦИИ ПО УСТАНОВКЕ MCP ДЛЯ CURSOR

## 📋 ДВА СПОСОБА УСТАНОВКИ

### 🎯 Способ №1: Через Cursor UI (рекомендуется для начала)
**Самый простой путь для быстрого старта.**

👉 **См. подробную инструкцию:** `mcp/MCP_UI_SETUP_GUIDE.md`

### 🔧 Способ №2: Через JSON файл (enterprise-правильно)
**Для контроля и воспроизводимости.**

👉 **См. подробную инструкцию:** `mcp/MCP_JSON_SETUP_GUIDE.md`

---

## 📋 БЫСТРЫЙ СТАРТ (ЧЕРЕЗ JSON)

### ШАГ 1: Создать файл mcp.json

**Для Windows:**
1. Открой проводник
2. Перейди в: `C:\Users\Dom\AppData\Roaming\Cursor\`
3. Создай файл `mcp.json` (если его нет)
4. Скопируй содержимое из файла `mcp/mcp.json` из проекта

**Для Mac:**
1. Открой Finder
2. Нажми `Cmd+Shift+G`
3. Введи: `~/Library/Application Support/Cursor/`
4. Создай файл `mcp.json`
5. Скопируй содержимое из файла `mcp/mcp.json` из проекта

**Для Linux:**
1. Открой терминал
2. Выполни: `mkdir -p ~/.config/Cursor`
3. Создай файл: `~/.config/Cursor/mcp.json`
4. Скопируй содержимое из файла `mcp/mcp.json` из проекта

---

### ШАГ 2: Настроить DATABASE_URL

**Важно:** Обнови строку подключения к базе данных в файле `mcp.json`:

```json
"postgres": {
  "env": {
    "DATABASE_URL": "postgresql://ТВОЙ_ПОЛЬЗОВАТЕЛЬ:ТВОЙ_ПАРОЛЬ@localhost:5432/tender_shield"
  }
}
```

Замени:
- `ТВОЙ_ПОЛЬЗОВАТЕЛЬ` - имя пользователя PostgreSQL (обычно `postgres`)
- `ТВОЙ_ПАРОЛЬ` - пароль PostgreSQL (обычно `postgres`)
- `tender_shield` - имя базы данных

👉 **Подробное объяснение:** `mcp/POSTGRES_SETUP_EXPLAINED.md`

---

### ШАГ 3: Перезагрузить Cursor

1. Закрой Cursor полностью
2. Открой Cursor снова
3. Проверь установку:
   - Открой: `Cursor > Settings > MCP Servers`
   - Должно быть видно 14 серверов:
     - pandoc, xlsx, python, postgres (для Tender Shield)
     - sequential-thinking, context7, playwright, filesystem, git, docker, browser, code-quality, npm (для разработки)

---

## ✅ ПРОВЕРКА УСТАНОВКИ

### Проверка 1: MCP серверы видны

1. Открой Cursor
2. Перейди в: `Settings > MCP Servers`
3. Должно быть видно 14 серверов:
   - **pandoc** (для DOCX → Markdown)
   - **xlsx** (для чтения Excel)
   - **python** (для расчётов)
   - **postgres** (для базы данных)
   - sequential-thinking, context7, playwright, filesystem, git, docker, browser, code-quality, npm

### Проверка 2: Тестовые команды

**Тест Pandoc:**
```
Используй MCP pandoc и преобразуй файл Проект_контракта.docx в Markdown.
```

**Тест XLSX:**
```
Используй MCP xlsx и прочитай значение ячейки B12 из файла nmck.xlsx.
```

**Тест Python:**
```
Используй MCP python и посчитай: (22440 * 1.2 * 720) * 1.15
```

**Тест Postgres:**
```
Используй MCP postgres и покажи список таблиц в базе данных.
```

Если Cursor делает tool-call и возвращает результат → MCP работает!

---

## 🔧 РЕШЕНИЕ ПРОБЛЕМ

### Проблема: MCP серверы не загружаются

**Решение:**
1. Проверь синтаксис JSON в `mcp.json` (используй JSON validator)
2. Проверь что Node.js установлен: `node --version`
3. Перезагрузи Cursor
4. Проверь логи Cursor: `Help > Toggle Developer Tools > Console`

### Проблема: Postgres MCP не работает

**Решение:**
1. Проверь что PostgreSQL запущен
2. Проверь DATABASE_URL в `mcp.json`
3. Проверь что база данных существует
4. Проверь права доступа пользователя

### Проблема: Docker MCP не работает

**Решение:**
1. Проверь что Docker запущен: `docker ps`
2. Проверь что Docker доступен из командной строки
3. Перезагрузи Cursor

---

## 📚 ДОПОЛНИТЕЛЬНАЯ ДОКУМЕНТАЦИЯ

Все файлы находятся в папке `mcp/`:

### 🎯 Основные инструкции:
- **UI Setup:** `mcp/MCP_UI_SETUP_GUIDE.md` - настройка через Cursor UI
- **JSON Setup:** `mcp/MCP_JSON_SETUP_GUIDE.md` - настройка через JSON файл
- **Postgres Setup:** `mcp/POSTGRES_SETUP_EXPLAINED.md` - объяснение DATABASE_URL
- **Quick Postgres:** `mcp/QUICK_SETUP_POSTGRES.md` - быстрая настройка PostgreSQL

### 🔗 Интеграция с Tender Shield:
- **Integration Guide:** `mcp/MCP_TENDER_SHIELD_INTEGRATION.md` - канонический пайплайн с MCP
- **Cursor Rules:** `.cursorrules` (раздел MCP INTEGRATION RULES)

### 📋 Старые документы (для справки):
- **Быстрый старт:** `mcp/2/QUICK_COPY_PASTE_GUIDE.md`
- **Полный гайд:** `mcp/MCP_Installation_Guide_Cursor_Ollama.md`
- **Расширенные правила:** `mcp/2/11_MCP_ADVANCED_RULES.md`
- **Стратегия:** `mcp/2/14_ADVANCED_MCP_STRATEGY.md`
- **Индекс документации:** `mcp/1/Complete_MCP_Documentation_Index.md`

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

После установки MCP:

1. **Прочитай интеграцию:** `mcp/MCP_TENDER_SHIELD_INTEGRATION.md`
2. **Изучи канонический пайплайн:** MCP используется только до Decision Preview
3. **Попробуй тестовые команды:** pandoc, xlsx, python, postgres
4. **Начни использовать MCP** для обработки документов и расчётов

---

## ⚠️ ВАЖНО: MCP И КАНОН ПРОЕКТА

**MCP используется только до Decision Preview:**
- ✅ MCP для обработки документов (pandoc, xlsx)
- ✅ MCP для расчётов (python)
- ✅ MCP для базы данных (postgres)
- ❌ MCP НЕ используется после Decision Preview
- ❌ MCP НЕ используется в Guardrails

👉 **Подробнее:** `mcp/MCP_TENDER_SHIELD_INTEGRATION.md`

---

## ✅ ГОТОВО!

Теперь Cursor настроен с 14 MCP серверами и готов к использованию!

**Время установки:** 5-10 минут  
**Ускорение обработки документов:** до 14x на отдельных задачах

**MCP серверы для Tender Shield:**
- pandoc (DOCX → Markdown)
- xlsx (чтение Excel)
- python (расчёты)
- postgres (база данных)


