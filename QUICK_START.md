# ⚡ Быстрый старт Tender Shield Pro

## 🎯 За 5 минут до запуска

### Шаг 1: Установка зависимостей

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### Шаг 2: Настройка (минимальная)

Создайте `backend/.env`:
```env
TENDER_SECRET_KEY=dev-secret-key-12345
TENDER_OLLAMA_BASE_URL=http://localhost:11434
TENDER_OLLAMA_MODEL=qwen2.5:0.5b
```

### Шаг 3: Запуск Ollama (если нужно)

```bash
# Установите Ollama с https://ollama.ai
# Затем загрузите модель:
ollama pull qwen2.5:0.5b
```

### Шаг 4: Запуск приложения

**Терминал 1 (Backend):**
```bash
cd backend
uvicorn main:app --reload
```

**Терминал 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### Шаг 5: Откройте браузер

Перейдите на: http://localhost:5173

---

## ✅ Готово!

Система запущена и готова к использованию.

**Примечание:** При первом запуске система автоматически:
- Создаст таблицы БД (SQLite по умолчанию)
- Создаст тарифы
- Создаст индексы

---

## 🔧 Решение проблем

**Ошибка подключения к БД:**
- Система автоматически использует SQLite, если PostgreSQL недоступен

**Ошибка Ollama:**
- Убедитесь, что Ollama запущен: `ollama serve`
- Проверьте модель: `ollama list`

**Ошибка портов:**
- Backend: измените порт в `uvicorn --port 8001`
- Frontend: измените в `vite.config.ts`

---

## 📞 Нужна помощь?

См. полную документацию в `README.md` и `ПРОЕКТ_ПОЛНЫЙ_ОБЗОР.md`

