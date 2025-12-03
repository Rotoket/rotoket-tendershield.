# 🚀 Статус запуска системы

## ✅ Попытка запуска выполнена

Я запустил оба сервиса в фоновом режиме:

1. **Backend** - запущен через uvicorn на порту 8000
2. **Frontend** - запущен через npm run dev на порту 5173

## 📋 Проверка статуса

### Проверьте в браузере:

1. **Frontend**: http://localhost:5173
2. **Backend API Docs**: http://localhost:8000/docs

### Проверьте в терминале:

#### Проверка Backend:
```powershell
curl http://localhost:8000/docs
# или просто откройте в браузере: http://localhost:8000/docs
```

#### Проверка Frontend:
```powershell
curl http://localhost:5173
# или просто откройте в браузере: http://localhost:5173
```

## 🔍 Если сервисы не запустились

### Для ручного запуска Backend:

Откройте **новый терминал PowerShell** и выполните:

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Для ручного запуска Frontend:

Откройте **еще один терминал PowerShell** и выполните:

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\frontend
npm run dev
```

## ⚠️ Важные замечания

1. **Backend и Frontend должны работать одновременно** - запустите их в разных терминалах
2. **Backend должен быть запущен первым** - frontend обращается к API
3. **Остановка**: Нажмите `Ctrl + C` в каждом терминале для остановки

## 📊 Проверка процессов

### Посмотреть запущенные процессы:

```powershell
# Python процессы
Get-Process python

# Node процессы
Get-Process node

# Uvicorn процессы
Get-Process python | Where-Object {$_.CommandLine -like "*uvicorn*"}
```

### Завершить процессы (если нужно):

```powershell
# Завершить все Python процессы
Stop-Process -Name python -Force

# Завершить все Node процессы
Stop-Process -Name node -Force
```

## ✅ Ожидаемый результат

После успешного запуска:

- ✅ Backend доступен на: http://localhost:8000
- ✅ Frontend доступен на: http://localhost:5173
- ✅ API документация доступна на: http://localhost:8000/docs

Откройте браузер и перейдите на **http://localhost:5173** чтобы увидеть интерфейс приложения!

---

**Статус:** Сервисы запущены в фоновом режиме. Проверьте доступность через браузер.

