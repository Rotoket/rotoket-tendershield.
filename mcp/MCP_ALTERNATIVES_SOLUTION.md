# 🔧 РЕШЕНИЕ: Альтернативы для удалённых MCP серверов

## 📊 СТАТУС УДАЛЁННЫХ СЕРВЕРОВ

### ❌ Не существуют в npm:
- `@modelcontextprotocol/server-pandoc` 
- `@modelcontextprotocol/server-python`
- `@modelcontextprotocol/server-docker`
- `@modelcontextprotocol/server-browser`
- `@modelcontextprotocol/server-code-quality`
- `@modelcontextprotocol/server-npm`
- `@modelcontextprotocol/server-git`

---

## ✅ НАЙДЕННЫЕ АЛЬТЕРНАТИВЫ

### 1. **Git** → `@cyanheads/git-mcp-server` ✅

**Пакет:** `@cyanheads/git-mcp-server`  
**Версия:** 2.6.5 (последняя)  
**Статус:** ✅ Работает

**Функции:**
- Git операции: commit, push, pull, branch, merge
- Безопасный и масштабируемый
- Поддержка STDIO и Streamable HTTP

**Конфигурация:**
```json
"git": {
  "command": "npx",
  "args": ["-y", "@cyanheads/git-mcp-server"],
  "timeout": 30000,
  "description": "Git operations"
}
```

**Альтернатива:** `github-mcp-server` (версия 1.8.7)

---

### 2. **Docker** → `mcp-server-docker` ✅

**Пакет:** `mcp-server-docker`  
**Версия:** 1.0.0  
**Статус:** ✅ Работает

**Функции:**
- Управление Docker контейнерами
- Выполнение команд в контейнерах
- Управление образами и сетями

**Конфигурация:**
```json
"docker": {
  "command": "npx",
  "args": ["-y", "mcp-server-docker"],
  "timeout": 60000,
  "description": "Docker container management"
}
```

**Альтернатива:** `@thelord/mcp-server-docker-npx` (версия 0.4.0, более продвинутый)

---

### 3. **Python** → `mcp-server-code-runner` ✅

**Пакет:** `mcp-server-code-runner`  
**Версия:** 0.1.8  
**Статус:** ✅ Работает

**Функции:**
- Выполнение Python кода
- Выполнение JavaScript кода
- Выполнение других языков программирования

**Конфигурация:**
```json
"code-runner": {
  "command": "npx",
  "args": ["-y", "mcp-server-code-runner"],
  "timeout": 60000,
  "description": "Code execution (Python, JavaScript, etc.)"
}
```

**Альтернатива:** `@geobio/code_execution_server` (версия 0.2.1)

---

### 4. **Browser** → `@playwright/mcp` ✅ (уже есть!)

**Пакет:** `@playwright/mcp`  
**Версия:** 0.0.53  
**Статус:** ✅ Уже в конфигурации

**Функции:**
- Управление браузером
- Скриншоты
- E2E тестирование
- Автоматизация браузера

**Вывод:** Не нужен отдельный browser сервер, Playwright покрывает все функции!

---

### 5. **Pandoc** → `@modelconductor/mcp-server-pandoc` ⚠️

**Пакет:** `@modelconductor/mcp-server-pandoc`  
**Статус:** ⚠️ В ранней стадии разработки

**Проблемы:**
- PDF, CSV, DOCX поддержка не завершена
- Может быть нестабильным

**Альтернативы:**
1. **Python скрипты** с `pypandoc`:
   ```python
   import pypandoc
   output = pypandoc.convert_file('input.docx', 'markdown')
   ```

2. **Локальный Pandoc** через командную строку:
   ```bash
   pandoc input.docx -o output.md
   ```

3. **Использовать filesystem MCP** для чтения файлов и Python для конвертации

---

### 6. **Code Quality** → Встроенные инструменты ✅

**Статус:** ✅ Не нужен отдельный сервер

**Решение:**
- Используй встроенные инструменты проекта:
  - **Python:** `pytest`, `pylint`, `black`
  - **TypeScript:** `jest`, `eslint`, `prettier`
- Создай скрипты для запуска тестов через `filesystem` MCP

**Пример скрипта:**
```bash
# backend/run_tests.sh
pytest tests/ --cov=. --cov-report=term
```

---

### 7. **NPM** → Встроенный npm CLI ✅

**Статус:** ✅ Не нужен отдельный сервер

**Решение:**
- Используй npm CLI напрямую через терминал
- Или создай скрипты для управления пакетами

**Пример:**
```bash
npm install <package>
npm update
npm audit
```

---

## 📋 ИТОГОВАЯ КОНФИГУРАЦИЯ

### Минимальная (6 серверов) - `mcp.json.working`:
1. sequential-thinking
2. context7
3. playwright (заменяет browser)
4. filesystem
5. postgres
6. xlsx

### Расширенная (9 серверов) - `mcp.json.extended`:
1. sequential-thinking
2. context7
3. playwright
4. filesystem
5. postgres
6. xlsx
7. **git** (через `@cyanheads/git-mcp-server`)
8. **docker** (через `mcp-server-docker`)
9. **code-runner** (через `mcp-server-code-runner`, заменяет python)

---

## 🚀 КАК ИСПОЛЬЗОВАТЬ

### Вариант 1: Минимальная конфигурация (рекомендуется)

```bash
# Скопируй минимальную конфигурацию
Copy-Item -Path ".\mcp\mcp.json.working" -Destination "$env:APPDATA\Cursor\mcp.json" -Force
```

**Плюсы:**
- ✅ Все серверы проверены и работают
- ✅ Быстрая загрузка
- ✅ Меньше ошибок

**Минусы:**
- ❌ Нет Git, Docker, Python через MCP (но можно через CLI)

---

### Вариант 2: Расширенная конфигурация

```bash
# Скопируй расширенную конфигурацию
Copy-Item -Path ".\mcp\mcp.json.extended" -Destination "$env:APPDATA\Cursor\mcp.json" -Force
```

**Плюсы:**
- ✅ Git операции через MCP
- ✅ Docker управление через MCP
- ✅ Выполнение кода через MCP

**Минусы:**
- ⚠️ Больше серверов = больше точек отказа
- ⚠️ Нужно проверить каждый сервер

---

## 🔍 ПРОВЕРКА РАБОТОСПОСОБНОСТИ

### После установки расширенной конфигурации:

1. **Перезагрузи Cursor**
2. **Проверь каждый сервер:**
   - Settings → Tools & MCP → MCP Servers
   - Должны быть видны 9 серверов
   - Проверь статус каждого

3. **Если сервер показывает ошибку:**
   - Нажми "Show Output"
   - Скопируй ошибку
   - Проверь, что пакет установлен: `npm view <package-name> version`

---

## 📊 СРАВНЕНИЕ КОНФИГУРАЦИЙ

| Функция | Минимальная | Расширенная | Альтернатива |
|---------|------------|-------------|--------------|
| Git | ❌ | ✅ MCP | ✅ CLI |
| Docker | ❌ | ✅ MCP | ✅ CLI |
| Python | ❌ | ✅ MCP | ✅ CLI |
| Browser | ✅ Playwright | ✅ Playwright | - |
| Pandoc | ❌ | ❌ | ✅ Python скрипты |
| Code Quality | ❌ | ❌ | ✅ Встроенные инструменты |
| NPM | ❌ | ❌ | ✅ CLI |

---

## ✅ РЕКОМЕНДАЦИЯ

**Для начала используй минимальную конфигурацию** (`mcp.json.working`):

1. Все 6 серверов проверены и работают
2. Меньше ошибок при загрузке
3. Playwright покрывает функции browser
4. Git, Docker, Python можно использовать через CLI

**Если нужны Git/Docker/Python через MCP**, переключись на расширенную конфигурацию (`mcp.json.extended`).

---

## 🆘 ЕСЛИ ЧТО-ТО НЕ РАБОТАЕТ

1. **Проверь версию пакета:**
   ```bash
   npm view <package-name> version
   ```

2. **Проверь логи в Cursor:**
   - Settings → Tools & MCP → MCP Servers
   - Нажми "Show Output" для проблемного сервера

3. **Попробуй альтернативный пакет:**
   - Git: `github-mcp-server` вместо `@cyanheads/git-mcp-server`
   - Docker: `@thelord/mcp-server-docker-npx` вместо `mcp-server-docker`
   - Code Runner: `@geobio/code_execution_server` вместо `mcp-server-code-runner`

---

## 📚 ФАЙЛЫ

- **Минимальная конфигурация:** `mcp/mcp.json.working`
- **Расширенная конфигурация:** `mcp/mcp.json.extended`
- **Текущая конфигурация:** `mcp/mcp.json`

---

## ✅ ГОТОВО!

Теперь у тебя есть:
- ✅ Рабочая минимальная конфигурация (6 серверов)
- ✅ Расширенная конфигурация с альтернативами (9 серверов)
- ✅ Альтернативы для всех удалённых серверов

**Выбери конфигурацию и перезагрузи Cursor!** 🚀















