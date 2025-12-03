# 🛡️ Tender Shield Pro

**AI-система для анализа тендерной документации**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2-blue.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8-blue.svg)](https://www.typescriptlang.org/)

---

## 🚀 Быстрый старт

### Предварительные требования

- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL 14+** (опционально, можно использовать SQLite)
- **Ollama** (для AI анализа)

### 1. Клонирование и установка

```bash
# Клонировать репозиторий
git clone <repository-url>
cd tender-shield-pro

# Backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Настройка окружения

Создайте файл `backend/.env`:

```env
# Database
TENDER_DB_USER=postgres
TENDER_DB_PASSWORD=postgres
TENDER_DB_HOST=localhost
TENDER_DB_PORT=5432
TENDER_DB_NAME=tender_shield

# JWT
TENDER_SECRET_KEY=your-secret-key-change-in-production

# Ollama
TENDER_OLLAMA_BASE_URL=http://localhost:11434
TENDER_OLLAMA_MODEL=qwen2.5:0.5b

# Frontend URL
TENDER_CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Запуск

**Backend:**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

**Или используйте скрипты:**
- Windows: `backend\start.ps1` или `backend\start-backend.bat`
- Frontend: `frontend\npm run dev`

---

## 📋 Основные функции

### ✅ Реализовано

1. **Анализ документов**
   - PDF, DOCX, DOC, TXT
   - Пакетный анализ
   - 4 отрасли (IT, Строительство, Медицина, Универсальный)

2. **Аналитика**
   - Статистика пользователя
   - Системная статистика
   - Временная линия
   - Экспорт в CSV/Excel

3. **Экспорт**
   - PDF отчеты
   - Excel отчеты
   - CSV экспорт

4. **Уведомления**
   - Предупреждения о лимитах
   - Уведомления о триале

5. **Безопасность**
   - JWT авторизация
   - Валидация файлов
   - Rate limiting

---

## 🧪 Тестирование

**Backend:**
```bash
cd backend
python -m pytest tests/ -v
```

**Frontend:**
```bash
cd frontend
npm test
```

---

## 📊 Статистика проекта

- **Backend:** 95% готов
- **Frontend:** 90% готов
- **Общий прогресс:** 92% готово к продакшену
- **Тесты:** 75+ тестов проходят

---

## 📚 Документация

- [Полный обзор проекта](ПРОЕКТ_ПОЛНЫЙ_ОБЗОР.md)
- [Итоговый отчет](ИТОГОВЫЙ_ОТЧЕТ_ПРОЕКТА.md)
- [Backend документация](backend/README.md)
- [Frontend документация](frontend/README.md)

---

## 🛠️ Технологии

**Backend:**
- FastAPI
- SQLAlchemy
- PostgreSQL/SQLite
- Ollama (LLM)
- Redis (кеширование)

**Frontend:**
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Recharts

---

## 📝 Лицензия

Proprietary - Все права защищены

---

## 👥 Контакты

Для вопросов и поддержки обращайтесь к команде разработки.
