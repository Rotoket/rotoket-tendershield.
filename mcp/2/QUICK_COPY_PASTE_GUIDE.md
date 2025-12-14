# 🎯 КОПИПАСТИТЬ БЕЗ ВОПРОСОВ (ГОТОВЫЕ КОНФИГИ + КОМАНДЫ)

## 📋 СОДЕРЖИМОЕ mcp.json (СКОПИРУЙ ВСЁ)

Открой файл:
- **Windows:** `%APPDATA%\Cursor\mcp.json`
- **Mac:** `~/Library/Application Support/Cursor/mcp.json`
- **Linux:** `~/.config/Cursor/mcp.json`

Если файла нет - создай его.

Вставь следующее содержимое ПОЛНОСТЬЮ:

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "timeout": 60000,
      "description": "Structured problem-solving"
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "timeout": 30000,
      "description": "Real-time documentation"
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
      "description": "File operations"
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"],
      "description": "Git operations"
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://tender_user:password@localhost:5432/tender_shield"
      },
      "timeout": 30000,
      "description": "PostgreSQL operations"
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

**Готово! Сохрани файл и перезагрузи Cursor.**

---

## 📝 СОДЕРЖИМОЕ .cursorules (СКОПИРУЙ ВЕСЬ ФАЙЛ)

Создай в корне проекта файл `.cursorules` и скопируй содержимое из этого файла:

```markdown
# TENDER SHIELD PROJECT CURSOR RULES

## PROJECT CONTEXT
- **Project Name**: Tender Shield (TenderShield)
- **Type**: Full-stack AI-powered tender analysis platform
- **Tech Stack**: React 18 + TypeScript, FastAPI (Python 3.11), PostgreSQL, Ollama
- **Phase**: Phase 1 (Deal Breaker Detection + Financial Analysis)

## ФАЙЛОВАЯ СТРУКТУРА
```
tender-shield/
├── frontend/
│   ├── src/
│   │   ├── components/Analysis/
│   │   │   ├── TenderAnalysisTabbed.tsx
│   │   │   └── tabs/
│   │   │       ├── DealBreakersTab.tsx
│   │   │       ├── FinancialImpactTab.tsx
│   │   │       ├── RecommendationTab.tsx
│   │   │       └── SmartQuestionsTab.tsx
│   │   ├── api/
│   │   ├── hooks/
│   │   └── types/
│   └── tailwind.config.js
├── backend/
│   ├── main.py
│   ├── models/
│   ├── analyzers/
│   ├── routes/
│   ├── services/
│   ├── tests/
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
├── .cursorules (ЭТО ФАЙЛ)
└── .git
```

## CODING STANDARDS

### Frontend (React/TypeScript)
- Functional components with hooks
- PascalCase for components, camelCase for utils
- Import order: React > libraries > local components > styles
- Always type props with interfaces
- Semantic HTML, no inline styles
- CSS: Tailwind + CSS modules
- Test file: Component.test.tsx

### Backend (Python/FastAPI)
- Python 3.11+ syntax
- Type hints for all functions
- snake_case naming
- Max line: 100 chars
- Pydantic models for validation
- Async/await for I/O
- pytest for testing

### Database
- PostgreSQL dialect
- snake_case table/column names
- UUID primary keys
- JSONB for flexible data
- Foreign keys with CASCADE
- Alembic for migrations

## NAMING CONVENTIONS

### Components
```
UI Component: TenderAnalysisTabbed.tsx (noun + adjective)
Tab Component: DealBreakersTab.tsx (feature + Tab)
Utility: analyzeDocument.ts (verb + noun)
```

### API Endpoints
```
POST /api/analyze                    # Analyze tender
GET /api/analyses/{id}              # Get analysis
GET /api/analyses?limit=10&offset=0 # List with pagination
DELETE /api/analyses/{id}           # Delete
```

### Database
```
analyses table:
  - id (UUID PK)
  - user_id (UUID FK)
  - result_json (JSONB) ← dealBreakers[], financialSummary{}
  - score (INT)
  - verdict (VARCHAR)
  - created_at, updated_at
```

## COMMON PATTERNS

### React Component
```typescript
interface ComponentProps {
  data: AnalysisResult;
  onAction?: (action: string) => void;
}

export default function ComponentName({ data, onAction }: ComponentProps) {
  return <div>...</div>;
}
```

### FastAPI Endpoint
```python
@router.post("/api/analyze")
async def analyze_single_file(
    user_id: UUID,
    file: UploadFile,
    industry: str
) -> EnhancedAnalysisResult:
    try:
        # Logic here
        return result
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500)
```

### Testing Pattern

**Python (pytest):**
```python
def test_detect_giant_penalty():
    detector = DealBreakerDetector()
    result = detector.detect_giant_penalty("штраф 1000000 руб")
    assert len(result) > 0
```

**TypeScript (Jest):**
```typescript
test('should display deal breakers', () => {
  const { getByText } = render(<DealBreakersTab data={mockData} />);
  expect(getByText(/Штраф/i)).toBeInTheDocument();
});
```

## ERROR HANDLING

### Frontend
- try-catch for API calls
- User-friendly error messages
- No internal errors exposed
- Console.log only in development

### Backend
- Catch specific exceptions
- Log with context (user_id, file, error)
- Proper HTTP status codes
- Validate input before processing

## TESTING REQUIREMENTS

### Frontend
- Jest + React Testing Library
- 80%+ coverage
- Test user interactions
- Mock API with MSW

### Backend
- pytest with fixtures
- 80%+ coverage
- Test edge cases
- Use test database

## PERFORMANCE GUIDELINES

### Frontend
- Bundle: < 200KB (gzipped)
- Use code splitting
- Memoize expensive components
- Optimize images (webp, lazy load)

### Backend
- API response: < 60 seconds
- Deal breaker detection: < 5 seconds
- Use async/await for I/O
- Cache calculations
- Index database columns

## SECURITY

### Frontend
- No localStorage for auth tokens
- Use httpOnly cookies
- Escape user input
- Content-security-policy headers
- Validate file uploads

### Backend
- Validate all input
- Hash passwords (bcrypt)
- Prepared statements
- Rate limit API
- Log security events

## GIT WORKFLOW

### Branch Naming
```
feature/deal-breaker-detector
fix/financial-calculations
docs/api-documentation
test/add-unit-tests
```

### Commit Messages
```
feat: Add deal breaker detection
fix: Correct financial calculation
docs: Update README
test: Add analyzer tests
refactor: Simplify component
chore: Update dependencies
```

## MCP INTEGRATION RULES

### SEQUENTIAL THINKING

**Когда использовать:**
- Сложная архитектура
- Дебаг сложного бага
- Анализ требований

**Как использовать:**
```
"Спланируй opportunities анализатор.
Используй sequential thinking - разбей на шаги"
```

**Cursor должен:**
- ✅ Предложить не более 7 шагов
- ✅ Вывести каждый шаг отдельно
- ✅ После плана спросить: "Начать?"

### CONTEXT7

**Когда использовать:**
- Новый компонент
- Новый API
- Обновление зависимостей
- Сомневаешься в актуальности

**Как использовать:**
```
"Создай FastAPI endpoint. use context7"
"Напиши React компонент. use context7"
```

**Cursor должен:**
- ✅ Подтягивать docs через Context7
- ✅ Показывать версию документации
- ✅ Только примеры из свежих docs

### PLAYWRIGHT

**Когда использовать:**
- E2E тесты
- Проверка UI в браузере
- Кроссбраузерность
- Визуальная регрессия

**Как использовать:**
```
"Напиши Playwright тесты для DealBreakersTab:
- Загрузить файл
- Нажать анализ
- Проверить результаты"
```

**Cursor должен:**
- ✅ Генерировать .spec.ts файлы
- ✅ Использовать page.goto(), page.click()
- ✅ Проверять видимость элементов
- ✅ Делать скриншоты

### FILESYSTEM

**Когда использовать:**
- Создание компонента
- Создание API endpoint
- Редактирование кода
- Удаление файлов

**Как использовать:**
```
"Создай OpportunitiesTab в src/components/Analysis/tabs/"
"Обновиши TenderAnalysisTabbed.tsx добавив импорт"
```

**Cursor должен:**
- ✅ Создавать в правильных папках
- ✅ Обновлять parent imports
- ✅ Показывать что создал
- **Работает автоматически!**

### GIT

**Когда использовать:**
- После создания компонента
- После написания тестов
- После исправления бага
- Перед новой фичей

**Как использовать:**
```
"После создания закоммити:
feat: Add OpportunitiesTab component"
```

**Cursor должен:**
- ✅ Автоматический commit после создания
- ✅ Правильные prefixes (feat:, fix:, test:)
- ✅ Показывать результат

### POSTGRES

**Когда использовать:**
- Новая таблица
- SQL запрос
- Миграция Alembic
- Проверка данных

**Как использовать:**
```
"Добавь таблицу opportunities с полями...
И создай миграцию Alembic"
```

**Cursor должен:**
- ✅ Генерировать CREATE TABLE
- ✅ Создавать миграции
- ✅ Выполнять SQL запросы

### DOCKER

**Когда использовать:**
- Запуск контейнеров
- Проверка логов
- Выполнение команд в контейнере
- Проверка состояния

**Как использовать:**
```
"Запусти docker-compose up -d"
"Покажи логи backend"
"Выполни миграции в backend"
```

**Cursor должен:**
- ✅ Управлять контейнерами
- ✅ Показывать статус
- ✅ Выполнять команды внутри

### BROWSER

**Когда использовать:**
- Открыть UI в браузере
- Скриншоты для проверки
- Responsive design проверка
- Visual regression

**Как использовать:**
```
"Открой браузер на http://localhost:5173
и покажи скриншот TenderAnalysisTabbed"

"Проверь responsive:
- Desktop: 1920x1080
- Mobile: 375x667"
```

**Cursor должен:**
- ✅ Открывать браузер
- ✅ Делать скриншоты
- ✅ Проверять responsive
- ✅ Сравнивать (visual regression)

### CODE QUALITY

**Когда использовать:**
- Написал компонент - нужны тесты
- Написал функцию - нужны тесты
- Проверить coverage
- Запустить линтер

**Как использовать:**
```
"Напиши unit тесты для DealBreakerDetector.
И запусти тесты: pytest tests/ -v"

"Запусти ESLint: npm run lint:fix"
```

**Cursor должен:**
- ✅ Генерировать тесты (80%+ coverage)
- ✅ Запускать pytest, jest
- ✅ Запускать ESLint, Pylint
- ✅ Показывать результаты

### NPM

**Когда использовать:**
- Добавить пакет
- Обновить версию
- Проверить конфликты
- Запустить скрипт

**Как использовать:**
```
"Добавь zustand: npm install zustand"
"Обновиши пакеты"
"Запусти dev: npm run dev"
```

**Cursor должен:**
- ✅ npm install/update
- ✅ Проверять версии
- ✅ Запускать скрипты
- ✅ Показывать результаты

## QUICK MCP MATRIX

| Задача | MCP | Команда |
|--------|-----|---------|
| Спланировать | Sequential Thinking | "Спланируй..." |
| Примеры | Context7 | "use context7" |
| Файлы | Filesystem | Автоматический |
| Тесты | Code Quality | "pytest tests/" |
| UI | Browser + Playwright | "Открой браузер" |
| БД | Postgres | "CREATE TABLE..." |
| Контейнеры | Docker | "docker-compose up" |
| Git | Git | Автоматический |
| Пакеты | NPM | "npm install X" |

## DEBUGGING TIPS

### Frontend
- React DevTools для инспекции компонентов
- Network tab для API запросов
- Sparse console logging
- DevTools inspector для CSS

### Backend
- Use logging (не print)
- Check /api/health endpoint
- Monitor response times
- psql для прямого доступа к БД

### Docker
```bash
docker-compose logs -f backend
docker-compose logs -f postgres
docker ps  # список контейнеров
```

## CODE REVIEW CHECKLIST

- [ ] No `any` types
- [ ] Error handling present
- [ ] Input validation
- [ ] Tests pass (80%+)
- [ ] No hardcoded secrets
- [ ] Performance OK
- [ ] Docs updated
- [ ] Naming conventions followed

## USEFUL CURSOR COMMANDS

- "Create a new component [name]"
- "Write tests for [file]"
- "Fix this error [message]"
- "Refactor this function"
- "Add docstrings"
- "Create migration [change]"
- "Generate Playwright tests"
- "Setup batch API"

## PHASE 1 FOCUS

### Must-Have
- ✅ Deal breaker detection (regex, < 5 sec)
- ✅ Financial calculation (in rubles)
- ✅ Tab-based UI
- ✅ PostgreSQL storage
- ✅ Docker setup

### Phase 2
- 🔜 Opportunities analyzer
- 🔜 Smart questions generator
- 🔜 Batch API
- 🔜 ЕГРЮЛ integration
```

**Готово! Сохрани как `.cursorules` в корень проекта.**

---

## 🚀 КОМАНДЫ ДЛЯ ТЕРМИНАЛА (КОПИПАСТИТЬ)

```bash
# 1. Инициализировать проект
git init
git add .
git commit -m "docs: Initial setup with all documentation"

# 2. Запустить инфра
docker-compose up -d

# 3. Frontend
npm install
npm run dev
# Откроется на http://localhost:5173

# 4. Backend
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
# API на http://localhost:8000
# Docs на http://localhost:8000/docs

# 5. Тесты
pytest tests/ -v  # Backend
npm run test      # Frontend

# 6. Проверка инфры
curl http://localhost:8000/api/health
curl http://localhost:5173

# 7. Логи
docker-compose logs -f backend
docker-compose logs -f postgres
docker-compose logs -f frontend

# 8. Остановить
docker-compose down

# 9. Git push
git add .
git commit -m "feat: Add feature name"
git push origin feature-name
```

---

## ✅ ФИНАЛЬНЫЙ СПИСОК ФАЙЛОВ

```
tender-shield/
├── .cursorules                      ← Скопировано (Cursor rules)
├── .git/                             ← git init
├── mcp.json                          ← Скопировано (MCP config)
│
├── 00_ИТОГОВЫЙ_ОТЧЕТ.md            ← Документация
├── 03_FRONTEND_PHASE1.md
├── 04_BACKEND_PHASE1.md
├── 05_REAL_TIMELINE.md
├── 06_EXPERT_WEAPONS.md
├── 07_DATABASE_DOCKER.md
├── 08_FULL_ARCHITECTURE.md
├── 10_CURSOR_RULES.md
├── 11_MCP_ADVANCED_RULES.md
├── 12_CURSOR_SETUP_INSTRUCTIONS.md
├── FINAL_PACKAGE_SUMMARY.md
├── QUICK_COPY_PASTE_GUIDE.md        ← Этот файл
│
├── docker-compose.yml               ← Из 07_DATABASE_DOCKER.md
├── .env.example                      ← Из 07_DATABASE_DOCKER.md
├── Dockerfile (backend)              ← Из 07_DATABASE_DOCKER.md
├── Dockerfile (frontend)             ← Из 07_DATABASE_DOCKER.md
│
├── frontend/
│   ├── src/components/...           ← Из 03_FRONTEND_PHASE1.md
│   └── package.json
│
└── backend/
    ├── main.py                       ← Из 04_BACKEND_PHASE1.md
    ├── requirements.txt              ← Из 04_BACKEND_PHASE1.md
    ├── models/
    ├── analyzers/
    ├── routes/
    ├── tests/
    └── alembic/
```

---

## 🎯 ЧЕКЛИСТ ПОСЛЕ КОПИПАСТЫ

- [ ] Скопировал JSON в mcp.json
- [ ] Создал .cursorules в корне
- [ ] Перезагрузил Cursor
- [ ] Проверил что 10 MCP видны
- [ ] docker-compose up -d запустилось
- [ ] npm run dev работает
- [ ] http://localhost:5173 открывается
- [ ] http://localhost:8000/docs открывается
- [ ] Тесты проходят
- [ ] Первый коммит сделан

---

## 🎉 ГОТОВО!

**Всё что нужно скопировано. Начинай работать!**

Если забыл что-то - вернись к этому файлу. Всё здесь.
