# 📋 MCP КОНФИГУРАЦИЯ ДЛЯ CURSOR

## 📍 РАСПОЛОЖЕНИЕ ФАЙЛА

**Windows:**
```
C:\Users\Dom\AppData\Roaming\Cursor\mcp.json
```

**Mac:**
```
~/Library/Application Support/Cursor/mcp.json
```

**Linux:**
```
~/.config/Cursor/mcp.json
```

---

## 📝 СОДЕРЖИМОЕ ФАЙЛА mcp.json

Скопируй это содержимое в файл `mcp.json`:

```json
{
  "mcpServers": {
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
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://tender_user:password@localhost:5432/tender_shield"
      },
      "timeout": 30000,
      "description": "PostgreSQL database operations and migrations"
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

## ⚙️ НАСТРОЙКА DATABASE_URL

**Важно:** Обнови `DATABASE_URL` в секции `postgres` на свои реальные данные:

```json
"postgres": {
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-postgres"],
  "env": {
    "DATABASE_URL": "postgresql://ТВОЙ_ПОЛЬЗОВАТЕЛЬ:ТВОЙ_ПАРОЛЬ@localhost:5432/tender_shield"
  },
  "timeout": 30000,
  "description": "PostgreSQL database operations and migrations"
}
```

---

## ✅ ПРОВЕРКА УСТАНОВКИ

После создания файла:

1. Перезагрузи Cursor
2. Открой: `Cursor > Settings > MCP Servers`
3. Должно быть видно 10 серверов

---

## 🚀 ГОТОВО!

Теперь Cursor может использовать все 10 MCP серверов для ускорения разработки!























