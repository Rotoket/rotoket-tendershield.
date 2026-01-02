# 🛡️ TENDER SHIELD PRO — ПОЛНЫЙ АНАЛИЗ ПРОЕКТА

**Дата анализа:** 2025-01-XX  
**Версия системы:** 1.0.0  
**Статус:** Production Ready (с ограничениями)

---

## 📋 ОГЛАВЛЕНИЕ

1. [Обзор проекта](#обзор-проекта)
2. [Архитектура системы](#архитектура-системы)
3. [Технологический стек](#технологический-стек)
4. [Структура проекта](#структура-проекта)
5. [Основные компоненты](#основные-компоненты)
6. [Бизнес-логика](#бизнес-логика)
7. [Известные проблемы и недостатки](#известные-проблемы-и-недостатки)
8. [Рекомендации по улучшению](#рекомендации-по-улучшению)
9. [Тестирование](#тестирование)
10. [Развертывание](#развертывание)

---

## 🎯 ОБЗОР ПРОЕКТА

### Что это?

**Tender Shield Pro** — система Decision Intelligence для анализа тендерной документации и принятия управленческих решений об участии/неучастии в тендерах.

### Целевая аудитория

- **Основной пользователь:** Директор / Владелец / Руководитель закупок
- **Вторичный пользователь:** Тендерный эксперт / Аналитик (подготовка, но не решение)

### Ключевая ценность

Помочь руководителю:
1. **Принять** решение об участии/неучастии в тендере
2. **Зафиксировать** решение с обоснованием
3. **Защитить** решение через Audit Trail и юридическую документацию

### Тип системы

**Decision Intelligence + Compliance Layer**  
Не BI-система, не GPT-чат, а инструмент фиксации управленческих решений.

---

## 🏗️ АРХИТЕКТУРА СИСТЕМЫ

### Общая архитектура

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │   UI     │  │  State   │  │ Services │             │
│  │Components│  │Management│  │   API    │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────────┐
│                 BACKEND (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │   API    │  │ Business │  │   Data   │            │
│  │ Endpoints│  │  Logic   │  │  Layer   │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│       │              │              │                  │
│       └──────────────┼──────────────┘                  │
│                     │                                  │
│  ┌──────────────────▼──────────────────┐               │
│  │      LLM Integration (Ollama)       │               │
│  │  - Document Analysis                │               │
│  │  - Risk Detection                   │               │
│  │  - Decision Preview Generation      │               │
│  └─────────────────────────────────────┘               │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              DATABASE (PostgreSQL/SQLite)               │
│  - Users, Tariffs, Usage                                │
│  - Analyses, PackageAnalyses                           │
│  - DecisionRecords, AuditTrail                         │
└─────────────────────────────────────────────────────────┘
```

### Архитектурные слои

#### 1. **Presentation Layer (Frontend)**
- React 19 + TypeScript
- Компонентная архитектура
- State management через React hooks
- API сервисы для коммуникации с backend

#### 2. **API Layer (Backend)**
- FastAPI REST API
- JWT аутентификация
- CORS middleware
- Rate limiting

#### 3. **Business Logic Layer**
- Document preprocessing
- Evidence extraction
- Reasoning engine
- Decision preview generation
- Risk classification

#### 4. **Data Layer**
- SQLAlchemy ORM
- PostgreSQL (production) / SQLite (development)
- JSON storage для результатов анализа
- Audit trail storage

#### 5. **AI/LLM Layer**
- Ollama integration
- Multiple model fallback
- Prompt engineering
- Response parsing

---

## 🛠️ ТЕХНОЛОГИЧЕСКИЙ СТЕК

### Backend

| Технология | Версия | Назначение |
|------------|--------|------------|
| Python | 3.10+ | Основной язык |
| FastAPI | 0.100+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| PostgreSQL | - | Production БД |
| SQLite | - | Development БД |
| Alembic | 1.12+ | Миграции БД |
| LangChain | 0.0.20+ | LLM интеграция |
| LangChain Ollama | 0.1.0+ | Ollama клиент |
| ChromaDB | 0.5.0+ | Vector DB для RAG |
| PyMuPDF | 1.23+ | PDF обработка |
| docx2txt | 0.8+ | DOCX обработка |
| Pandoc | - | Конвертация документов |
| python-jose | 3.3+ | JWT токены |
| passlib | 1.7.4+ | Хеширование паролей |
| reportlab | 4.0+ | PDF генерация |
| openpyxl | 3.1+ | Excel обработка |
| pytest | 7.4+ | Тестирование |

### Frontend

| Технология | Версия | Назначение |
|------------|--------|------------|
| React | 19.2.0 | UI библиотека |
| TypeScript | 5.8.2 | Типизация |
| Vite | 6.2.0 | Сборщик |
| Tailwind CSS | - | Стилизация |
| Lucide React | 0.554.0 | Иконки |
| Vitest | 2.1.8 | Unit тесты |
| Playwright | 1.49.0 | E2E тесты |

### Инфраструктура

- **Docker** — контейнеризация
- **Nginx** — reverse proxy (опционально)
- **Ollama** — локальный LLM сервер
- **MCP (Model Context Protocol)** — интеграция внешних инструментов

---

## 📁 СТРУКТУРА ПРОЕКТА

```
tender-shield-pro/
├── backend/                    # Backend приложение
│   ├── main.py                # Точка входа FastAPI
│   ├── config.py              # Конфигурация
│   ├── database.py            # Модели БД
│   ├── auth.py                # Авторизация
│   ├── schemas.py             # Pydantic схемы
│   ├── llm_client.py          # LLM клиент
│   ├── preprocessor.py        # Обработка документов
│   ├── reasoning_layer.py     # Reasoning engine
│   ├── decision_preview_formatter.py  # Форматирование Decision Preview
│   ├── audit_trail_manager.py # Audit Trail
│   ├── rag_engine.py          # RAG для базы знаний
│   ├── specialized_analyzers.py  # Отраслевые анализаторы
│   ├── services/             # Сервисы
│   │   ├── pandoc_service.py  # Pandoc интеграция
│   │   └── __init__.py
│   ├── prompts/               # Промпты для LLM
│   │   ├── decision_preview_canon.py
│   │   └── risk_evidence_canon.py
│   ├── tests/                 # Тесты
│   ├── alembic/               # Миграции БД
│   └── requirements.txt      # Зависимости
│
├── frontend/                  # Frontend приложение
│   ├── src/
│   │   ├── App.tsx            # Главный компонент
│   │   ├── components/        # React компоненты
│   │   │   ├── Auth.tsx       # Авторизация
│   │   │   ├── TenderAnalysis.tsx  # Анализ
│   │   │   ├── DecisionPreviewScreen.tsx
│   │   │   ├── audit/         # Компоненты аудита
│   │   │   └── decision/      # Компоненты решений
│   │   ├── services/          # API сервисы
│   │   │   ├── authService.ts
│   │   │   ├── geminiService.ts
│   │   │   └── profileService.ts
│   │   ├── utils/             # Утилиты
│   │   ├── types.ts            # TypeScript типы
│   │   └── context/           # React контексты
│   ├── tests/                 # Тесты
│   ├── package.json
│   └── vite.config.ts
│
├── infra/                     # Инфраструктура
│   ├── docker-compose.yml
│   └── nginx.conf
│
├── docs/                     # Документация
├── mcp/                       # MCP серверы
├── .cursorrules              # Правила проекта
└── start.bat                  # Скрипт запуска
```

---

## 🔧 ОСНОВНЫЕ КОМПОНЕНТЫ

### Backend компоненты

#### 1. **Document Analysis Pipeline**

**Файл:** `backend/main.py` (функция `analyze_single_file`)

**Процесс:**
1. Загрузка файла (PDF, DOCX, XLSX, XLS)
2. Извлечение текста (Pandoc → Docx2txt → PyMuPDF)
3. Preprocessing (Evidence extraction)
4. LLM анализ (Ollama)
5. Reasoning layer (классификация рисков)
6. Decision Preview generation
7. Сохранение в БД

**Ключевые функции:**
- `analyze_single_file()` — анализ одного документа
- `analyze_package()` — анализ пакета документов
- `_extract_text()` — извлечение текста из файла
- `_safe_ollama_invoke()` — безопасный вызов LLM с fallback

#### 2. **Authentication & Authorization**

**Файл:** `backend/auth.py`

**Функции:**
- `authenticate_user()` — проверка учетных данных
- `create_access_token()` — генерация JWT токена
- `get_current_user()` — получение пользователя из токена
- `get_password_hash()` — хеширование пароля (pbkdf2_sha256)

**Эндпоинты:**
- `POST /api/auth/register` — регистрация
- `POST /api/auth/login` — вход
- `GET /api/auth/me` — информация о пользователе
- `POST /api/auth/forgot-password` — запрос сброса пароля
- `POST /api/auth/reset-password` — сброс пароля

#### 3. **Database Models**

**Файл:** `backend/database.py`

**Модели:**
- `User` — пользователи (email, пароль, тариф, триал)
- `Tariff` — тарифные планы (Start, Pro, Enterprise)
- `Analysis` — анализы документов
- `PackageAnalysis` — пакетные анализы
- `DecisionRecord` — журнал решений
- `Usage` — учет использования (квоты)
- `DemoSession` — демо-сессии

#### 4. **Reasoning Layer**

**Файл:** `backend/reasoning_layer.py`

**Назначение:** Классификация рисков и генерация Decision Preview

**Классификация рисков:**
- `DEAL_BREAKER` — критический стоп-фактор
- `CONTROLLED_RISK` — управляемый риск
- `MARKET_NOISE` — рыночный фактор

#### 5. **Audit Trail**

**Файл:** `backend/audit_trail_manager.py`

**Назначение:** Фиксация всех действий для compliance

**События:**
- `decision_fixed` — решение зафиксировано
- `board_pack_generated` — Board Pack сгенерирован
- `compliance_exported` — экспорт для compliance

### Frontend компоненты

#### 1. **App.tsx**

**Назначение:** Главный роутер приложения

**Потоки:**
- Неавторизованные пользователи: Landing → Type Select → Analysis → Decision Preview → Post-Decision
- Авторизованные пользователи: Sidebar navigation

#### 2. **Auth.tsx**

**Назначение:** Авторизация и регистрация

**Функции:**
- Регистрация с автоматическим триалом
- Вход с JWT токеном
- Восстановление пароля

#### 3. **TenderAnalysis.tsx**

**Назначение:** Анализ тендерной документации

**Режимы:**
- Single mode — анализ одного документа
- Package mode — анализ пакета документов

#### 4. **DecisionPreviewScreen.tsx**

**Назначение:** Отображение Decision Preview для директора

**Компоненты:**
- Deal Snapshot
- Вердикт и ИУН
- Расшифровка ИУН
- Управляемые риски
- Action Plan
- Фиксация ответственности

---

## 💼 БИЗНЕС-ЛОГИКА

### Канонический порядок экранов

1. **Context** (Tender / Package Context)
2. **DealBreakersPanel**
3. **DecisionBlock** ← Decision Layer
4. **FinancialMetricsGrid**
5. **HeroVerdict**
6. **AIConsultantIntro**
7. **RiskNarrative**
8. **DecisionSupport**
9. **Details / Deep Dive**

### Decision Layer

**UserDecision типы:**
- `participate` — участвовать
- `participate_with_conditions` — участвовать с условиями
- `do_not_participate` — не участвовать
- `postpone` — отложить

**Правила:**
- Решение принимается ТОЛЬКО через DecisionBlock
- Решение необратимо (immutable)
- Любое решение → Audit Trail
- Без решения анализ считается НЕ завершённым

### ИУН (Индекс управленческой нагрузки)

**Компоненты:**
- **A (Конфликты условий)** — противоречия в документах
- **B (Финансовая экспозиция)** — риски кассовых разрывов
- **C (Юридико-процедурная нагрузка)** — сложность лицензий
- **D (Ручной операционный контроль)** — необходимость постоянного контроля

**Расчет:**
```
ИУН = Базовый риск (10) + Риск B + Риск C + Риск D
```

**Интерпретация:**
- ИУН < 30: Низкая управленческая нагрузка
- ИУН 30-50: Средняя управленческая нагрузка
- ИУН > 50: Высокая управленческая нагрузка (deal breaker для малого бизнеса)

### Система тарифов

| Тариф | Цена | Анализов/мес | Документов в пакете |
|-------|------|--------------|---------------------|
| Start | 2,990 ₽ | 50 | 5 |
| Pro | 9,990 ₽ | 200 | 10 |
| Enterprise | 29,990 ₽ | Безлимит | Безлимит |

**Триал:** 7 дней безлимитного доступа при регистрации

---

## ⚠️ ИЗВЕСТНЫЕ ПРОБЛЕМЫ И НЕДОСТАТКИ

> **Подробный отчет о тестировании авторизации:** см. `AUTH_TESTING_REPORT.md`

### Критические проблемы

#### 1. **Проблемы с авторизацией**

**Проблема:** Fallback пользователь в `authService.ts`
- При таймауте `/api/auth/me` создается fallback пользователь
- Это может привести к проблемам с правами доступа

**Файл:** `frontend/src/services/authService.ts` (строки 130-177)

**Решение:**
- Улучшить обработку ошибок
- Добавить retry механизм
- Убрать fallback пользователя в production

#### 2. **Кодировка в connection string**

**Проблема:** Проблемы с не-UTF-8 символами в пароле PostgreSQL

**Файл:** `backend/database.py` (строки 305-319)

**Решение:** URL-кодирование пароля реализовано, но нужны тесты

#### 3. **Timeout Ollama**

**Проблема:** Таймаут 300 секунд может быть недостаточным для больших документов

**Файл:** `backend/main.py` (функция `_safe_ollama_invoke`)

**Решение:**
- Асинхронная обработка через Celery
- Увеличение таймаута для больших документов

### Средние проблемы

#### 4. **Размер бандла фронтенда**

**Проблема:** Основной чанк 746 KB (предупреждение)

**Решение:**
- Code splitting
- Lazy loading компонентов
- Tree shaking

#### 5. **Deprecated функции**

**Проблема:**
- `@app.on_event("startup")` — заменено на `lifespan`
- `datetime.utcnow()` — предупреждения

**Статус:** Частично исправлено

#### 6. **База знаний не работает**

**Проблема:** При вводе вопроса в "База знаний" ничего не происходит

**Файл:** `frontend/src/components/KnowledgeView.tsx`

**Решение:** Проверить:
- Эндпоинт `/api/legal/search`
- RAG-движок (`rag_engine.py`)
- ChromaDB индексацию

#### 7. **Светлая тема не работает**

**Проблема:** Работает только тёмная тема

**Файл:** `frontend/src/components/Profile.tsx`

**Решение:** Проверить `toggleTheme()`, CSS переменные, Tailwind конфигурацию

### Низкие проблемы

#### 8. **TODO комментарии в коде**

**Найдено:** 21 TODO/FIXME комментарий

**Файлы:**
- `backend/main.py`
- `backend/preprocessor.py`
- `backend/ci_guards/prompt_abuse_guard.py`

#### 9. **Отсутствие мониторинга**

**Проблема:** Нет системы отслеживания ошибок в production

**Решение:**
- Интеграция Sentry
- Логирование в централизованную систему
- Метрики производительности

#### 10. **Отсутствие кеширования**

**Проблема:** Каждый анализ выполняется заново

**Решение:**
- Redis для кеширования результатов
- Кеширование промптов
- Кеширование извлеченных данных

---

## 🎯 РЕКОМЕНДАЦИИ ПО УЛУЧШЕНИЮ

### Немедленно (P0)

1. **Исправить авторизацию**
   - Убрать fallback пользователя
   - Улучшить обработку ошибок
   - Добавить retry механизм

2. **Исправить базу знаний**
   - Проверить RAG-движок
   - Проверить ChromaDB индексацию
   - Добавить логирование

3. **Исправить светлую тему**
   - Проверить CSS переменные
   - Проверить Tailwind конфигурацию

### Среднесрочно (P1)

4. **Асинхронная обработка**
   - Интеграция Celery
   - Фоновые задачи для анализа
   - WebSocket для прогресса

5. **Кеширование**
   - Redis интеграция
   - Кеширование результатов анализа
   - Кеширование промптов

6. **Мониторинг**
   - Sentry интеграция
   - Логирование в централизованную систему
   - Метрики производительности

### Долгосрочно (P2)

7. **Оптимизация бандла**
   - Code splitting
   - Lazy loading
   - Tree shaking

8. **Улучшение безопасности**
   - Rate limiting по IP
   - CSRF защита
   - Input validation

9. **Масштабируемость**
   - Горизонтальное масштабирование
   - Load balancing
   - Database sharding

---

## 🧪 ТЕСТИРОВАНИЕ

### Статистика тестов

| Категория | Количество | Успешность |
|-----------|------------|------------|
| Frontend Unit Tests | 55 | 100% ✅ |
| Backend Unit Tests | 51/54 | 94.4% ✅ |
| E2E Tests (Playwright) | 9 | ~80% ⚠️ |
| **Всего** | **115+** | **~90%** |

### Покрытие тестами

- ✅ Авторизация (15 тестов)
- ✅ Обработка ошибок API (10 тестов)
- ✅ Decision Preview v1.0 (6 тестов)
- ✅ Risk Extraction v2.1 (8 тестов)
- ⚠️ Интеграционные тесты (требуют настройки БД)

### Известные проблемы тестов

1. **Интеграционные тесты с БД**
   - Требуют настройки PostgreSQL
   - Проблема с кодировкой в connection string
   - **Решение:** Использовать SQLite для разработки

2. **Playwright тесты**
   - Устаревшие селекторы
   - **Решение:** Обновлены селекторы в последней версии

---

## 🚀 РАЗВЕРТЫВАНИЕ

### Требования

- Python 3.10+
- Node.js 18+
- PostgreSQL (production) или SQLite (development)
- Ollama с моделями (qwen2.5-coder:7b, qwen2.5:0.5b)

### Установка

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend

```bash
cd frontend
npm install
```

### Запуск

#### Development

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
./start.sh
```

#### Production

```bash
# Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run build
npm run preview
```

### Переменные окружения

**Backend (.env):**
```env
TENDER_OLLAMA_BASE_URL=http://localhost:11434
TENDER_OLLAMA_MODEL=qwen2.5-coder:7b
TENDER_DB_HOST=sqlite  # или localhost для PostgreSQL
TENDER_DB_NAME=tender_shield
TENDER_SECRET_KEY=your-secret-key-change-in-production
TENDER_CORS_ORIGINS=["http://localhost:5173"]
```

**Frontend (.env):**
```env
VITE_API_URL=http://localhost:8000/api
```

---

## 📊 МЕТРИКИ ПРОЕКТА

### Размер кодовой базы

- **Backend:** ~15,000 строк Python
- **Frontend:** ~10,000 строк TypeScript/TSX
- **Тесты:** ~3,000 строк
- **Документация:** ~5,000 строк Markdown

### Зависимости

- **Backend:** 30+ пакетов Python
- **Frontend:** 20+ пакетов npm

### Производительность

- **Время анализа документа:** 30-120 секунд (зависит от размера)
- **Размер бандла фронтенда:** 746 KB (215 KB gzip)
- **Время загрузки страницы:** < 2 секунд

---

## 🔒 БЕЗОПАСНОСТЬ

### Реализовано

- ✅ JWT токены для аутентификации
- ✅ Хеширование паролей (pbkdf2_sha256)
- ✅ CORS настройки
- ✅ Rate limiting (slowapi)
- ✅ Input validation (Pydantic)
- ✅ SQL injection защита (SQLAlchemy ORM)

### Требует улучшения

- ⚠️ CSRF защита
- ⚠️ Rate limiting по IP
- ⚠️ HTTPS в production
- ⚠️ Secrets management

---

## 📝 ЗАКЛЮЧЕНИЕ

**Tender Shield Pro** — зрелая система для анализа тендерной документации с четкой архитектурой и бизнес-логикой. Система готова к использованию, но требует доработки в области:

1. **Авторизация** — убрать fallback пользователя
2. **База знаний** — исправить работу RAG
3. **Мониторинг** — добавить систему отслеживания ошибок
4. **Производительность** — асинхронная обработка и кеширование

**Общая оценка:** 8/10

**Готовность к production:** 85%

---

**Последнее обновление:** 2025-01-XX  
**Автор анализа:** AI Assistant (Cursor)

