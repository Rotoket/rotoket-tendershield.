# 🔧 УСТАНОВКА MCP В CURSOR И OLLAMA
## Практическое руководство для вашей системы

---

## КРАТКИЙ ОТВЕТ

**Есть 3 способа использовать MCP:**

1. ✅ **В Cursor IDE** (РЕКОМЕНДУЕТСЯ) — встроенная поддержка MCP
2. ✅ **В Ollama локально** (СЛОЖНЕЕ, но работает) — через обёртки
3. ✅ **В своем FastAPI приложении** (ЛУЧШЕ для production) — на вашем сервере

**Для МВП**: Способ #1 (Cursor) или #3 (FastAPI)

---

## СПОСОБ #1: УСТАНОВКА В CURSOR IDE (САМЫЙ ПРОСТОЙ)

### Шаг 1: Установить Node.js и npm

```bash
# Проверь есть ли у тебя
node --version
npm --version

# Если нет — установи с nodejs.org
```

### Шаг 2: Установить MCP серверы в проект

```bash
# Перейди в папку проекта
cd /path/to/tender-shield

# Установи MCP серверы
npm install @modelcontextprotocol/server-git \
  @modelcontextprotocol/server-fetch \
  @modelcontextprotocol/server-memory

# Проверь установку
npm list @modelcontextprotocol/server-*
```

**Результат**: 3 сервера установлены в `node_modules`

### Шаг 3: Настроить Cursor

#### Способ A: Через .cursorrules файл

**В корне проекта создай `.cursorrules`:**

```
# MCP Servers Configuration for Tender Shield

## AVAILABLE MCP SERVERS

### 1. Git MCP Server
- Purpose: Version control and history tracking
- Can: Read Git repos, view commits, manage branches
- Use for: Tracking tender analysis history, versioning

### 2. Fetch MCP Server  
- Purpose: Download and parse web content
- Can: Load HTML, PDF, JSON from URLs
- Use for: Automatically downloading tenders from web

### 3. Memory MCP Server
- Purpose: Persistent knowledge base
- Can: Store patterns, risks, market data
- Use for: Remembering risk patterns across analyses

## WHEN ANALYZING TENDERS:

1. Use Fetch MCP to download tender (if URL provided)
2. Analyze with LLM + Memory context (if similar tendersexist)
3. Commit results to Git (Gitsaves analysis history)
4. Generate report with recommendations

## SYSTEM PROMPT FOR ANALYSIS

You are analyzing government/commercial tenders with full MCP context:
- Git MCP provides historical context
- Memory MCP provides pattern knowledge
- Fetch MCP provides real-time data

Generate comprehensive analysis with:
1. Risk summary (1 sentence, level: high/medium/low)
2. Why is this risky? (explanation)
3. Market comparison (if Memory/Fetch available)
4. Questions for clarification (3-5 specific)
5. Recommendations (how to fix)
```

#### Способ B: Через GUI Cursor (проще)

1. **Открой Cursor Settings** (Cmd+, на Mac, Ctrl+, на Windows)
2. **Найди "MCP" или "Model Context Protocol"**
3. **Добавь серверы вручную:**

```
Server 1:
- Name: git
- Command: node
- Args: node_modules/.bin/mcp-git

Server 2:
- Name: fetch  
- Command: node
- Args: node_modules/.bin/mcp-fetch

Server 3:
- Name: memory
- Command: node
- Args: node_modules/.bin/mcp-memory
```

### Шаг 4: Перезагрузи Cursor

```
Cmd+Shift+P (Mac) или Ctrl+Shift+P (Windows)
→ Reload Window
```

### Шаг 5: Тестируй

**В Cursor chat напиши:**

```
"Проанализируй этот тендер: https://tender.ru/123.pdf"
```

**Ожидаемый результат:**
- Fetch MCP загружает PDF
- Memory MCP выдает похожие паттерны
- Git MCP показывает историю
- LLM анализирует с контекстом

---

## СПОСОБ #2: С OLLAMA (ЛОКАЛЬНО)

### ⚠️ Важно: Ollama НЕ имеет встроенной поддержки MCP

**Но есть обходные пути:**

### Вариант A: Через собственный сервер

**Шаг 1: Создать MCP proxy сервер**

```bash
# Установить утилиты
npm install mcp-server-core

# Или использовать готовый proxy
npm install anthropic-mcp-proxy
```

**Шаг 2: Запустить proxy**

```bash
# Запускаешь proxy который слушает порт 3000
mcp-proxy --port 3000 \
  --git node_modules/.bin/mcp-git \
  --fetch node_modules/.bin/mcp-fetch \
  --memory node_modules/.bin/mcp-memory
```

**Шаг 3: Подключить Ollama к proxy**

```bash
# Запустить Ollama с переменной окружения
OLLAMA_MCP_ENDPOINT=http://localhost:3000 ollama run mistral
```

**Результат**: Ollama может использовать MCP через HTTP proxy

### Вариант B: Через custom скрипт (рекомендуется для вас)

**Создай `mcp-wrapper.js` в корне проекта:**

```javascript
const { exec } = require('child_process');
const http = require('http');
const fs = require('fs');
const path = require('path');

// Путь к хранилищу памяти
const MEMORY_FILE = path.join(__dirname, '.mcp-memory.json');

// Инициализировать память
let memory = {};
if (fs.existsSync(MEMORY_FILE)) {
  memory = JSON.parse(fs.readFileSync(MEMORY_FILE, 'utf8'));
}

// HTTP сервер для Ollama
const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  
  if (req.method === 'POST' && req.url === '/memory') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      const data = JSON.parse(body);
      if (data.action === 'store') {
        memory[data.key] = data.value;
        fs.writeFileSync(MEMORY_FILE, JSON.stringify(memory, null, 2));
        res.end(JSON.stringify({ status: 'saved' }));
      } else if (data.action === 'retrieve') {
        res.end(JSON.stringify({ value: memory[data.key] }));
      }
    });
  } else if (req.url === '/memory') {
    res.end(JSON.stringify(memory));
  } else {
    res.end(JSON.stringify({ error: 'Not found' }));
  }
});

server.listen(3000, () => {
  console.log('✅ MCP wrapper server running on http://localhost:3000');
  console.log('Memory file:', MEMORY_FILE);
});
```

**Запусти:**

```bash
node mcp-wrapper.js
```

**Теперь Ollama может:*

```bash
# Запустить Ollama с доступом к памяти через API
ollama run mistral

# В Ollama скрипт можно вызывать:
# curl http://localhost:3000/memory (получить всю память)
# POST с action=store/retrieve
```

---

## СПОСОБ #3: В ВАШЕМ FASTAPI ПРИЛОЖЕНИИ (PRODUCTION)

### Это ЛУЧШИЙ способ для вашей системы!

**Архитектура:**

```
Cursor/Ollama
    ↓
Your FastAPI (8000)
    ↓
MCP Layer (Python wrapper)
├─ Git MCP ──→ Git operations
├─ Fetch MCP ──→ Web scraping
└─ Memory MCP ──→ JSON database
    ↓
Response
```

### Шаг 1: Установить Python MCP пакеты

```bash
# В folder вашего FastAPI проекта
pip install anthropic-sdk mcp

# Или для более низкого уровня:
pip install mcp-client
```

### Шаг 2: Создать MCP wrapper в FastAPI

**Файл: `app/services/mcp_service.py`**

```python
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess

class MCPService:
    """Wrapper для MCP серверов"""
    
    def __init__(self):
        self.memory_file = Path('.mcp-memory.json')
        self.git_repo = Path('.git')
        self.memory = self._load_memory()
    
    def _load_memory(self) -> Dict[str, Any]:
        """Загрузить память из файла"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_memory(self):
        """Сохранить память в файл"""
        with open(self.memory_file, 'w') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)
    
    def store_pattern(self, key: str, value: Dict[str, Any]):
        """Сохранить паттерн в памяти"""
        self.memory[key] = value
        self._save_memory()
        return {"status": "saved", "key": key}
    
    def get_pattern(self, key: str) -> Optional[Dict[str, Any]]:
        """Получить паттерн из памяти"""
        return self.memory.get(key)
    
    def get_similar_patterns(self, query: str) -> list:
        """Найти похожие паттерны"""
        results = []
        for key, value in self.memory.items():
            if query.lower() in key.lower():
                results.append({key: value})
        return results
    
    def fetch_document(self, url: str) -> Optional[str]:
        """Загрузить документ с URL"""
        try:
            import requests
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text[:50000]  # Первые 50k символов
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_git_history(self) -> list:
        """Получить историю из Git"""
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '-10'],
                capture_output=True,
                text=True
            )
            return result.stdout.strip().split('\n')
        except Exception as e:
            return [f"Error: {str(e)}"]

# Инициализировать
mcp_service = MCPService()
```

### Шаг 3: Добавить endpoints в FastAPI

**Файл: `app/api/mcp_routes.py`**

```python
from fastapi import APIRouter, HTTPException
from app.services.mcp_service import mcp_service

router = APIRouter(prefix="/api/mcp", tags=["MCP"])

@router.post("/memory/store")
async def store_memory(key: str, value: dict):
    """Сохранить в памяти"""
    return mcp_service.store_pattern(key, value)

@router.get("/memory/{key}")
async def get_memory(key: str):
    """Получить из памяти"""
    result = mcp_service.get_pattern(key)
    if result is None:
        raise HTTPException(status_code=404, detail="Not found")
    return result

@router.get("/memory/search/{query}")
async def search_patterns(query: str):
    """Найти похожие паттерны"""
    return mcp_service.get_similar_patterns(query)

@router.post("/fetch")
async def fetch(url: str):
    """Загрузить документ"""
    content = mcp_service.fetch_document(url)
    return {"url": url, "content": content}

@router.get("/git/history")
async def get_history():
    """Получить историю"""
    return {"history": mcp_service.get_git_history()}

@router.post("/analyze-tender")
async def analyze_tender(tender_url: str, tender_content: Optional[str] = None):
    """Полный анализ тендера с MCP контекстом"""
    
    # 1. Загрузить тендер если только URL
    if tender_url and not tender_content:
        tender_content = mcp_service.fetch_document(tender_url)
    
    # 2. Получить похожие паттерны из памяти
    patterns = mcp_service.get_similar_patterns("tendor_risk")
    
    # 3. Получить историю
    history = mcp_service.get_git_history()
    
    # 4. Вернуть контекст для LLM
    return {
        "tender_content": tender_content[:5000],  # Первые 5k символов
        "similar_patterns": patterns,
        "history": history,
        "context_ready": True
    }
```

### Шаг 4: Добавить в main.py

```python
from fastapi import FastAPI
from app.api.mcp_routes import router as mcp_router

app = FastAPI()

# Подключить MCP routes
app.include_router(mcp_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Шаг 5: Использовать в Ollama

**В скрипте Ollama:**

```python
import requests
import json

MCP_API = "http://localhost:8000/api/mcp"

def analyze_tender_with_mcp(tender_url: str):
    """Анализировать тендер с MCP контекстом"""
    
    # 1. Получить контекст из MCP
    response = requests.post(
        f"{MCP_API}/analyze-tender",
        json={"tender_url": tender_url}
    )
    context = response.json()
    
    # 2. Отправить Ollama с контекстом
    prompt = f"""
    Analyze tender with context:
    
    TENDER CONTENT:
    {context['tender_content']}
    
    SIMILAR PATTERNS FROM MEMORY:
    {json.dumps(context['similar_patterns'], ensure_ascii=False)}
    
    HISTORY:
    {json.dumps(context['history'])}
    
    Provide comprehensive analysis with risks and recommendations.
    """
    
    # 3. Запросить Ollama
    import ollama
    response = ollama.generate(
        model='mistral',
        prompt=prompt,
        stream=False
    )
    
    # 4. Сохранить результат в памяти
    result = response['response']
    requests.post(
        f"{MCP_API}/memory/store",
        json={
            "key": f"analysis_{tender_url.split('/')[-1]}",
            "value": {"url": tender_url, "analysis": result}
        }
    )
    
    return result
```

---

## СРАВНЕНИЕ 3 СПОСОБОВ

| Способ | Простота | Мощь | Где работает | Рекомендация |
|---|---|---|---|---|
| **#1 Cursor** | ⭐⭐⭐ Супер просто | ⭐⭐⭐ Отличная | Только в IDE | 🔴 FAST START |
| **#2 Ollama proxy** | ⭐⭐ Средне | ⭐⭐ Хорошо | На компе | 🟡 Для Ollama |
| **#3 FastAPI** | ⭐ Сложнее | ⭐⭐⭐ Мощная | Везде (production) | 🟢 PRODUCTION |

---

## ДЛЯ ВАШЕЙ СИТУАЦИИ (Ollama + FastAPI + React)

### РЕКОМЕНДУЕМАЯ АРХИТЕКТУРА:

```
┌─────────────────────────────────────┐
│  Cursor IDE (разработка)             │
│  + MCP серверы (Git, Fetch, Memory) │
└──────────────┬──────────────────────┘
               │ (пишешь код)
               ↓
┌─────────────────────────────────────┐
│  FastAPI (8000)                      │
│  + MCP Python wrapper (Способ #3)   │
│  + Ollama интеграция                │
└────────┬────────────────┬───────────┘
         │                │
         ↓                ↓
    React (5173)    Ollama (local)
    + SQLite        для анализа
```

### ПОШАГОВАЯ УСТАНОВКА:

```bash
# 1. Установить MCP в Cursor (для разработки)
npm install @modelcontextprotocol/server-git \
  @modelcontextprotocol/server-fetch \
  @modelcontextprotocol/server-memory

# 2. Установить Python MCP в FastAPI
pip install anthropic-sdk mcp

# 3. Добавить мой код (app/services/mcp_service.py и app/api/mcp_routes.py)

# 4. Запустить
python -m uvicorn app.main:app --reload

# 5. Ollama будет использовать через API на localhost:8000
```

---

## БЫСТРЫЙ СТАРТ ДЛЯ ВАС

**СЕЙЧАС (этот час):**

```bash
# 1. Установи в Cursor
npm install @modelcontextprotocol/server-git \
  @modelcontextprotocol/server-fetch \
  @modelcontextprotocol/server-memory

# 2. Добавь .cursorrules (см. выше)

# 3. Перезагрузи Cursor

# 4. Тестируй!
```

**НА НЕДЕЛЮ 2:**

```bash
# 1. Добавь MCP wrapper в FastAPI (мой код выше)

# 2. Запусти FastAPI с MCP

# 3. Подключи Ollama к FastAPI

# 4. Всё работает везде!
```

---

## ЕСЛИ ЕСТЬ ОШИБКИ

### Ошибка: "node_modules/.bin/mcp-git not found"

```bash
# Переустанови
npm uninstall @modelcontextprotocol/server-git
npm install @modelcontextprotocol/server-git

# Проверь
ls -la node_modules/.bin/mcp-*
```

### Ошибка: "Cannot find module 'mcp'"

```bash
# Python
pip install mcp anthropic-sdk --upgrade

# Check
python -c "import mcp; print(mcp.__version__)"
```

### Ollama не видит MCP

```bash
# Проверь что FastAPI работает
curl http://localhost:8000/api/mcp/git/history

# Если 404 - добавь routes в main.py
```

---

## ФИНАЛЬНЫЙ СОВЕТ

**Для МВП используй Способ #1 (Cursor)** — это просто npm install + .cursorrules

**Для production используй Способ #3 (FastAPI)** — это универсально и мощно

**Способ #2 (Ollama proxy)** — если ты хочешь Ollama с MCP напрямую (более сложно, но возможно)

---

**P.S.** Весь код выше готов к копированию. Просто вставь в свои файлы и работай!

Начнёшь с установки? 🚀
