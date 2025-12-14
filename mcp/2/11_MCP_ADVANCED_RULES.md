# 🚀 РАСШИРЕННЫЙ MCP SETUP + CURSOR RULES (ПОЛНЫЙ ПАКЕТ)

## 📊 АНАЛИЗ ТВОИХ 3 УСТАНОВЛЕННЫХ MCP

### 1️⃣ SEQUENTIAL THINKING (✅ УСТАНОВЛЕН)
**Что это:** MCP сервер для структурированного решения сложных задач
**Работает:** Разбирает проблему на шаги, создаёт цепочку рассуждений
**Идеально для:**
- Планирование архитектуры перед кодингом
- Разбор сложных алгоритмов
- Дебаг перед тем как кодить
- Анализ требований (будут ли конфликты)

**Интеграция в Cursor:** Используй когда задача сложная
```
"Проанализируй как сделать batch API для анализа тендеров.
Используй sequential thinking для планирования."
```

---

### 2️⃣ CONTEXT7 (✅ УСТАНОВЛЕН)
**Что это:** Доступ к актуальной документации во время кодирования
**Работает:** Автоматически подтягивает свежие docs из интернета
**Идеально для:**
- FastAPI документация (актуальная версия)
- React/TypeScript (новые фичи)
- PostgreSQL (последние команды)
- Tailwind CSS (новые утилиты)

**Интеграция в Cursor:** Используй когда нужна свежая информация
```
"Создай API endpoint в FastAPI с authentication. use context7"
"Напиши React компонент с TypeScript. use context7"
```

---

### 3️⃣ PLAYWRIGHT MCP (✅ УСТАНОВЛЕН)
**Что это:** Браузерная автоматизация + тестирование
**Работает:** Управляет браузером, кликает, вводит, проверяет
**Идеально для:**
- E2E тесты для фронтенда
- Visual regression testing
- Тестирование после деплоя
- Проверка что UI работает (без ручного открытия браузера)

**Интеграция в Cursor:** Используй для автоматического тестирования
```
"Напиши Playwright тесты для DealBreakersTab"
"Проверь что форма анализа работает на всех браузерах"
```

---

## 📋 РЕКОМЕНДУЕМЫЕ ДОБАВИТЬ MCP (7 КРИТИЧНЫХ)

### Уже есть (3):
- ✅ Sequential Thinking (сложные задачи)
- ✅ Context7 (документация)
- ✅ Playwright (E2E тесты)

### Нужно добавить (7):

#### 1. **FILESYSTEM MCP** (КРИТИЧЕН)
**Что это:** Создание, чтение, редактирование файлов
**Почему:** Без этого Cursor не может создавать новые файлы автоматически
**Setup:** Обычно идёт с Cursor по умолчанию

#### 2. **GIT MCP** (КРИТИЧЕН)
**Что это:** Git коммиты, push, pull, status
**Почему:** Автоматические коммиты с правильными сообщениями
**Setup:**
```json
{
  "mcpServers": {
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    }
  }
}
```

#### 3. **DATABASE MCP (POSTGRESQL)** (КРИТИЧЕН)
**Что это:** Запуск SQL, создание миграций, управление БД
**Почему:** Автоматические миграции Alembic, выполнение SQL запросов
**Setup:**
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://tender_user:password@localhost:5432/tender_shield"
      }
    }
  }
}
```

#### 4. **DOCKER MCP** (ОЧЕНЬ ПОЛЕЗЕН)
**Что это:** Управление контейнерами, логи, экзекьют команды в контейнере
**Почему:** Запуск тестов в контейнере, проверка что всё в Docker работает
**Setup:**
```json
{
  "mcpServers": {
    "docker": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-docker"]
    }
  }
}
```

#### 5. **BROWSER MCP** (ОЧЕНЬ ПОЛЕЗЕН)
**Что это:** Открытие браузера, скриншоты, проверка визуального отображения
**Почему:** Без открытия браузера вручную видеть результаты UI
**Setup:**
```json
{
  "mcpServers": {
    "browser": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-browser"]
    }
  }
}
```

#### 6. **CODE QUALITY MCP** (ОЧЕНЬ ПОЛЕЗЕН)
**Что это:** Запуск тестов (pytest, jest), линтинг (eslint, pylint)
**Почему:** Автоматический запуск тестов после каждого создания компонента
**Setup:**
```json
{
  "mcpServers": {
    "codeQuality": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-code-quality"]
    }
  }
}
```

#### 7. **NPM/PACKAGE MCP** (ПОЛЕЗЕН)
**Что это:** Управление npm пакетами, версиями, зависимостями
**Почему:** Обновление пакетов, проверка конфликтов
**Setup:**
```json
{
  "mcpServers": {
    "npm": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-npm"]
    }
  }
}
```

---

## 🎯 ИТОГОВАЯ КОМАНДА: 10 MCP СЕРВЕРОВ

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
      "timeout": 60000
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"],
      "timeout": 30000
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-playwright"],
      "timeout": 120000
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"]
    },
    "git": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-git"]
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://tender_user:password@localhost:5432/tender_shield"
      }
    },
    "docker": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-docker"]
    },
    "browser": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-browser"]
    },
    "codeQuality": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-code-quality"]
    },
    "npm": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-npm"]
    }
  }
}
```

---

## 🔗 СИНЕРГИЯ: КАК MCP РАБОТАЮТ ВМЕСТЕ

### Типичный workflow разработки с твоей setup:

**Задача:** "Создай OpportunitiesTab компонент с тестами и визуально проверь"

**Executor:**

1. **Sequential Thinking MCP** (план)
   - Разбирает задачу: структура компонента, пропсы, логика

2. **Context7 MCP** (документация)
   - Подтягивает актуальные примеры React/TypeScript

3. **Filesystem MCP** (создание файлов)
   - Создаёт OpportunitiesTab.tsx в правильной папке
   - Обновляет imports в parent component

4. **Code Quality MCP** (тесты)
   - Генерирует тесты в OpportunitiesTab.test.tsx
   - Запускает jest, проверяет coverage

5. **Browser MCP** (визуально)
   - Открывает браузер на http://localhost:5173
   - Показывает компонент работающий в реальном браузере

6. **Git MCP** (сохранение)
   - Коммитит с правильным сообщением:
     `feat: Add OpportunitiesTab component with tests`

**Результат:** Всё за 30 секунд вместо 30 минут! ⚡

---

## 📝 НОВЫЕ CURSOR RULES (ПО КАЖДОМУ MCP)

Добавь эти rules в .cursorules файл:

---

## SEQUENTIAL THINKING MCP RULES

```markdown
## SEQUENTIAL THINKING - КОГДА ИСПОЛЬЗОВАТЬ

### Используй Sequential Thinking когда:

1. **Сложная архитектурная задача**
   Пример: "Спланируй как сделать batch API"
   Cursor:
   - Использует sequential_thinking для каждого шага
   - Выводит понятный план из N шагов
   - Потом выполняет каждый шаг

2. **Дебаг сложного бага**
   Пример: "Почему CORS ошибка при запросе к /api/analyze?"
   Cursor:
   - Step 1: Изучи frontend запрос (какие headers)
   - Step 2: Проверь backend CORS конфиг
   - Step 3: Проверь network tab в браузере
   - Step 4: Реши проблему

3. **Анализ требований перед кодированием**
   Пример: "Нужна поддержка batch анализа. Есть ли конфликты?"
   Cursor:
   - Step 1: Проверь текущую архитектуру
   - Step 2: Спрогнозируй проблемы
   - Step 3: Выведи список решений

### Типовой prompt:
```
"Спланируй добавление opportunities анализатора.
Используй sequential thinking - разбей на шаги:
1. Что нужно спарсить в тексте
2. Как это связано с deal breakers
3. Какие новые классы нужны
4. Как интегрировать в UI"
```

### Cursor должен:
- ✅ Предложить максимум 7 шагов (не больше)
- ✅ Вывести каждый шаг отдельно
- ✅ После плана спросить: "Начать выполнение?"
- ✅ Потом выполнить каждый шаг по очереди
```

---

## CONTEXT7 MCP RULES

```markdown
## CONTEXT7 - АКТУАЛЬНАЯ ДОКУМЕНТАЦИЯ

### Используй Context7 когда:
1. Разработка нового компонента с новой библиотекой
2. Интеграция с новым API
3. Обновление зависимостей (нужны новые примеры)
4. Сомневаешься в актуальности информации

### Типовой prompt:
```
"Создай FastAPI endpoint для batch анализа тендеров.
use context7 для актуальной документации FastAPI"

"Напиши React компонент для таблицы результатов.
use context7 для свежих примеров React 18"
```

### Cursor должен:
- ✅ Автоматически подтягивать docs через Context7
- ✅ Показывать версию документации которую использовал
- ✅ Использовать только примеры из свежих docs
- ✅ Указывать источник: "По официальной docs FastAPI v0.100+"

### Поддерживаемые библиотеки:
- FastAPI (backend)
- React, TypeScript (frontend)
- PostgreSQL (database)
- Tailwind CSS (styling)
- Next.js, Vue.js (если понадобятся)
```

---

## PLAYWRIGHT MCP RULES

```markdown
## PLAYWRIGHT - E2E ТЕСТИРОВАНИЕ И ВИЗУАЛЬНАЯ ПРОВЕРКА

### Используй Playwright когда:
1. Нужно написать E2E тесты
2. Нужно проверить UI работает в браузере
3. Нужно проверить кроссбраузерность (Chrome, Firefox, Safari)
4. Нужна визуальная регрессия (скриншоты)

### Типовой prompt:
```
"Напиши Playwright тесты для DealBreakersTab:
- Загрузить файл с тендером
- Нажать на кнопку анализа
- Проверить что результаты отображаются
- Проверить что можно скопировать текст"

"Проверь визуально что OpportunitiesTab выглядит хорошо
на разных разрешениях экрана (mobile, tablet, desktop)"
```

### Cursor должен:
- ✅ Генерировать .spec.ts файлы для каждого компонента
- ✅ Использовать `page.goto()`, `page.fill()`, `page.click()`
- ✅ Проверять видимость элементов через `page.isVisible()`
- ✅ Делать скриншоты для visual regression
- ✅ Запускать тесты во всех браузерах (headless)

### Структура теста:
```typescript
test('should analyze tender and show results', async ({ page }) => {
  // 1. Navigate
  await page.goto('http://localhost:5173');
  
  // 2. Upload file
  await page.fill('input[type="file"]', '/path/to/tender.txt');
  
  // 3. Click button
  await page.click('button:has-text("Analyze")');
  
  // 4. Wait for results
  await page.waitForSelector('[data-testid="deal-breakers"]');
  
  // 5. Assert
  await expect(page.locator('[data-testid="deal-breakers"]')).toBeVisible();
});
```

### Команда для запуска:
```bash
playwright test --headed  # с браузером видимым
playwright test           # headless
playwright show-report    # отчёт с результатами
```
```

---

## FILESYSTEM MCP RULES

```markdown
## FILESYSTEM - СОЗДАНИЕ И РЕДАКТИРОВАНИЕ ФАЙЛОВ

### Используй Filesystem когда:
- Создание нового компонента
- Создание нового файла API
- Редактирование существующего кода
- Удаление/переименование файлов

### Типовой prompt:
```
"Создай компонент OpportunitiesTab.tsx в src/components/Analysis/tabs/"
"Обновиши TenderAnalysisTabbed.tsx добавив импорт нового таба"
"Удали старый файл OldComponent.tsx"
```

### Cursor должен:
- ✅ Автоматически использовать Filesystem MCP
- ✅ Создавать файлы в правильных папках
- ✅ Обновлять parent файлы (imports)
- ✅ Показывать что создал:
   "✓ Created: src/components/Analysis/tabs/OpportunitiesTab.tsx"
   "✓ Updated: src/components/Analysis/TenderAnalysisTabbed.tsx"

### Не требует явного запроса - работает автоматически!
```

---

## GIT MCP RULES

```markdown
## GIT - АВТОМАТИЧЕСКИЕ КОММИТЫ И УПРАВЛЕНИЕ ВЕРСИЯМИ

### Используй Git когда:
- После создания нового компонента
- После написания тестов
- После исправления бага
- Перед началом новой фичи (checkout -b)

### Типовой prompt:
```
"После создания OpportunitiesTab закоммити изменения:
feat: Add OpportunitiesTab component with unit tests"

"Создай новую ветку для opportunities анализатора:
git checkout -b feature/opportunities-analyzer"
```

### Cursor должен:
- ✅ Автоматически запускать Git MCP после создания файлов
- ✅ Использовать правильные commit message prefixes:
   - `feat:` для новых фич
   - `fix:` для багов
   - `test:` для тестов
   - `docs:` для документации
   - `refactor:` для рефакторинга
- ✅ Показывать результат: "✓ Committed: feat: Add OpportunitiesTab..."

### Workflow:
```bash
# 1. Создать ветку
git checkout -b feature/opportunities

# 2. Создать компоненты (Filesystem MCP)
# 3. Написать тесты (Code Quality MCP)
# 4. Закоммитить (Git MCP)
# 5. Push на GitHub

# Result: ✓ Push to origin/feature/opportunities
```
```

---

## POSTGRES MCP RULES

```markdown
## POSTGRES - УПРАВЛЕНИЕ БАЗОЙ ДАННЫХ

### Используй Postgres когда:
- Нужна новая таблица или колонка
- Нужен SQL запрос к базе
- Нужна миграция Alembic
- Нужно проверить данные в БД

### Типовой prompt:
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

### Cursor должен:
- ✅ Генерировать CREATE TABLE запросы
- ✅ Создавать файлы миграций в alembic/versions/
- ✅ Выполнять SQL через Postgres MCP
- ✅ Показывать результаты запросов:
   ```
   ID          | SCORE | VERDICT
   -----------+-------+--------
   123-456     | 8     | HIGH
   789-012     | 5     | MEDIUM
   ```

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
```

---

## DOCKER MCP RULES

```markdown
## DOCKER - УПРАВЛЕНИЕ КОНТЕЙНЕРАМИ

### Используй Docker когда:
- Запуск контейнеров (docker-compose up)
- Проверка логов контейнера
- Выполнение команды внутри контейнера
- Проверка состояния контейнеров

### Типовой prompt:
```
"Запусти все контейнеры: docker-compose up -d"

"Покажи логи backend: docker logs -f tender-backend"

"Выполни миграции в backend:
docker exec tender-backend alembic upgrade head"

"Проверь что postgres работает:
docker exec tender-postgres psql -U tender_user -d tender_shield -c 'SELECT 1'"
```

### Cursor должен:
- ✅ Использовать Docker MCP для управления контейнерами
- ✅ Показывать статус контейнеров:
   ```
   CONTAINER ID   STATUS       PORTS
   abc123         Up 2 mins    0.0.0.0:8000->8000/tcp
   def456         Up 2 mins    0.0.0.0:5173->5173/tcp
   ```
- ✅ Выполнять команды внутри контейнеров
- ✅ Показывать логи для дебага

### Основные команды:
```bash
docker-compose up -d              # Запуск всех контейнеров
docker-compose down               # Остановка
docker logs -f service_name       # Логи контейнера
docker exec container_name cmd    # Выполнить команду в контейнере
docker ps                         # Список контейнеров
```
```

---

## BROWSER MCP RULES

```markdown
## BROWSER - ВИЗУАЛЬНАЯ ПРОВЕРКА И СКРИНШОТЫ

### Используй Browser когда:
- Нужно увидеть UI в браузере
- Нужны скриншоты для проверки
- Нужно проверить responsive design
- Нужна visual regression

### Типовой prompt:
```
"Открой браузер на http://localhost:5173 
и покажи скриншот как выглядит TenderAnalysisTabbed"

"Проверь responsive design:
- Desktop: 1920x1080
- Tablet: 768x1024
- Mobile: 375x667"

"Сравни скриншоты (visual regression) - изменилась ли кнопка?"
```

### Cursor должен:
- ✅ Автоматически открывать браузер
- ✅ Делать скриншоты в full page / viewport mode
- ✅ Проверять responsive на разных разрешениях
- ✅ Сохранять скриншоты для сравнения
- ✅ Показывать результаты в чате:
   ```
   ✓ Screenshot saved: screenshots/tender-analysis-desktop.png
   ✓ Layout looks good on mobile (375x667)
   ✓ No visual regressions detected
   ```

### Команды:
```bash
# Открыть браузер на URL
# Сделать скриншот
# Проверить responsive
# Сравнить с предыдущим скриншотом
```
```

---

## CODE QUALITY MCP RULES

```markdown
## CODE QUALITY - ТЕСТЫ И ЛИНТИНГ

### Используй Code Quality когда:
- Написал компонент - нужно запустить тесты
- Написал функцию - нужно запустить тесты
- Нужно проверить coverage
- Нужно запустить линтер (ESLint, Pylint)

### Типовой prompt:
```
"Напиши unit тесты для DealBreakerDetector:
- Test regex pattern matching
- Test penalty detection
- Test multiple breakers
И запусти тесты: pytest tests/test_deal_breaker_detector.py -v"

"Запусти ESLint на компоненты: npm run lint:fix"

"Проверь что coverage >= 80%: pytest --cov=. --cov-report=term"
```

### Cursor должен:
- ✅ Генерировать тесты с 80%+ coverage
- ✅ Запускать pytest для Python
- ✅ Запускать jest для TypeScript/React
- ✅ Запускать ESLint для code quality
- ✅ Показывать результаты:
   ```
   PASSED tests/test_deal_breaker_detector.py::test_regex_matching
   PASSED tests/test_deal_breaker_detector.py::test_penalty_detection
   PASSED tests/test_deal_breaker_detector.py::test_multiple_breakers
   ✓ Coverage: 85%
   ```

### Типовая структура теста:

**Python (pytest):**
```python
def test_detect_giant_penalty():
    detector = DealBreakerDetector()
    result = detector.detect_giant_penalty("штраф 1000000 руб")
    assert len(result) > 0
    assert result[0].penalty_amount == 1000000
```

**TypeScript (Jest):**
```typescript
test('should display deal breakers when loaded', () => {
  const { getByText } = render(<DealBreakersTab data={mockData} />);
  expect(getByText(/Giant Penalty/i)).toBeInTheDocument();
});
```
```

---

## NPM MCP RULES

```markdown
## NPM - УПРАВЛЕНИЕ ЗАВИСИМОСТЯМИ

### Используй NPM когда:
- Нужно добавить пакет
- Нужно обновить версию
- Нужно проверить конфликты зависимостей
- Нужно запустить скрипт из package.json

### Типовой prompt:
```
"Добавь пакет zustand для state management:
npm install zustand"

"Обновиши все пакеты до последней версии"

"Проверь нет ли конфликтов в зависимостях:
npm audit"

"Запусти dev сервер: npm run dev"
```

### Cursor должен:
- ✅ Использовать npm install / update
- ✅ Проверять версии конфликтов
- ✅ Запускать скрипты из package.json
- ✅ Показывать результаты:
   ```
   ✓ Installed zustand@4.4.0
   ✓ No vulnerabilities found
   ✓ Dev server running on http://localhost:5173
   ```

### Типовые скрипты:
```bash
npm run dev          # Запуск dev сервера
npm run build        # Build для production
npm run lint         # ESLint check
npm run test         # Запуск тестов
npm run test:watch  # Тесты в watch режиме
```
```

---

## 📊 МАТРИЦА ИСПОЛЬЗОВАНИЯ MCP

| Задача | MCP | Команда |
|--------|-----|---------|
| Спланировать архитектуру | Sequential Thinking | "Спланируй batch API" |
| Найти актуальные примеры | Context7 | "use context7" |
| Создать компонент | Filesystem | Автоматический |
| Написать тесты | Code Quality | "pytest tests/" |
| Проверить UI | Browser + Playwright | "Откройте браузер" |
| Коммитить | Git | Автоматический |
| Добавить таблицу в БД | Postgres | "CREATE TABLE..." |
| Запустить контейнеры | Docker | "docker-compose up" |
| Добавить пакет | NPM | "npm install X" |

---

## 🎯 ПРИМЕРЫ REAL-WORLD WORKFLOWS

### Workflow 1: Добавление нового компонента (30 сек)

**Ты:**
```
"Создай SmartQuestionsTab компонент с вопросами к РЗ"
```

**Cursor (автоматически):**
1. Sequential Thinking: Планирует структуру (пропсы, логика)
2. Context7: Подтягивает актуальные примеры React
3. Filesystem: Создаёт SmartQuestionsTab.tsx
4. Filesystem: Обновляет TenderAnalysisTabbed.tsx с импортом
5. Code Quality: Генерирует тесты, запускает jest
6. Browser: Открывает браузер, показывает результат
7. Git: Коммитит `feat: Add SmartQuestionsTab component`

**Результат:**
```
✓ Created: src/components/Analysis/tabs/SmartQuestionsTab.tsx
✓ Updated: src/components/Analysis/TenderAnalysisTabbed.tsx
✓ Tests passed: 95% coverage
✓ UI looks good on desktop/mobile
✓ Committed: feat: Add SmartQuestionsTab component
```

---

### Workflow 2: Добавление API endpoint (1 мин)

**Ты:**
```
"Добавь POST /api/opportunities endpoint.
use context7 для FastAPI документации"
```

**Cursor (автоматически):**
1. Sequential Thinking: Планирует endpoint
2. Context7: Подтягивает FastAPI примеры
3. Filesystem: Создаёт routes/opportunities.py
4. Filesystem: Обновляет main.py с импортом
5. Postgres: Генерирует миграцию для opportunities таблицы
6. Docker: Выполняет миграцию в контейнере
7. Code Quality: Генерирует тесты, запускает pytest
8. Git: Коммитит `feat: Add opportunities API endpoint`

**Результат:**
```
✓ Created: src/routes/opportunities.py
✓ Created: alembic/versions/add_opportunities_table.py
✓ Migrated: docker exec tender-backend alembic upgrade head
✓ Tests passed: 8 tests, 0 failures
✓ Committed: feat: Add opportunities API endpoint
```

---

### Workflow 3: Тестирование UI (2 мин)

**Ты:**
```
"Напиши Playwright тесты для TenderAnalysisTabbed.
Проверь что все 4 таба работают"
```

**Cursor (автоматически):**
1. Sequential Thinking: Планирует тест-кейсы
2. Playwright: Генерирует .spec.ts файл с тестами
3. Code Quality: Запускает playwright test
4. Browser: Открывает браузер, показывает выполнение
5. Git: Коммитит `test: Add Playwright tests for TenderAnalysisTabbed`

**Результат:**
```
✓ Created: e2e/tender-analysis.spec.ts
✓ Test: should load all 4 tabs ✓
✓ Test: should display deal breakers ✓
✓ Test: should show financial impact ✓
✓ Test: should show recommendations ✓
✓ All tests passed (4/4)
✓ Committed: test: Add Playwright tests for TenderAnalysisTabbed
```

---

### Workflow 4: Миграция БД (1 мин)

**Ты:**
```
"Добавь колонку last_updated к analyses таблице"
```

**Cursor (автоматически):**
1. Sequential Thinking: Планирует изменение
2. Postgres: Создаёт миграцию через SQLAlchemy
3. Filesystem: Создаёт файл в alembic/versions/
4. Docker: Выполняет миграцию в контейнере
5. Code Quality: Проверяет что миграция успешна
6. Git: Коммитит `feat: Add last_updated column to analyses table`

**Результат:**
```
✓ Created: alembic/versions/add_last_updated_to_analyses.py
✓ Migrated: Successfully applied
✓ Committed: feat: Add last_updated column to analyses table
```

---

## 🚀 ФИНАЛЬНЫЙ CHECKLIST

Скопируй весь этот файл в .cursorules:

```bash
# 1. Создай файл
touch ~/.cursor/mcp.json

# 2. Вставь JSON конфиг из "ИТОГОВАЯ КОМАНДА: 10 MCP СЕРВЕРОВ"

# 3. Перезагрузи Cursor

# 4. Проверь что все MCP загрузились:
# Cursor > Settings > MCP Servers > Проверь все 10 есть

# 5. Используй rules из этого файла в .cursorules
```

---

**ГОТОВО! Теперь твой Cursor работает с МОЩЬЮ 10 MCP серверов! 🚀**
