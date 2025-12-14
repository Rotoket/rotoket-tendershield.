# 🎯 ИНСТРУКЦИЯ: КАК ВСТАВИТЬ ВСЁ В CURSOR

## ШАГ 1: Скопируй JSON конфиг для MCP в Cursor

### ДЛЯ WINDOWS:
```
1. Открой: %APPDATA%\Cursor\mcp.json
2. ЕСЛИ ФАЙЛА НЕТ - создай его
3. Вставь содержимое ниже
```

### ДЛЯ MAC:
```
1. Открой: ~/Library/Application Support/Cursor/mcp.json
2. ЕСЛИ ФАЙЛА НЕТ - создай его
3. Вставь содержимое ниже
```

### ДЛЯ LINUX:
```
1. Открой: ~/.config/Cursor/mcp.json
2. ЕСЛИ ФАЙЛА НЕТ - создай его
3. Вставь содержимое ниже
```

---

## 🔧 ПОЛНАЯ КОНФИГУРАЦИЯ MCP ДЛЯ CURSOR

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

## ШАГ 2: Скопируй .cursorules в корень проекта

### Содержимое: `.cursorules`

Скопируй ВСЁ содержимое из файла `10_CURSOR_RULES.md` и добавь в конец НОВЫЕ ПРАВИЛА:

```markdown
# ... (содержимое из 10_CURSOR_RULES.md) ...

# ============================================================
# MCP INTEGRATION RULES (НОВОЕ)
# ============================================================

## SEQUENTIAL THINKING MCP

### Когда использовать:
- Сложная архитектурная задача
- Разбор сложного бага
- Анализ требований перед кодированием

### Как использовать:
```
"Спланируй добавление opportunities анализатора.
Используй sequential thinking - разбей на N шагов:
1. Что нужно спарсить
2. Как это связано с deal breakers
3. Какие новые классы нужны
4. Как интегрировать в UI"
```

### Что Cursor должен делать:
- ✅ Предложить не более 7 шагов
- ✅ Вывести каждый шаг отдельно
- ✅ После плана спросить: "Начать выполнение?"
- ✅ Потом выполнить каждый шаг по очереди

---

## CONTEXT7 MCP

### Когда использовать:
- Новый компонент с новой библиотекой
- Интеграция с новым API
- Обновление зависимостей
- Сомневаешься в актуальности информации

### Как использовать:
```
"Создай FastAPI endpoint для batch анализа.
use context7 для актуальной документации"

"Напиши React компонент.
use context7 для свежих примеров React 18"
```

### Что Cursor должен делать:
- ✅ Автоматически подтягивать docs через Context7
- ✅ Показывать версию документации
- ✅ Использовать только примеры из свежих docs
- ✅ Указывать источник: "По официальной docs FastAPI v0.100+"

---

## PLAYWRIGHT MCP

### Когда использовать:
- Написание E2E тестов
- Проверка что UI работает в браузере
- Проверка кроссбраузерности
- Визуальная регрессия

### Как использовать:
```
"Напиши Playwright тесты для DealBreakersTab:
- Загрузить файл с тендером
- Нажать на кнопку анализа
- Проверить что результаты отображаются"

"Проверь визуально OpportunitiesTab на разных разрешениях"
```

### Что Cursor должен делать:
- ✅ Генерировать .spec.ts файлы
- ✅ Использовать page.goto(), page.fill(), page.click()
- ✅ Проверять видимость элементов
- ✅ Делать скриншоты для visual regression
- ✅ Запускать тесты во всех браузерах

### Типовая структура:
```typescript
test('should analyze tender', async ({ page }) => {
  await page.goto('http://localhost:5173');
  await page.fill('input[type="file"]', '/path');
  await page.click('button:has-text("Analyze")');
  await page.waitForSelector('[data-testid="results"]');
  await expect(page.locator('[data-testid="results"]')).toBeVisible();
});
```

---

## FILESYSTEM MCP

### Когда использовать:
- Создание нового компонента
- Создание нового API endpoint
- Редактирование существующего кода
- Удаление/переименование файлов

### Как использовать:
```
"Создай компонент OpportunitiesTab.tsx в src/components/Analysis/tabs/"
"Обновиши TenderAnalysisTabbed.tsx добавив импорт нового таба"
```

### Что Cursor должен делать:
- ✅ Автоматически использовать Filesystem MCP
- ✅ Создавать файлы в правильных папках
- ✅ Обновлять parent файлы (imports)
- ✅ Показывать что создал

### Не требует явного запроса - работает автоматически!

---

## GIT MCP

### Когда использовать:
- После создания нового компонента
- После написания тестов
- После исправления бага
- Перед началом новой фичи

### Как использовать:
```
"После создания OpportunitiesTab закоммити:
feat: Add OpportunitiesTab component with tests"

"Создай новую ветку:
git checkout -b feature/opportunities-analyzer"
```

### Что Cursor должен делать:
- ✅ Автоматически запускать после создания файлов
- ✅ Использовать правильные prefixes:
   - feat: новые фичи
   - fix: баги
   - test: тесты
   - docs: документация
   - refactor: рефакторинг
- ✅ Показывать результат: "✓ Committed: feat: Add..."

### Workflow:
```bash
# 1. Создать ветку
git checkout -b feature/opportunities

# 2. Создать компоненты (Filesystem MCP)
# 3. Написать тесты (Code Quality MCP)
# 4. Закоммитить (Git MCP)
# 5. Push на GitHub
```

---

## POSTGRES MCP

### Когда использовать:
- Новая таблица или колонка
- SQL запрос к базе
- Миграция Alembic
- Проверка данных в БД

### Как использовать:
```
"Добавь новую таблицу opportunities:
- id (UUID)
- analysis_id (FK to analyses)
- opportunity_text (TEXT)
- category (VARCHAR)
- potential_benefit (FLOAT)

И создай миграцию Alembic"

"Выполни SQL: SELECT * FROM analyses WHERE score > 7 LIMIT 10"
```

### Что Cursor должен делать:
- ✅ Генерировать CREATE TABLE запросы
- ✅ Создавать файлы миграций в alembic/versions/
- ✅ Выполнять SQL через Postgres MCP
- ✅ Показывать результаты запросов

### Структура миграции:
```python
def upgrade() -> None:
    op.create_table(
        'opportunities',
        sa.Column('id', sa.UUID, primary_key=True),
        sa.Column('analysis_id', sa.UUID, sa.ForeignKey('analyses.id')),
        sa.Column('opportunity_text', sa.Text),
        sa.Column('category', sa.String(50)),
        sa.Column('potential_benefit', sa.Float)
    )

def downgrade() -> None:
    op.drop_table('opportunities')
```

### Команды:
```bash
alembic revision --autogenerate -m "Add opportunities table"
alembic upgrade head
```

---

## DOCKER MCP

### Когда использовать:
- Запуск контейнеров
- Проверка логов
- Выполнение команды в контейнере
- Проверка состояния контейнеров

### Как использовать:
```
"Запусти все контейнеры: docker-compose up -d"
"Покажи логи backend: docker logs -f tender-backend"
"Выполни миграции:
docker exec tender-backend alembic upgrade head"
```

### Что Cursor должен делать:
- ✅ Использовать Docker MCP для управления
- ✅ Показывать статус контейнеров
- ✅ Выполнять команды внутри контейнеров
- ✅ Показывать логи для дебага

### Основные команды:
```bash
docker-compose up -d              # Запуск
docker-compose down               # Остановка
docker logs -f service_name       # Логи
docker exec container cmd         # Выполнить команду
docker ps                         # Список контейнеров
```

---

## BROWSER MCP

### Когда использовать:
- Нужно увидеть UI в браузере
- Нужны скриншоты для проверки
- Проверка responsive design
- Visual regression

### Как использовать:
```
"Открой браузер на http://localhost:5173 
и покажи скриншот TenderAnalysisTabbed"

"Проверь responsive design:
- Desktop: 1920x1080
- Tablet: 768x1024
- Mobile: 375x667"
```

### Что Cursor должен делать:
- ✅ Автоматически открывать браузер
- ✅ Делать скриншоты
- ✅ Проверять responsive на разных разрешениях
- ✅ Сохранять скриншоты для сравнения
- ✅ Показывать результаты в чате

---

## CODE QUALITY MCP

### Когда использовать:
- Написал компонент - нужны тесты
- Написал функцию - нужны тесты
- Проверить coverage
- Запустить линтер

### Как использовать:
```
"Напиши unit тесты для DealBreakerDetector.
И запусти тесты: pytest tests/ -v"

"Запусти ESLint: npm run lint:fix"

"Проверь coverage: pytest --cov=. --cov-report=term"
```

### Что Cursor должен делать:
- ✅ Генерировать тесты с 80%+ coverage
- ✅ Запускать pytest для Python
- ✅ Запускать jest для TypeScript/React
- ✅ Запускать ESLint для code quality
- ✅ Показывать результаты

### Структура тестов:

**Python:**
```python
def test_detect_penalty():
    detector = DealBreakerDetector()
    result = detector.detect_giant_penalty("штраф 1000000 руб")
    assert len(result) > 0
    assert result[0].penalty_amount == 1000000
```

**TypeScript:**
```typescript
test('should display deal breakers', () => {
  const { getByText } = render(<DealBreakersTab data={mockData} />);
  expect(getByText(/Giant Penalty/i)).toBeInTheDocument();
});
```

---

## NPM MCP

### Когда использовать:
- Нужно добавить пакет
- Обновить версию
- Проверить конфликты
- Запустить скрипт

### Как использовать:
```
"Добавь zustand: npm install zustand"
"Обновиши все пакеты"
"Проверь конфликты: npm audit"
"Запусти dev: npm run dev"
```

### Что Cursor должен делать:
- ✅ Использовать npm install/update
- ✅ Проверять версии конфликтов
- ✅ Запускать скрипты из package.json
- ✅ Показывать результаты

### Типовые скрипты:
```bash
npm run dev          # Dev сервер
npm run build        # Production build
npm run lint         # ESLint check
npm run test         # Тесты
npm run test:watch  # Тесты в watch режиме
```

---

## 📊 МАТРИЦА ИСПОЛЬЗОВАНИЯ MCP

| Задача | MCP | Команда |
|--------|-----|---------|
| Спланировать | Sequential Thinking | "Спланируй batch API" |
| Актуальные примеры | Context7 | "use context7" |
| Создать файл | Filesystem | Автоматический |
| Тесты | Code Quality | "pytest tests/" |
| UI проверка | Browser + Playwright | "Откройте браузер" |
| Коммитить | Git | Автоматический |
| БД | Postgres | "CREATE TABLE..." |
| Контейнеры | Docker | "docker-compose up" |
| Пакеты | NPM | "npm install X" |

---

## 🎯 ПРИМЕРЫ WORKFLOWS

### Workflow: Добавить компонент (30 сек)

**Ты:**
```
"Создай SmartQuestionsTab с вопросами к РЗ"
```

**Cursor:**
1. Sequential Thinking: Планирует структуру
2. Context7: Подтягивает примеры React
3. Filesystem: Создаёт файл + обновляет imports
4. Code Quality: Генерирует тесты, запускает jest
5. Browser: Открывает браузер
6. Git: Коммитит `feat: Add SmartQuestionsTab`

**Результат:**
```
✓ Created: src/components/Analysis/tabs/SmartQuestionsTab.tsx
✓ Updated: src/components/Analysis/TenderAnalysisTabbed.tsx
✓ Tests passed: 95% coverage
✓ UI looks good
✓ Committed: feat: Add SmartQuestionsTab
```

---

### Workflow: Добавить API (1 мин)

**Ты:**
```
"Добавь POST /api/opportunities endpoint.
use context7"
```

**Cursor:**
1. Sequential Thinking: Планирует endpoint
2. Context7: Примеры FastAPI
3. Filesystem: Создаёт routes/opportunities.py
4. Postgres: Генерирует миграцию
5. Docker: Выполняет миграцию
6. Code Quality: Генерирует тесты, запускает pytest
7. Git: Коммитит `feat: Add opportunities API endpoint`

---

### Workflow: E2E тесты (2 мин)

**Ты:**
```
"Напиши Playwright тесты для TenderAnalysisTabbed"
```

**Cursor:**
1. Sequential Thinking: Планирует тест-кейсы
2. Playwright: Генерирует .spec.ts
3. Code Quality: Запускает playwright test
4. Browser: Открывает браузер
5. Git: Коммитит `test: Add Playwright tests`

---

## ✅ ФИНАЛЬНЫЙ CHECKLIST

Перед тем как начать работать:

- [ ] Скопировал JSON конфиг в .../Cursor/mcp.json
- [ ] Скопировал правила в .cursorules в корень проекта
- [ ] Перезагрузил Cursor
- [ ] Проверил что все 10 MCP загрузились (Cursor > Settings > MCP)
- [ ] Прочитал примеры workflows выше
- [ ] Готов использовать MCP с Cursor

---

## 🚀 READY TO GO!

Теперь твой Cursor работает с ПОЛНОЙ МОЩЬЮ!

**10 MCP серверов = 14x ускорение разработки**

Начни с простого:
```
"Создай OpportunitiesTab компонент"
```

И Cursor сделает ВСЁ автоматически! 🎉
