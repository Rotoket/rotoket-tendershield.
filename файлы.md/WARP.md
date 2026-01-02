# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Коротко о репозитории
Tender Shield Pro — сервис для анализа тендерной документации (44‑ФЗ/223‑ФЗ) и поддержки управленческого решения «участвовать / не участвовать».

Репозиторий — full-stack:
- `backend/` — FastAPI API + анализаторы + LLM/RAG + авторизация/тарифы/платежи.
- `frontend/` — React + TypeScript + Vite SPA.
- `infra/` — docker-compose (Postgres, ChromaDB, backend, frontend) + nginx конфиг.

## Команды (локальная разработка)

### Быстрый старт (Windows)
Запускает Ollama (если доступна), backend и frontend в отдельных окнах:
- PowerShell: `./start.ps1`
- CMD: `start.bat`

### Backend (FastAPI, Python)
Зависимости и окружение:
- `cd backend`
- `python -m venv venv`
- PowerShell: `./venv/Scripts/Activate.ps1`
- `pip install -r requirements.txt`

Переменные окружения:
- Backend читает `.env` через `backend/config.py` (префикс `TENDER_`).
- В репозитории есть шаблон `backend/env.example` (это НЕ `.env.example`).
  - Скопируйте в `backend/.env` и отредактируйте при необходимости.

Запуск:
- Dev (рекомендуется): `uvicorn main:app --reload --host 0.0.0.0 --port 8000`
- Healthcheck: `GET http://localhost:8000/api/health`
- Swagger: `http://localhost:8000/docs`

База данных:
- По умолчанию ожидается PostgreSQL (параметры `TENDER_DB_*`).
- Для «безболезненного» dev-режима без Postgres есть принудительный fallback:
  - если `TENDER_DB_HOST=sqlite`, используется SQLite файл `backend/tender_shield.db` (см. `backend/database.py`).

Тесты:
- Все тесты: `pytest`
- Через хелпер: `python run_tests.py`
- Один файл/тест:
  - `pytest tests/test_foo.py`
  - `pytest tests/test_foo.py::test_bar`

### Frontend (React + Vite)
Установка/запуск:
- `cd frontend`
- `npm install`
- `npm run dev` (Vite на `http://localhost:5173`)

API URL:
- Клиент использует `import.meta.env.VITE_API_URL` или дефолт `http://localhost:8000/api` (см. `frontend/src/services/api.ts`, `frontend/src/services/geminiService.ts`, `frontend/src/services/authService.ts`).
- Если нужно переопределить — создайте `frontend/.env` и задайте `VITE_API_URL=...`.

Unit-тесты:
- `npm test` (vitest run)
- Watch: `npm run test:watch`
- Один тестовый файл (vitest): `npm test -- src/utils/logger.test.ts`

E2E (Playwright):
- Все e2e: `npx playwright test`
- Один spec: `npx playwright test tests/e2e/auth.spec.ts`

### Docker / infra
- Поднять инфраструктуру: `docker compose -f infra/docker-compose.yml up --build`
  - сервисы: Postgres (`:5432`), ChromaDB (`:8001`), backend (`:8000`), frontend (`:80`).

Примечание по docker-сборке фронта:
- `frontend/Dockerfile` делает `COPY infra/nginx.conf /etc/nginx/nginx.conf`, но в текущем дереве nginx конфиг лежит в `infra/nginx.conf` (вне build context `frontend/`). Если сборка `frontend` падает — сначала проверьте этот путь.

## Архитектура (big picture)

### Поток данных «пользователь → решение»
1) Frontend принимает файлы (single или package) и отправляет их в backend (FormData):
   - single: `POST /api/analyze` (`frontend/src/services/geminiService.ts:analyzeDocument`)
   - package: `POST /api/analyze-package` (`...:analyzePackage`)
2) Backend извлекает текст из PDF/DOCX, выполняет эвристики + LLM (Ollama), опционально подтягивает правовые сниппеты через RAG.
3) Frontend отображает результат через «каноническую» структуру экрана анализа и требует фиксации решения пользователем.

### Backend: ключевые узлы
- Точка входа API: `backend/main.py`
  - содержит основной FastAPI app и большинство эндпоинтов: анализ, auth, история, payments.
- Конфигурация: `backend/config.py`
  - `Settings` (Pydantic Settings), env-prefix `TENDER_`, чтение `.env`.
- LLM клиент: `backend/llm_client.py`
  - `get_analysis_llm()`/`get_chat_llm()` (ChatOllama), retry helper `invoke_with_retry()`.
- RAG по правовой базе: `backend/rag_engine.py`
  - Chroma (persisted в `backend/chroma_db/`), embeddings через Ollama; при проблемах возвращает пусто (не ломает анализ).
- БД и доменные модели: `backend/database.py`
  - SQLAlchemy модели `User`, `Tariff`, `Usage`, `Analysis`, `PackageAnalysis`, `DemoSession`, `GeneratedDocument`, `PasswordResetToken`.
  - Встроенная поддержка Postgres + режим SQLite по `TENDER_DB_HOST=sqlite`.
- Авторизация: `backend/auth.py`
  - JWT (`/api/auth/*`), токен хранится на фронте в localStorage.
- Платежи: `backend/payment.py`
  - YooKassa, в dev автоматически включается mock-режим (если ключи не заданы).

### Frontend: ключевые узлы
- Точка входа UI: `frontend/src/App.tsx`
  - переключение «экранов» через `AppView` (см. `frontend/src/types.ts`), проверка токена через `frontend/src/services/authService.ts`.
- Главные экраны анализа:
  - `frontend/src/components/Analyzer.tsx` — single документ.
  - `frontend/src/components/ComplexAudit.tsx` — пакет документов.
  - `frontend/src/components/TenderAnalysis.tsx` — переключатель режима (single/package).
- API слой:
  - `frontend/src/services/api.ts` — низкоуровневый fetch helper.
  - `frontend/src/services/geminiService.ts` — основной клиент к backend для анализа/чата/истории/поиска норм.
  - `frontend/src/services/authService.ts` — login/register/me + хранение JWT.
- Типы данных (важно держать синхронно с backend-JSON): `frontend/src/types.ts`.
- История решений (Decision Layer): `frontend/src/services/decisionHistoryService.ts`
  - каноническое хранилище истории — localStorage, сущность `TenderDecisionRecord`.

## Продуктовые/UX инварианты (из `.cursorrules`)
Эти правила важнее «красоты кода» и должны соблюдаться на ключевых экранах анализа.

1) Язык интерфейса — русский.
2) Экран анализа должен позволять принять решение быстро: сначала стоп‑факторы и финансово‑правовой удар, потом детали.
3) Канон порядка блоков на экранах анализа (как минимум для `Analyzer.tsx` и `ComplexAudit.tsx`):
   - `TenderContextPanel` / `PackageContextPanel` (только факты)
   - `HeroVerdict`
   - `AIConsultantIntro`
   - `FinancialMetricsGrid`
   - `DealBreakersPanel` (только HIGH/CRITICAL; не дублировать в других блоках)
   - `DecisionBlock` (единственная точка фиксации решения)
   - `RiskNarrative` (единственное место для «глобальных» рисков + интеграция с базой знаний)
   - `DecisionSupport`
   - Deep Dive по выбранному документу
4) DealBreakers vs Risks:
   - `DealBreakersPanel` — только HIGH/CRITICAL; если риск попал сюда, не дублировать его в `RiskNarrative` и других блоках.
5) История = факт решения, а не полный отчёт:
   - сохранять решения через `decisionHistoryService.saveDecisionToHistory()`; не распылять запись истории по компонентам.
6) Триал/платежи/авторизация:
   - не менять логику триала (7 дней) и IP-ограничения регистрации без явной просьбы;
   - YooKassa: в dev допустим mock-режим, не требующий реальных ключей (см. `backend/payment.py`).
7) LLM/RAG устойчивость важнее «идеальной точности»:
   - не удалять существующие fallback/деградации при ошибках Ollama/RAG;
   - правовые сниппеты подтягивать через `backend/rag_engine.py:get_law_snippets()` (если слой доступен), при ошибках — корректная деградация.

