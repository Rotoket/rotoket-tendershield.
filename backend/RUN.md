# 🚀 Запуск проекта через терминал

## Быстрый старт

### 📋 Предварительные требования

1. **Python 3.10+** (для backend)
2. **Node.js 18+** и **npm** (для frontend)
3. **PostgreSQL** (опционально, для базы данных)
4. **Ollama** (для работы LLM)

---

## 🔧 Запуск Backend

### Шаг 1: Откройте терминал PowerShell

Нажмите `Win + X` и выберите **"Windows PowerShell"** или **"Терминал"**

### Шаг 2: Перейдите в папку backend

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\backend
```

### Шаг 3: Активируйте виртуальное окружение

```powershell
# Если виртуальное окружение еще не создано:
python -m venv venv

# Активируйте его:
.\venv\Scripts\Activate.ps1
```

Если появится ошибка о политике выполнения скриптов, выполните:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Шаг 4: Установите зависимости (если еще не установлены)

```powershell
pip install -r requirements.txt
```

### Шаг 5: Создайте файл .env (если еще не создан)

Создайте файл `.env` в папке `backend` с содержимым:

```env
# База данных (если используете PostgreSQL)
TENDER_DB_USER=postgres
TENDER_DB_PASSWORD=postgres
TENDER_DB_HOST=localhost
TENDER_DB_PORT=5432
TENDER_DB_NAME=tender_shield

# Секретный ключ для JWT
TENDER_SECRET_KEY=your-super-secret-key-change-this-min-32-characters-long

# Ollama (если используете локально)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# CORS (для фронтенда)
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### Шаг 6: Запустите сервер

**Вариант 1: Через uvicorn (рекомендуется)**
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Вариант 2: Через Python**
```powershell
python main.py
```

Backend будет доступен по адресу: **http://localhost:8000**  
API документация: **http://localhost:8000/docs**

---

## 🎨 Запуск Frontend

### Шаг 1: Откройте НОВЫЙ терминал PowerShell

(Оставьте backend запущенным в первом терминале)

### Шаг 2: Перейдите в папку frontend

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\frontend
```

### Шаг 3: Установите зависимости (если еще не установлены)

```powershell
npm install
```

### Шаг 4: Создайте файл .env (если еще не создан)

Создайте файл `.env` в папке `frontend` с содержимым:

```env
VITE_API_URL=http://localhost:8000
```

### Шаг 5: Запустите dev-сервер

```powershell
npm run dev
```

Frontend будет доступен по адресу: **http://localhost:5173**

---

## ✅ Проверка работы

1. **Backend работает**, если:
   - В терминале видно: `Uvicorn running on http://0.0.0.0:8000`
   - Открывается страница: http://localhost:8000/docs

2. **Frontend работает**, если:
   - В терминале видно: `Local: http://localhost:5173/`
   - Открывается интерфейс приложения

---

## 🔄 Одновременный запуск (оба сервера)

### Вариант 1: Два терминала

1. **Терминал 1** - Backend:
   ```powershell
   cd C:\Users\Dom\Desktop\tender-shield-pro\backend
   .\venv\Scripts\Activate.ps1
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Терминал 2** - Frontend:
   ```powershell
   cd C:\Users\Dom\Desktop\tender-shield-pro\frontend
   npm run dev
   ```

### Вариант 2: Один терминал с фоновыми процессами

```powershell
# Запуск backend в фоне
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\Dom\Desktop\tender-shield-pro\backend; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8000"

# Запуск frontend
cd C:\Users\Dom\Desktop\tender-shield-pro\frontend
npm run dev
```

---

## 🛑 Остановка серверов

### Остановка Backend:
- Нажмите `Ctrl + C` в терминале с backend

### Остановка Frontend:
- Нажмите `Ctrl + C` в терминале с frontend

---

## ⚠️ Возможные проблемы

### Проблема 1: Порт 8000 уже занят

**Решение:**
```powershell
# Найдите процесс, использующий порт 8000
netstat -ano | findstr :8000

# Завершите процесс (замените PID на номер процесса)
taskkill /PID <PID> /F

# Или запустите на другом порте:
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Проблема 2: Порт 5173 уже занят

**Решение:**
```powershell
# Frontend автоматически предложит использовать другой порт
# Или укажите порт явно:
npm run dev -- --port 5174
```

### Проблема 3: Модули не найдены (Python)

**Решение:**
```powershell
# Убедитесь, что виртуальное окружение активировано
# В начале строки должно быть (venv)
.\venv\Scripts\Activate.ps1

# Переустановите зависимости
pip install -r requirements.txt
```

### Проблема 4: Модули не найдены (Node.js)

**Решение:**
```powershell
# Удалите node_modules и package-lock.json
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json

# Переустановите зависимости
npm install
```

### Проблема 5: Ошибка подключения к Ollama

**Решение:**
1. Убедитесь, что Ollama запущен:
   ```powershell
   # Проверьте, что Ollama работает
   ollama list
   ```

2. Или используйте другой LLM (если настроен)

---

## 📝 Полезные команды

### Backend

```powershell
# Просмотр логов в реальном времени
uvicorn main:app --reload --log-level debug

# Запуск без автоматической перезагрузки
uvicorn main:app --host 0.0.0.0 --port 8000

# Проверка синтаксиса Python
python -m py_compile main.py
```

### Frontend

```powershell
# Сборка для production
npm run build

# Просмотр собранного проекта
npm run preview

# Проверка кода
npm run lint

# Запуск тестов
npm test
```

---

## 🎯 Быстрые команды (скопируйте и вставьте)

### Запуск Backend:
```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\backend; .\venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Запуск Frontend:
```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\frontend; npm run dev
```

---

## 📚 Дополнительная информация

- **Backend API документация**: http://localhost:8000/docs
- **Backend альтернативная документация**: http://localhost:8000/redoc
- **Frontend**: http://localhost:5173

---

**Готово!** Проект запущен и готов к работе! 🎉

