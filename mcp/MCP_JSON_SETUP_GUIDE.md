# 🔧 НАСТРОЙКА MCP ЧЕРЕЗ cursor-settings.json

## 📋 СПОСОБ №2 — ЧЕРЕЗ JSON (ENTERPRISE-ПРАВИЛЬНО)

Если хочешь контроль и воспроизводимость, делай так.

---

## 🚀 ШАГ 1: НАЙДИ ФАЙЛ cursor-settings.json

### Windows:
```
C:\Users\Dom\AppData\Roaming\Cursor\mcp.json
```

### Mac:
```
~/Library/Application Support/Cursor/mcp.json
```

### Linux:
```
~/.config/Cursor/mcp.json
```

> ⚠️ Если файла нет - создай его

---

## 🚀 ШАГ 2: СКОПИРУЙ КОНФИГУРАЦИЮ

Открой файл `mcp/mcp.json` из проекта и скопируй содержимое в `cursor-settings.json` (или `mcp.json` в папке Cursor).

**Полная конфигурация:**

```json
{
  "mcpServers": {
    "pandoc": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-pandoc"],
      "timeout": 60000,
      "description": "Document conversion (DOCX, PDF, XLSX to Markdown)"
    },
    "xlsx": {
      "command": "npx",
      "args": ["-y", "mcp-server-xlsx"],
      "timeout": 30000,
      "description": "Excel file reading and processing"
    },
    "python": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-python"],
      "timeout": 60000,
      "description": "Python interpreter for calculations and data processing"
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/tender_shield"
      },
      "timeout": 30000,
      "description": "PostgreSQL database operations and migrations"
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "timeout": 60000,
      "description": "Structured problem-solving with step-by-step reasoning"
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "timeout": 30000,
      "description": "Real-time documentation access for latest APIs and frameworks"
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-playwright"],
      "timeout": 120000,
      "description": "Browser automation and E2E testing"
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "description": "File operations: create, read, edit, delete"
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"],
      "description": "Git operations: commit, push, branch management"
    },
    "docker": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-docker"],
      "timeout": 60000,
      "description": "Docker container management"
    },
    "browser": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-browser"],
      "timeout": 120000,
      "description": "Browser control and screenshots"
    },
    "code-quality": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-code-quality"],
      "timeout": 60000,
      "description": "Testing and linting"
    },
    "npm": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-npm"],
      "description": "NPM package management"
    }
  }
}
```

---

## 🚀 ШАГ 3: ОБНОВИ DATABASE_URL

**Важно:** Замени данные подключения к PostgreSQL:

```json
"postgres": {
  "env": {
    "DATABASE_URL": "postgresql://ТВОЙ_ПОЛЬЗОВАТЕЛЬ:ТВОЙ_ПАРОЛЬ@localhost:5432/tender_shield"
  }
}
```

**Пример:**
Если твой пользователь `postgres`, пароль `mypassword123`:
```json
"DATABASE_URL": "postgresql://postgres:mypassword123@localhost:5432/tender_shield"
```

---

## 🚀 ШАГ 4: ПРОВЕРЬ JSON СИНТАКСИС

1. Открой файл в редакторе с проверкой JSON (VS Code, Cursor)
2. Убедись, что нет ошибок синтаксиса
3. Проверь, что все запятые на месте
4. Проверь, что все кавычки закрыты

**Онлайн валидатор:**
- https://jsonlint.com/
- https://jsonformatter.org/

---

## 🚀 ШАГ 5: ПЕРЕЗАГРУЗИ CURSOR

1. Закрой Cursor полностью
2. Открой Cursor снова
3. Проверь, что MCP серверы загрузились:
   - Settings → MCP Servers
   - Должны быть видны все 14 серверов

---

## ✅ ПРЕИМУЩЕСТВА JSON ПОДХОДА

### ✅ Можно коммитить
Файл `mcp/mcp.json` можно добавить в Git (без секретов):
```json
"DATABASE_URL": "postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/tender_shield"
```

### ✅ Можно использовать в команде
Все разработчики используют одинаковую конфигурацию.

### ✅ Можно воспроизводить на сервере
Конфигурация версионируется и воспроизводима.

---

## 🔒 БЕЗОПАСНОСТЬ

### ⚠️ НЕ коммить файл с реальными паролями!

**Правильно:**
```json
"DATABASE_URL": "postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/tender_shield"
```

**Неправильно:**
```json
"DATABASE_URL": "postgresql://postgres:realpassword123@localhost:5432/tender_shield"
```

### ✅ Используй переменные окружения

В `.gitignore` добавь:
```
Cursor/mcp.json
```

Или используй шаблон:
```
Cursor/mcp.json.example
```

---

## 🧪 ПРОВЕРКА РАБОТЫ

После настройки проверь через тестовые команды (см. `MCP_UI_SETUP_GUIDE.md`):

1. **Тест Pandoc:**
```
Используй MCP pandoc и преобразуй файл Проект_контракта.docx в Markdown.
```

2. **Тест XLSX:**
```
Используй MCP xlsx и прочитай значение ячейки B12 из файла nmck.xlsx.
```

3. **Тест Python:**
```
Используй MCP python и посчитай: (22440 * 1.2 * 720) * 1.15
```

4. **Тест Postgres:**
```
Используй MCP postgres и покажи список таблиц в базе данных.
```

---

## 📋 БЫСТРЫЙ ЧЕКЛИСТ

- [ ] Файл `mcp.json` найден/создан
- [ ] Конфигурация скопирована из `mcp/mcp.json`
- [ ] DATABASE_URL обновлён с правильными данными
- [ ] JSON синтаксис проверен
- [ ] Cursor перезагружен
- [ ] MCP серверы видны в Settings
- [ ] Тестовые команды работают

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

После настройки через JSON:

1. Прочитай: `mcp/MCP_TENDER_SHIELD_INTEGRATION.md`
2. Изучи канонический пайплайн с MCP
3. Попробуй обработать реальный документ через MCP

---

## ✅ ГОТОВО!

Теперь MCP настроен через JSON и готов к использованию!

**Преимущества:**
- ✅ Версионирование конфигурации
- ✅ Воспроизводимость
- ✅ Контроль над настройками






















