# 🚀 Быстрый запуск проекта

## Команды для копирования

### 1️⃣ Запуск Backend (Терминал 1)

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\backend
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Результат:** Backend запустится на http://localhost:8000

---

### 2️⃣ Запуск Frontend (Терминал 2)

Откройте **новый терминал** и выполните:

```powershell
cd C:\Users\Dom\Desktop\tender-shield-pro\frontend
npm run dev
```

**Результат:** Frontend запустится на http://localhost:5173

---

## ✅ Проверка

1. Откройте браузер и перейдите на: **http://localhost:5173**
2. Backend API документация: **http://localhost:8000/docs**

---

## 🛑 Остановка

Нажмите `Ctrl + C` в каждом терминале для остановки серверов.

---

## 📖 Подробная инструкция

См. файл [`RUN.md`](RUN.md) для детальной информации.

