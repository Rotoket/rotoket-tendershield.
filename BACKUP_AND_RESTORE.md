# 💾 Инструкция по сохранению и восстановлению проекта

## 📦 ЧТО СОХРАНИТЬ ПЕРЕД ПЕРЕУСТАНОВКОЙ WINDOWS

### 1. Код проекта (ОБЯЗАТЕЛЬНО)

#### Вариант A: Через Git (РЕКОМЕНДУЕТСЯ)
```bash
# Проверьте, что все изменения закоммичены
cd c:\Users\Dom\Desktop\tender-shield-pro
git status

# Если есть незакоммиченные изменения, закоммитьте их
git add .
git commit -m "Backup before Windows reinstall"

# Отправьте в удаленный репозиторий (GitHub, GitLab и т.д.)
git push origin main
```

#### Вариант B: Резервная копия на внешний диск/облако
```bash
# Скопируйте всю папку проекта
xcopy "c:\Users\Dom\Desktop\tender-shield-pro" "D:\Backup\tender-shield-pro" /E /I /H /Y
```

**Что копировать:**
- ✅ Вся папка `tender-shield-pro` (код, конфиги, документация)
- ✅ Папка `.git` (если используете Git)
- ❌ НЕ копируйте: `node_modules`, `venv`, `__pycache__`, `.pytest_cache`

---

### 2. Конфигурационные файлы (ОБЯЗАТЕЛЬНО)

Скопируйте эти файлы отдельно (они могут содержать секреты):

```bash
# Backend конфигурация
backend\.env
backend\env.example

# Docker конфигурация
infra\docker-compose.yml
infra\nginx.conf

# Другие важные конфиги
.cursorrules
.gitignore
```

**⚠️ ВАЖНО:** Файл `backend\.env` содержит секретные ключи! Сохраните его в безопасном месте.

---

### 3. База данных (если есть важные данные)

#### PostgreSQL данные
```bash
# Экспорт базы данных
docker-compose exec db pg_dump -U tender_user tender > backup_db.sql

# Или если БД не в Docker
pg_dump -U tender_user -d tender_shield > backup_db.sql
```

#### ChromaDB данные
```bash
# Скопируйте volume ChromaDB
# Найти путь к volume:
docker volume inspect infra_chroma_data

# Скопировать данные
# (путь будет примерно: C:\ProgramData\docker\volumes\infra_chroma_data\_data)
```

---

### 4. Ollama модели (если нужно)

```bash
# Список установленных моделей
ollama list

# Экспорт моделей (если нужно)
# Ollama хранит модели в: C:\Users\Dom\.ollama
# Скопируйте эту папку, если хотите сохранить модели
```

**Примечание:** Модели можно скачать заново после установки, но это займет время.

---

### 5. Другие важные данные

- Документация проекта (файлы `.md`)
- Тестовые документы тендеров (папка `tender/`)
- Логи и отчеты (если важны)

---

## 🔄 ВОССТАНОВЛЕНИЕ ПОСЛЕ ПЕРЕУСТАНОВКИ WINDOWS

### Шаг 1: Установка необходимого ПО

#### 1.1. Установите Git
```bash
# Скачайте с: https://git-scm.com/download/win
# Или через winget:
winget install Git.Git
```

#### 1.2. Установите Docker Desktop
```bash
# Скачайте с: https://www.docker.com/products/docker-desktop
# Или через winget:
winget install Docker.DockerDesktop
```

#### 1.3. Установите Node.js (для разработки)
```bash
# Скачайте LTS версию с: https://nodejs.org/
# Или через winget:
winget install OpenJS.NodeJS.LTS
```

#### 1.4. Установите Python (для разработки)
```bash
# Скачайте с: https://www.python.org/downloads/
# Или через winget:
winget install Python.Python.3.11
```

#### 1.5. Установите Ollama
```bash
# Скачайте с: https://ollama.ai/download
# Или через winget:
winget install Ollama.Ollama
```

---

### Шаг 2: Восстановление проекта

#### 2.1. Клонирование/копирование проекта

**Если использовали Git:**
```bash
# Клонируйте репозиторий
git clone <URL_вашего_репозитория> c:\Users\Dom\Desktop\tender-shield-pro
cd c:\Users\Dom\Desktop\tender-shield-pro
```

**Если делали резервную копию:**
```bash
# Скопируйте папку проекта обратно
xcopy "D:\Backup\tender-shield-pro" "c:\Users\Dom\Desktop\tender-shield-pro" /E /I /H /Y
```

#### 2.2. Восстановление конфигурационных файлов

```bash
# Скопируйте сохраненные конфиги обратно
copy "D:\Backup\backend\.env" "c:\Users\Dom\Desktop\tender-shield-pro\backend\.env"
copy "D:\Backup\infra\docker-compose.yml" "c:\Users\Dom\Desktop\tender-shield-pro\infra\docker-compose.yml"
# и т.д.
```

**⚠️ ВАЖНО:** Проверьте, что файл `backend\.env` восстановлен и содержит все необходимые переменные.

---

### Шаг 3: Восстановление зависимостей

#### 3.1. Backend зависимости
```bash
cd c:\Users\Dom\Desktop\tender-shield-pro\backend

# Создайте виртуальное окружение
python -m venv venv
venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

#### 3.2. Frontend зависимости
```bash
cd c:\Users\Dom\Desktop\tender-shield-pro\frontend

# Установите зависимости
npm install
```

---

### Шаг 4: Восстановление базы данных

#### 4.1. Запустите Docker контейнеры
```bash
cd c:\Users\Dom\Desktop\tender-shield-pro\infra
docker-compose up -d
```

#### 4.2. Дождитесь запуска PostgreSQL (10-15 секунд)

#### 4.3. Восстановите базу данных
```bash
# Если сохранили дамп БД
docker-compose exec -T db psql -U tender_user tender < backup_db.sql

# Или инициализируйте заново (если данных не было)
docker-compose exec backend python init_db.py
```

---

### Шаг 5: Восстановление Ollama моделей

```bash
# Загрузите модель заново
ollama pull qwen2.5-coder:7b

# Или если сохранили папку .ollama, скопируйте её обратно
# (обычно в: C:\Users\Dom\.ollama)
```

---

### Шаг 6: Проверка работы

```bash
# Проверьте Backend
curl http://localhost:8000/api/health

# Проверьте Frontend
# Откройте: http://localhost

# Проверьте ChromaDB
curl http://localhost:8001/api/v1/heartbeat
```

---

## 📋 ЧЕКЛИСТ ПЕРЕД ПЕРЕУСТАНОВКОЙ

- [ ] Закоммитить все изменения в Git и отправить в удаленный репозиторий
- [ ] Сохранить файл `backend\.env` в безопасное место
- [ ] Сохранить конфигурационные файлы (`docker-compose.yml`, `nginx.conf`)
- [ ] Экспортировать базу данных (если есть важные данные)
- [ ] Сохранить тестовые документы тендеров (если нужны)
- [ ] Записать список установленных Ollama моделей
- [ ] Создать резервную копию всей папки проекта на внешний диск/облако

---

## 📋 ЧЕКЛИСТ ПОСЛЕ ПЕРЕУСТАНОВКИ

- [ ] Установлен Git
- [ ] Установлен Docker Desktop
- [ ] Установлен Node.js
- [ ] Установлен Python
- [ ] Установлен Ollama
- [ ] Проект склонирован/скопирован
- [ ] Восстановлен файл `backend\.env`
- [ ] Восстановлены конфигурационные файлы
- [ ] Установлены зависимости backend (`pip install -r requirements.txt`)
- [ ] Установлены зависимости frontend (`npm install`)
- [ ] Запущены Docker контейнеры (`docker-compose up -d`)
- [ ] Инициализирована база данных (`python init_db.py`)
- [ ] Загружена модель Ollama (`ollama pull qwen2.5-coder:7b`)
- [ ] Проверена работа всех сервисов

---

## 🚨 ЧАСТЫЕ ПРОБЛЕМЫ ПРИ ВОССТАНОВЛЕНИИ

### Проблема: Docker не запускается
**Решение:**
- Убедитесь, что WSL2 установлен и обновлен
- Перезапустите Docker Desktop
- Проверьте, что виртуализация включена в BIOS

### Проблема: Ollama не подключается из Docker
**Решение:**
- Убедитесь, что Ollama запущен на хосте
- Проверьте, что порт 11434 доступен
- В `docker-compose.yml` используйте `host.docker.internal:11434`

### Проблема: База данных не восстанавливается
**Решение:**
- Убедитесь, что PostgreSQL контейнер запущен
- Проверьте права доступа к файлу дампа
- Попробуйте инициализировать БД заново через `init_db.py`

### Проблема: Зависимости не устанавливаются
**Решение:**
- Обновите pip: `python -m pip install --upgrade pip`
- Обновите npm: `npm install -g npm@latest`
- Очистите кэш: `npm cache clean --force`

---

## 💡 СОВЕТЫ

1. **Используйте Git** - это самый надежный способ сохранить код
2. **Сохраняйте .env отдельно** - этот файл содержит секреты и не должен быть в Git
3. **Делайте резервные копии БД регулярно** - особенно перед переустановкой
4. **Документируйте изменения** - записывайте, что меняли в конфигах
5. **Тестируйте после восстановления** - убедитесь, что все работает

---

## 📞 ЕСЛИ ЧТО-ТО ПОШЛО НЕ ТАК

1. Проверьте логи Docker: `docker-compose logs`
2. Проверьте логи Backend: `docker-compose logs backend`
3. Проверьте подключение к БД: `docker-compose exec db psql -U tender_user -d tender`
4. Проверьте Ollama: `ollama list`
5. Следуйте инструкциям в `DOCKER_SETUP.md`

---

**Удачи с переустановкой! 🚀**

