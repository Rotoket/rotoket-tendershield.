# 🚀 ПРАКТИЧЕСКИЙ ГАЙД: УСТАНОВКА MCP (выбери способ)

---

## 3 ВАРИАНТА ДЛЯ ВАШЕЙ СИТУАЦИИ

### ✅ ВАРИАНТ 1: CURSOR IDE (САМЫЙ ПРОСТОЙ)

**5 минут установки:**

```bash
npm install @modelcontextprotocol/server-git \
  @modelcontextprotocol/server-fetch \
  @modelcontextprotocol/server-memory
```

**Потом:**
- Создаешь `.cursorrules` файл (копируешь из гайда)
- Перезагружаешь Cursor
- Готово!

**Результат:**
- MCP работает в Cursor IDE
- Можешь тестировать с Claude/GPT-4
- Идеально для разработки

**Документ:** `MCP_Installation_Guide_Cursor_Ollama.md` → Способ #1

---

### 🟠 ВАРИАНТ 2: OLLAMA + PROXY (ДЛЯ ЛОКАЛЬНОГО AI)

**Если хочешь Ollama с MCP:**

```bash
# Установи proxy
npm install anthropic-mcp-proxy

# Запусти
mcp-proxy --port 3000 \
  --git node_modules/.bin/mcp-git \
  --fetch node_modules/.bin/mcp-fetch \
  --memory node_modules/.bin/mcp-memory

# В другом терминале запусти Ollama
OLLAMA_MCP_ENDPOINT=http://localhost:3000 ollama run mistral
```

**Результат:**
- Ollama может использовать MCP
- Работает локально на твоём компе
- Более мощно, чем просто Ollama

**Документ:** `MCP_Installation_Guide_Cursor_Ollama.md` → Способ #2

---

### 🟢 ВАРИАНТ 3: FASTAPI + MCP (PRODUCTION - РЕКОМЕНДУЕТСЯ)

**Лучше всего для вашей системы (FastAPI + React + Ollama):**

```bash
# 1. Установи Python пакеты
pip install anthropic-sdk mcp

# 2. Добавь мой код в FastAPI (app/services/mcp_service.py)

# 3. Добавь routes (app/api/mcp_routes.py)

# 4. Запусти
python -m uvicorn app.main:app --reload

# 5. Ollama подключится через API
```

**Результат:**
- MCP работает везде (Cursor, FastAPI, React, Ollama)
- Универсальное решение
- Готово для масштабирования
- Production-ready

**Документ:** `MCP_Installation_Guide_Cursor_Ollama.md` → Способ #3

---

## КАКОЙ ВЫБРАТЬ?

| Сценарий | Вариант | Время | Сложность |
|---|---|---|---|
| "Хочу попробовать MCP" | #1 Cursor | 5 мин | ⭐ |
| "Нужно Ollama с MCP" | #2 Proxy | 15 мин | ⭐⭐ |
| "Нужно для production" | #3 FastAPI | 30 мин | ⭐⭐⭐ |

---

## БЫСТРЫЙ СТАРТ

### Если ты сейчас в Cursor:

```bash
# 1. Открой терминал в Cursor
# 2. Скопируй и выполни:

npm install @modelcontextprotocol/server-git \
  @modelcontextprotocol/server-fetch \
  @modelcontextprotocol/server-memory

# 3. Жди 2 минуты

# 4. Готово!
```

### Если ты используешь Ollama:

Смотри Вариант #2 или #3 в гайде выше.

### Если ты хочешь production:

Используй Вариант #3 (FastAPI) — это универсально.

---

## ПОЛНЫЙ ГАЙД

👉 **[MCP_Installation_Guide_Cursor_Ollama.md](MCP_Installation_Guide_Cursor_Ollama.md)**

- Все 3 варианта с полным кодом
- Пошаговые инструкции
- Примеры конфигураций
- Решение проблем

---

## ГЛАВНОЕ

**MCP серверы будут работать везде:**
- ✅ В Cursor IDE
- ✅ В Ollama (через proxy или FastAPI)
- ✅ В вашем FastAPI приложении
- ✅ В React + Vite frontend (через API)
- ✅ С локальным Ollama на вашем компе

**Все 3 способа работают. Выбирай в зависимости от что тебе нужно.**

---

**Начнёшь с Варианта #1? Это займет 5 минут! 🚀**
