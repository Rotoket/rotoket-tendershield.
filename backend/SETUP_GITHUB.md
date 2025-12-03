# 📦 Создание репозитория на GitHub

## ✅ Предварительные шаги выполнены

1. ✅ Все ошибки линтера исправлены
2. ✅ `.gitignore` настроен
3. ✅ Документация подготовлена

## 🚀 Быстрый старт

### Шаг 1: Инициализация Git (если еще не сделано)

Откройте PowerShell в корневой папке проекта `tender-shield-pro` и выполните:

```powershell
# Перейдите в корневую папку проекта
cd "C:\Users\Dom\Desktop\tender-shield-pro"

# Проверьте, есть ли уже git репозиторий
if (Test-Path .git) {
    Write-Host "Git репозиторий уже инициализирован"
} else {
    Write-Host "Инициализация нового репозитория..."
    git init
}

# Проверьте статус
git status
```

### Шаг 2: Настройка Git (если еще не настроено)

```powershell
# Настройте ваше имя и email (если еще не настроено)
git config --global user.name "Ваше Имя"
git config --global user.email "ваш.email@example.com"
```

### Шаг 3: Добавление файлов

```powershell
# Добавьте все файлы в staging area
git add .

# Проверьте, что будет добавлено (убедитесь, что нет .env, venv, node_modules)
git status
```

### Шаг 4: Первый коммит

```powershell
# Создайте первый коммит
git commit -m "Initial commit: Tender Shield Pro - SaaS сервис для анализа тендерной документации

- FastAPI backend с интеграцией LLM (Ollama)
- React frontend с TypeScript
- Система анализа тендерных документов
- База знаний по законодательству
- Калькулятор маржинальности
- История анализов с фильтрацией
- Валидация файлов
- Система аутентификации"
```

### Шаг 5: Создание репозитория на GitHub

1. Перейдите на https://github.com/new
2. Заполните:
   - **Repository name**: `tender-shield-pro`
   - **Description**: `SaaS-сервис для интеллектуального анализа тендерной документации РФ`
   - **Visibility**: Private (или Public)
   - ❌ **НЕ** отмечайте галочки (README, .gitignore уже есть)
3. Нажмите **"Create repository"**

### Шаг 6: Подключение к GitHub

После создания репозитория GitHub покажет инструкции. Выполните:

```powershell
# Добавьте удаленный репозиторий (замените YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/tender-shield-pro.git

# Или если хотите использовать SSH (если настроен):
# git remote add origin git@github.com:YOUR_USERNAME/tender-shield-pro.git

# Переименуйте ветку в main (если нужно)
git branch -M main

# Отправьте код на GitHub
git push -u origin main
```

## ✅ Проверка

1. Обновите страницу репозитория на GitHub
2. Убедитесь, что все файлы загружены
3. Проверьте, что файлы `.env`, `venv/`, `node_modules/` **НЕ** попали в репозиторий

## 📋 Структура репозитория

После успешной загрузки структура должна выглядеть так:

```
tender-shield-pro/
├── .gitignore
├── README.md
├── ERROR_ANALYSIS.md
├── GITHUB_SETUP.md
├── SETUP_GITHUB.md
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   └── ...
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
└── ...
```

## ⚠️ Важно

### Файлы, которые НЕ должны попасть в репозиторий:

- ❌ `backend/.env` (с реальными ключами)
- ❌ `backend/venv/` (виртуальное окружение)
- ❌ `frontend/node_modules/` (зависимости)
- ❌ `backend/temp_*.doc` (временные файлы)
- ❌ `*.log` (логи)

Если какие-то из этих файлов попали в коммит, удалите их:

```powershell
# Удалить файл из git, но оставить локально
git rm --cached backend/.env
git rm --cached -r backend/venv/
git rm --cached -r frontend/node_modules/

# Обновить .gitignore (если нужно)
# Затем создать новый коммит
git add .gitignore
git commit -m "Remove sensitive files and dependencies"
git push
```

## 🔄 Дальнейшая работа

### Добавление изменений:

```powershell
git status                    # Проверить изменения
git add .                     # Добавить все изменения
git commit -m "Описание"      # Создать коммит
git push                      # Отправить на GitHub
```

### Создание новой ветки:

```powershell
git checkout -b feature/new-feature
# Внести изменения
git add .
git commit -m "Add new feature"
git push -u origin feature/new-feature
```

## 📚 Дополнительные ресурсы

- [Официальная документация Git](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

---

**Готово!** Ваш проект теперь на GitHub! 🎉

