# ⚡ БЫСТРАЯ ШПАРГАЛКА: Сохранение и восстановление

## 🚀 БЫСТРОЕ СОХРАНЕНИЕ (5 минут)

### 1. Запустите скрипт бэкапа
```powershell
cd c:\Users\Dom\Desktop\tender-shield-pro
.\backup_script.ps1
```

Скрипт автоматически:
- ✅ Скопирует весь проект (без node_modules, venv и т.д.)
- ✅ Сохранит конфиги отдельно (включая .env)
- ✅ Экспортирует базу данных (если Docker запущен)
- ✅ Сохранит список Ollama моделей

### 2. Проверьте результат
Бэкап будет в:
- `D:\Backup\tender-shield-pro-YYYY-MM-DD/` - весь проект
- `D:\Backup\tender-shield-pro-env-YYYY-MM-DD/` - конфиги и секреты

### 3. Закоммитьте в Git (если используете)
```bash
git add .
git commit -m "Backup before Windows reinstall"
git push
```

---

## 🔄 БЫСТРОЕ ВОССТАНОВЛЕНИЕ (10 минут)

### 1. Установите необходимое ПО
```powershell
# Git
winget install Git.Git

# Docker Desktop
winget install Docker.DockerDesktop

# Node.js
winget install OpenJS.NodeJS.LTS

# Python
winget install Python.Python.3.11

# Ollama
winget install Ollama.Ollama
```

### 2. Восстановите проект
```powershell
# Скопируйте папку проекта обратно
xcopy "D:\Backup\tender-shield-pro-YYYY-MM-DD" "c:\Users\Dom\Desktop\tender-shield-pro" /E /I /H /Y

# Или клонируйте из Git
git clone <URL> c:\Users\Dom\Desktop\tender-shield-pro
```

### 3. Восстановите конфиги
```powershell
# Скопируйте .env обратно
copy "D:\Backup\tender-shield-pro-env-YYYY-MM-DD\backend\.env" "c:\Users\Dom\Desktop\tender-shield-pro\backend\.env"
```

### 4. Установите зависимости
```powershell
# Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ..\frontend
npm install
```

### 5. Запустите Docker
```powershell
cd ..\infra
docker-compose up -d

# Подождите 15 секунд, затем инициализируйте БД
docker-compose exec backend python init_db.py
```

### 6. Загрузите Ollama модель
```powershell
ollama pull qwen2.5-coder:7b
```

### 7. Проверьте работу
- Backend: http://localhost:8000/api/health
- Frontend: http://localhost

---

## 📝 ЧЕКЛИСТ

### Перед переустановкой:
- [ ] Запущен `backup_script.ps1`
- [ ] Проверен бэкап в `D:\Backup\`
- [ ] Закоммичены изменения в Git (если используется)
- [ ] Сохранен `.env` файл отдельно

### После переустановки:
- [ ] Установлен Git, Docker, Node.js, Python, Ollama
- [ ] Проект восстановлен
- [ ] `.env` файл восстановлен
- [ ] Зависимости установлены
- [ ] Docker контейнеры запущены
- [ ] БД инициализирована
- [ ] Ollama модель загружена
- [ ] Все работает

---

**Подробная инструкция:** см. `BACKUP_AND_RESTORE.md`
