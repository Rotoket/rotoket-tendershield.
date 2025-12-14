# Tender Shield Pro

SaaS-сервис для **интеллектуального анализа тендерной документации РФ** (44-ФЗ / 223-ФЗ и смежные нормы), который позволяет тендерному специалисту за **2–3 минуты** получить уровень понимания, на который раньше уходили **2–3 часа** чтения ТЗ, извещения и проекта договора.

## 🎯 Основная концепция

Ключевой пользователь: **тендерный специалист / руководитель отдела продаж**, работающий с госзакупками.

Система предоставляет:
- Автоматический анализ тендерной документации
- Выявление рисков и красных флагов
- Рекомендации по участию
- Генерацию документов (протоколы разногласий, жалобы в ФАС)
- Базу знаний по законодательству
- Калькулятор маржинальности

## 📁 Структура проекта

```
tender-shield-pro/
├── backend/          # FastAPI backend
│   ├── main.py       # Основной файл API
│   ├── config.py     # Конфигурация
│   ├── llm_client.py # Клиент для LLM (Ollama)
│   ├── legal_data.py # Правовая база
│   └── requirements.txt
├── frontend/         # React + TypeScript frontend
│   ├── src/
│   │   ├── components/  # React компоненты
│   │   ├── services/    # API сервисы
│   │   ├── utils/       # Утилиты
│   │   └── types.ts     # TypeScript типы
│   └── package.json
└── warp.md           # Детальная документация проекта
```

## 🚀 Быстрый старт

### Backend

1. Перейдите в папку backend:
```bash
cd backend
```

2. Создайте виртуальное окружение (если еще не создано):
```bash
python -m venv venv
```

3. Активируйте виртуальное окружение:
```powershell
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Linux/Mac
source venv/bin/activate
```

4. Установите зависимости:
```bash
pip install -r requirements.txt
```

5. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

6. Запустите сервер:
```bash
python main.py
```

Или через uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend будет доступен по адресу: `http://localhost:8000`
API документация: `http://localhost:8000/docs`

### Frontend

1. Перейдите в папку frontend:
```bash
cd frontend
```

2. Установите зависимости:
```bash
npm install
```

3. Создайте файл `.env` на основе `.env.example`:
```bash
cp .env.example .env
```

4. Запустите dev-сервер:
```bash
npm run dev
```

Frontend будет доступен по адресу: `http://localhost:5173`

## 📚 Основные модули

### Backend

- **API Endpoints:**
  - `POST /api/analyze` - Анализ одного документа
  - `POST /api/analyze-package` - Комплексный анализ пакета документов
  - `GET /api/history` - История анализов
  - `GET /api/legal/search` - Поиск по правовой базе
  - `POST /api/chat` - Чат с AI-помощником

### Frontend

- **Основные экраны:**
  - `Analyzer` - Анализ одного документа
  - `ComplexAudit` - Комплексный аудит пакета
  - `Calculator` - Калькулятор маржинальности
  - `DocumentGenerator` - Генератор документов
  - `KnowledgeView` - База знаний
  - `HistoryView` - История анализов
  - `Profile` - Личный кабинет

## 🛠 Технологии

**Backend:**
- FastAPI
- Python 3.10+
- Ollama (LLM)
- LangChain

**Frontend:**
- React 19
- TypeScript
- Vite
- Tailwind CSS

## 📖 Документация

Подробная документация проекта находится в файле [`warp.md`](warp.md).

### MCP (Cursor инструменты)
- Точка входа и шаблоны: `mcp/README.md`
- Правила безопасности: `mcp/SECURITY.md`

## ⚠️ Важно

- Система **не заменяет юриста** и не даёт «готовых схем» обхода закона
- Все выводы носят аналитический характер
- Окончательное решение принимает специалист
- При загрузке документов пользователь подтверждает законность использования и соглашается на обработку ПДн

## 📝 Лицензия

Proprietary - Все права защищены

## 👥 Разработка

Для разработчиков:
- См. [`warp.md`](warp.md) для архитектуры и правил
- См. `backend/README.md` для деталей backend
- См. `frontend/README.md` для деталей frontend
