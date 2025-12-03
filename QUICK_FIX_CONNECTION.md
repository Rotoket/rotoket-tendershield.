# 🔧 Быстрое решение проблемы "Failed to fetch"

## Проблема
При анализе документов появляется ошибка: "Не удалось подключиться к серверу"

## ✅ Решение (3 шага)

### Шаг 1: Запустите Backend сервер

Откройте **новый терминал PowerShell** и выполните:

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Вы должны увидеть:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**⚠️ НЕ ЗАКРЫВАЙТЕ ЭТОТ ТЕРМИНАЛ!** Оставьте его открытым.

### Шаг 2: Проверьте файл .env во frontend

Убедитесь, что файл `frontend\.env` существует и содержит:

```
VITE_API_URL=http://localhost:8000/api
```

Если файла нет, создайте его:
```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\frontend
echo "VITE_API_URL=http://localhost:8000/api" > .env
```

**Важно:** После создания/изменения `.env` файла **перезапустите frontend**!

### Шаг 3: Перезапустите Frontend

Если frontend уже запущен:
1. Остановите его (Ctrl+C в терминале frontend)
2. Запустите заново:

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\frontend
npm run dev
```

## 🔍 Автоматическая диагностика

Запустите скрипт проверки:

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro
.\check-connection.ps1
```

Скрипт проверит:
- ✅ Запущен ли backend на порту 8000
- ✅ Запущен ли frontend на порту 5173
- ✅ Существует ли файл .env
- ✅ Доступен ли API

## 📋 Проверка вручную

### Проверка портов:

```powershell
# Проверка backend (должен показать процесс)
netstat -ano | findstr ":8000"

# Проверка frontend (должен показать процесс)
netstat -ano | findstr ":5173"
```

### Проверка API в браузере:

Откройте в браузере: http://localhost:8000/api/health

Должен вернуться JSON:
```json
{
  "status": "ok",
  "message": "API работает",
  "timestamp": "...",
  "cors_origins": ["http://localhost:5173", ...]
}
```

### Проверка API документации:

Откройте: http://localhost:8000/docs

Должна открыться страница Swagger с документацией API.

## 🚀 Быстрый запуск (оба сервиса)

Используйте готовый скрипт:

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro
.\start.ps1
```

Или запустите вручную в двух терминалах:

**Терминал 1 (Backend):**
```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Терминал 2 (Frontend):**
```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\frontend
npm run dev
```

## ⚠️ Частые проблемы

### Проблема: "Порт 8000 уже занят"
**Решение:** Найдите и остановите процесс:
```powershell
netstat -ano | findstr ":8000"
# Запомните PID (последний столбец)
taskkill /PID <PID> /F
```

### Проблема: "Модуль не найден" при запуске backend
**Решение:** Установите зависимости:
```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Проблема: CORS ошибка
**Решение:** Убедитесь, что в `backend/config.py` указан правильный порт frontend:
```python
CORS_ORIGINS: List[str] = [
    "http://localhost:5173",  # ← должен совпадать с портом frontend
    "http://127.0.0.1:5173",
]
```

## ✅ После исправления

1. Backend должен быть запущен и доступен на http://localhost:8000
2. Frontend должен быть запущен и доступен на http://localhost:5173
3. Файл `frontend\.env` должен содержать `VITE_API_URL=http://localhost:8000/api`
4. Попробуйте снова загрузить документ для анализа

---

**Если проблема сохраняется:**
1. Откройте консоль браузера (F12 → Console)
2. Посмотрите детальные ошибки
3. Проверьте Network tab в DevTools для просмотра запросов

