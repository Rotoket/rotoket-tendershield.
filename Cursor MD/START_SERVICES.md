# ✅ Система запущена!

## 🚀 Статус запуска

Я запустил оба сервиса в фоновом режиме через терминал:

1. ✅ **Backend** запущен на http://localhost:8000
2. ✅ **Frontend** запущен на http://localhost:5173

## 📋 Проверка работы

### Откройте в браузере:

1. **Главное приложение**: http://localhost:5173
2. **API документация**: http://localhost:8000/docs

### Или проверьте через PowerShell:

```powershell
# Проверка Backend
Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing

# Проверка Frontend  
Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing
```

## 🔧 Если сервисы не запущены

### Запуск Backend (Терминал 1):

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Запуск Frontend (Терминал 2):

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\frontend
npm run dev
```

## 🛑 Остановка сервисов

### Через терминал:

Нажмите `Ctrl + C` в каждом терминале, где запущен сервис.

### Через PowerShell (принудительная остановка):

```powershell
# Остановить все Python процессы (backend)
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Остановить все Node процессы (frontend)
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
```

## 📊 Проверка процессов

### Посмотреть запущенные процессы:

```powershell
# Python процессы (backend)
Get-Process python -ErrorAction SilentlyContinue

# Node процессы (frontend)
Get-Process node -ErrorAction SilentlyContinue

# Проверка портов
netstat -ano | findstr ":8000"
netstat -ano | findstr ":5173"
```

## ✅ Ожидаемый результат

После успешного запуска вы должны увидеть:

- ✅ Интерфейс приложения в браузере на http://localhost:5173
- ✅ API документацию на http://localhost:8000/docs
- ✅ Возможность зарегистрироваться и войти в систему
- ✅ Возможность загрузить документ для анализа

---

**Система готова к работе!** 🎉

Откройте браузер и перейдите на **http://localhost:5173**

