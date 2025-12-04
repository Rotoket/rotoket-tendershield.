# 🚀 Инструкция по созданию репозитория на GitHub

## Шаг 1: Создание репозитория на GitHub

1. Перейдите на [GitHub.com](https://github.com) и войдите в свой аккаунт
2. Нажмите кнопку **"New repository"** (или перейдите по ссылке: https://github.com/new)
3. Заполните форму:
   - **Repository name**: `tender-shield-pro`
   - **Description**: `SaaS-сервис для интеллектуального анализа тендерной документации РФ`
   - **Visibility**: Выберите **Private** (или Public, если хотите открытый репозиторий)
   - **НЕ** отмечайте галочки:
     - ❌ Add a README file (у нас уже есть)
     - ❌ Add .gitignore (у нас уже есть)
     - ❌ Choose a license (можно добавить позже)
4. Нажмите кнопку **"Create repository"**

## Шаг 2: Инициализация локального репозитория

Выполните следующие команды в PowerShell в корневой папке проекта:

```powershell
# Перейдите в корневую папку проекта
cd C:\Users\Dom\Desktop\tender-shield-pro

# Инициализируйте git репозиторий
git init

# Добавьте все файлы
git add .

# Создайте первый коммит
git commit -m "Initial commit: Tender Shield Pro - SaaS сервис для анализа тендерной документации"

# Добавьте удаленный репозиторий (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/tender-shield-pro.git

# Переименуйте ветку в main (если нужно)
git branch -M main

# Отправьте код на GitHub
git push -u origin main
```

## Шаг 3: Настройка .gitignore

Убедитесь, что файл `.gitignore` в корне проекта содержит все необходимые исключения. Он уже настроен, но проверьте, что не забыты:
- `venv/` и `node_modules/`
- `.env` файлы
- Временные файлы
- Скомпилированные файлы

## Шаг 4: Проверка

После выполнения команд:

1. Обновите страницу репозитория на GitHub
2. Убедитесь, что все файлы загружены
3. Проверьте, что файлы `.env`, `venv/`, `node_modules/` отсутствуют (они должны быть в .gitignore)

## ⚠️ Важные замечания

### Безопасность:

- ❌ **НИКОГДА** не коммитьте файлы `.env` с реальными ключами API
- ❌ **НИКОГДА** не коммитьте пароли или токены
- ✅ Используйте `.env.example` для шаблонов конфигурации

### Что НЕ должно попасть в репозиторий:

- Файлы `.env` с реальными ключами
- Папка `venv/` (виртуальное окружение Python)
- Папка `node_modules/` (зависимости Node.js)
- Временные файлы (`temp_*`, `*.tmp`)
- Бинарные файлы документов (если они большие)
- База данных (`*.db`, `*.sqlite`)

## 🔄 Последующие коммиты

После первого коммита, для добавления изменений используйте:

```powershell
# Проверить статус
git status

# Добавить изменения
git add .

# Создать коммит
git commit -m "Описание изменений"

# Отправить на GitHub
git push
```

## 📝 Создание тегов версий

Для создания релизов используйте теги:

```powershell
# Создать тег
git tag -a v1.0.0 -m "Версия 1.0.0 - Первый релиз"

# Отправить тег на GitHub
git push origin v1.0.0
```

## 🛠 Дополнительные команды

### Просмотр истории коммитов:
```powershell
git log --oneline --graph
```

### Отмена последнего коммита (если еще не отправлен):
```powershell
git reset --soft HEAD~1
```

### Клонирование репозитория на другом компьютере:
```powershell
git clone https://github.com/YOUR_USERNAME/tender-shield-pro.git
cd tender-shield-pro
```

## 📚 Полезные ссылки

- [Документация Git](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Git Cheat Sheet](https://education.github.com/git-cheat-sheet-education.pdf)

---

**Готово!** Ваш проект теперь на GitHub! 🎉

