# 🚀 Roadmap для выхода на рынок: tender-shield-pro

**Дата:** 2025-11-29  
**Цель:** Превратить MVP в коммерчески готовый SaaS продукт

---

## 📊 Анализ текущего состояния

### ✅ Что уже есть (сильные стороны):
1. **Функциональное ядро:**
   - Анализ тендерных документов (PDF/DOCX/TXT)
   - Поддержка 3 отраслей (IT, Медицина, Строительство)
   - Пакетный анализ документов
   - Генерация черновиков (протокол разногласий, жалобы в ФАС)
   - Калькулятор маржинальности
   - База знаний (правовые сниппеты)
   - История анализов

2. **UX/UI:**
   - Современный темный интерфейс
   - Интуитивная навигация
   - Хаб-дашборд для быстрого обзора

3. **Техническая база:**
   - TypeScript + React + FastAPI
   - LLM интеграция (Ollama)
   - Тесты для утилитарных функций

### ❌ Критичные пробелы для коммерции:
1. **Нет системы пользователей** - только эмуляция авторизации
2. **Нет базы данных** - все данные в памяти
3. **Нет платежной системы** - нет монетизации
4. **Нет тарифных планов** - нет бизнес-модели
5. **Нет безопасности** - нет rate limiting, валидации, защиты
6. **Нет масштабируемости** - все синхронно, нет очередей

---

## 🎯 Приоритетные направления развития

## 🔥 **ПРИОРИТЕТ 1: Монетизация (4-6 недель)**

### 1.1. Система пользователей и авторизации

**Что нужно:**
- [ ] Реальная регистрация через email + подтверждение
- [ ] JWT токены для авторизации
- [ ] Восстановление пароля
- [ ] Роли пользователей (админ, пользователь)

**Технологии:**
```python
# Backend
- FastAPI-Users (готовое решение для авторизации)
- PostgreSQL + SQLAlchemy для хранения пользователей
- JWT токены (access + refresh)
- OAuth2 password flow

# Frontend
- React Context для управления сессией
- Хранение токенов в localStorage (или httpOnly cookies)
- Protected routes
```

**Оценка:** 2-3 недели

### 1.2. База данных

**Что нужно:**
- [ ] PostgreSQL база данных
- [ ] Миграции (Alembic)
- [ ] Модели:
  - `User` (id, email, hashed_password, company, tariff_id, created_at)
  - `Tariff` (id, name, price, limits)
  - `Analysis` (id, user_id, filename, result_json, created_at, industry)
  - `PackageAnalysis` (id, user_id, documents, created_at)
  - `Usage` (user_id, date, analyses_count, tokens_used)

**Структура:**
```python
# backend/database.py
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    company = Column(String)
    tariff_id = Column(Integer, ForeignKey("tariffs.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    analyses = relationship("Analysis", back_populates="user")

class Tariff(Base):
    __tablename__ = "tariffs"
    id = Column(Integer, primary_key=True)
    name = Column(String)  # "Start", "Pro", "Enterprise"
    price = Column(Integer)  # в рублях/месяц
    analyses_limit = Column(Integer)  # лимит анализов в месяц
    package_limit = Column(Integer)  # лимит документов в пакете
    features = Column(JSON)  # список доступных функций

class Analysis(Base):
    __tablename__ = "analyses"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String)
    industry = Column(String)
    result_json = Column(JSON)  # весь результат анализа
    score = Column(Integer)
    verdict = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="analyses")
```

**Оценка:** 1-2 недели

### 1.3. Платежная система

**Что нужно:**
- [ ] Интеграция с платежным провайдером (ЮKassa или CloudPayments)
- [ ] Подписки (recurring payments)
- [ ] Управление тарифами
- [ ] История платежей
- [ ] Webhook для обработки платежей

**Тарифные планы:**
```
START (2,990 ₽/мес):
- 50 анализов в месяц
- 1 пакет (до 5 документов)
- Базовая поддержка
- История 30 дней

PRO (9,990 ₽/мес):
- 200 анализов в месяц
- 10 пакетов (до 10 документов)
- Приоритетная поддержка
- История 90 дней
- Экспорт отчетов

ENTERPRISE (по договору):
- Безлимит анализов
- Приоритетная поддержка 24/7
- История без ограничений
- API доступ
- Кастомные интеграции
- SLA гарантии
```

**Интеграция ЮKassa:**
```python
# backend/payment.py
from yookassa import Configuration, Payment
import uuid

Configuration.account_id = "YOUR_SHOP_ID"
Configuration.secret_key = "YOUR_SECRET_KEY"

async def create_subscription_payment(user_id: int, tariff_id: int):
    payment = Payment.create({
        "amount": {
            "value": "2990.00",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://tender-shield.ai/subscription/success"
        },
        "capture": True,
        "description": f"Подписка PRO на месяц",
        "metadata": {
            "user_id": user_id,
            "tariff_id": tariff_id
        }
    }, uuid.uuid4())
    return payment
```

**Оценка:** 2-3 недели

---

## ⚡ **ПРИОРИТЕТ 2: Оптимизация Backend (3-4 недели)**

### 2.1. Асинхронность и очереди

**Проблема:** Сейчас все запросы синхронные, LLM запросы блокируют поток.

**Решение:**
```python
# Добавить Celery + Redis для фоновых задач
# backend/tasks.py
from celery import Celery

celery_app = Celery(
    'tender_shield',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task
def analyze_document_async(file_path: str, user_id: int, industry: str):
    """Асинхронный анализ документа"""
    result = analyze_single_file(file_path, filename, industry)
    # Сохранить в БД
    # Отправить уведомление пользователю
    return result.id

# API эндпоинт становится неблокирующим
@app.post("/api/analyze")
async def analyze_document(file: UploadFile, user_id: int):
    task = analyze_document_async.delay(file_path, user_id)
    return {"task_id": task.id, "status": "processing"}
```

**Оценка:** 1-2 недели

### 2.2. Кеширование результатов

**Что нужно:**
- [ ] Кеширование похожих документов (по хешу содержимого)
- [ ] Redis для кеша
- [ ] Кеширование правовых сниппетов

```python
import hashlib
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=1)

def get_document_hash(file_content: bytes) -> str:
    return hashlib.sha256(file_content).hexdigest()

async def get_cached_analysis(file_hash: str):
    cached = redis_client.get(f"analysis:{file_hash}")
    if cached:
        return json.loads(cached)
    return None

async def cache_analysis(file_hash: str, result: dict, ttl: int = 86400):
    redis_client.setex(
        f"analysis:{file_hash}",
        ttl,
        json.dumps(result)
    )
```

**Оценка:** 1 неделя

### 2.3. Rate Limiting и квотирование

**Что нужно:**
- [ ] Ограничение запросов по тарифу
- [ ] Rate limiting на уровне API
- [ ] Проверка лимитов перед анализом

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/api/analyze")
@limiter.limit("10/minute")  # 10 запросов в минуту
async def analyze_document(request: Request, file: UploadFile):
    # Проверить лимит тарифа
    user = await get_current_user()
    usage = await get_user_usage(user.id, current_month=True)
    
    if usage.analyses_count >= user.tariff.analyses_limit:
        raise HTTPException(
            status_code=429,
            detail="Достигнут лимит анализов по тарифу. Обновите подписку."
        )
    
    # Продолжить анализ...
```

**Оценка:** 1 неделя

### 2.4. Оптимизация LLM запросов

**Что нужно:**
- [ ] Кеширование промптов
- [ ] Сжатие промптов (убрать избыточность)
- [ ] Streaming ответов для больших документов
- [ ] Batch обработка для пакетов

**Оценка:** 1 неделя

---

## 🔒 **ПРИОРИТЕТ 3: Безопасность и соответствие (2-3 недели)**

### 3.1. Защита данных (152-ФЗ)

**Что нужно:**
- [ ] Шифрование данных в БД (поля с ПДн)
- [ ] Шифрование файлов на диске
- [ ] Автоматическое удаление файлов после анализа (или по расписанию)
- [ ] Аудит доступа (кто когда смотрел данные)

```python
from cryptography.fernet import Fernet

class EncryptionService:
    def __init__(self):
        self.key = settings.ENCRYPTION_KEY
        self.cipher = Fernet(self.key)
    
    def encrypt_file(self, file_path: str) -> bytes:
        with open(file_path, 'rb') as f:
            return self.cipher.encrypt(f.read())
    
    def decrypt_file(self, encrypted_data: bytes, output_path: str):
        decrypted = self.cipher.decrypt(encrypted_data)
        with open(output_path, 'wb') as f:
            f.write(decrypted)

# Автоматическая очистка файлов через 7 дней
@celery_app.task
def cleanup_old_files():
    """Удаляет файлы старше 7 дней"""
    pass
```

**Оценка:** 1-2 недели

### 3.2. Валидация и санитизация

**Что нужно:**
- [ ] Валидация размера файлов (макс 50 МБ)
- [ ] Проверка типов файлов (только PDF, DOCX, DOC, TXT)
- [ ] Защита от вредоносных файлов
- [ ] Валидация входных данных

```python
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ

def validate_file(file: UploadFile):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Неподдерживаемый формат: {ext}")
    
    file_size = 0
    for chunk in file.file:
        file_size += len(chunk)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(413, "Файл слишком большой")
```

**Оценка:** 3-5 дней

---

## 📈 **ПРИОРИТЕТ 4: Аналитика и метрики (1-2 недели)**

### 4.1. Дашборд аналитики

**Что нужно:**
- [ ] Метрики использования (анализов/день, популярные отрасли)
- [ ] Конверсия (пробные → платные)
- [ ] Популярные функции
- [ ] Технические метрики (время ответа, ошибки)

**Инструменты:**
- Google Analytics / Яндекс.Метрика
- Sentry для отслеживания ошибок
- Prometheus + Grafana для технических метрик

**Оценка:** 1 неделя

### 4.2. Email уведомления

**Что нужно:**
- [ ] Приветственное письмо после регистрации
- [ ] Напоминание о лимитах
- [ ] Уведомление о завершении анализа
- [ ] Еженедельный дайджест активности

**Технологии:**
- SendGrid / Mailgun / SMTP
- Шаблоны писем

**Оценка:** 3-5 дней

---

## 🎨 **ПРИОРИТЕТ 5: UX улучшения (2-3 недели)**

### 5.1. Экспорт и отчеты

**Что нужно:**
- [ ] Экспорт анализа в PDF
- [ ] Экспорт в Excel
- [ ] История с фильтрацией и поиском
- [ ] Сохранение избранных анализов

**Оценка:** 1-2 недели

### 5.2. Мобильная адаптация / PWA

**Что нужно:**
- [ ] Адаптивная верстка для планшетов/мобильных
- [ ] PWA (Progressive Web App) для оффлайн работы
- [ ] Push уведомления

**Оценка:** 1-2 недели

---

## 🛠️ **ПРИОРИТЕТ 6: Документация и поддержка (1-2 недели)**

### 6.1. Документация API

**Что нужно:**
- [ ] OpenAPI/Swagger документация (FastAPI уже генерирует)
- [ ] Примеры запросов
- [ ] Интеграционные гайды

**Оценка:** 3-5 дней

### 6.2. Онбординг и помощь

**Что нужно:**
- [ ] Интерактивный тур по интерфейсу
- [ ] Видео-инструкции
- [ ] FAQ
- [ ] Чат поддержки (или интеграция с чат-ботом)

**Оценка:** 1 неделя

---

## 📊 **Итоговый план по приоритетам**

### Фаза 1: MVP для бета-теста (6-8 недель)
- ✅ Система пользователей + БД
- ✅ Базовые тарифы
- ✅ Интеграция платежей
- ✅ Rate limiting
- ✅ Базовая безопасность

### Фаза 2: Оптимизация (3-4 недели)
- ✅ Асинхронная обработка
- ✅ Кеширование
- ✅ Оптимизация LLM
- ✅ Аналитика

### Фаза 3: Полировка (2-3 недели)
- ✅ Экспорт данных
- ✅ Email уведомления
- ✅ Документация
- ✅ Мобильная версия

### Фаза 4: Запуск (1-2 недели)
- ✅ Бета-тестирование
- ✅ Исправление багов
- ✅ Маркетинговая подготовка

**Общий срок до запуска:** 12-17 недель (3-4 месяца)

---

## 💰 Оценка стоимости инфраструктуры

**Минимальная конфигурация для старта:**
- VPS сервер (8 GB RAM, 4 CPU): ~3,000 ₽/мес
- PostgreSQL (managed): ~1,500 ₽/мес
- Redis: ~500 ₽/мес
- Хранилище (100 GB): ~500 ₽/мес
- Домен + SSL: ~200 ₽/мес

**Итого:** ~5,700 ₽/мес базовая инфраструктура

**При росте (100+ пользователей):**
- Увеличение сервера: +5,000 ₽/мес
- CDN для статики: ~1,000 ₽/мес
- Мониторинг и логи: ~1,000 ₽/мес

**Итого при росте:** ~12,700 ₽/мес

---

## 🎯 Критичные метрики для отслеживания

1. **Продуктовые:**
   - Количество активных пользователей (DAU/MAU)
   - Конверсия: пробная → платная подписка
   - Retention (удержание пользователей)
   - Средний чек (ARPU)

2. **Технические:**
   - Время обработки анализа
   - Uptime сервиса (цель: 99.5%+)
   - Количество ошибок
   - Загрузка серверов

3. **Бизнес:**
   - MRR (месячный регулярный доход)
   - LTV (lifetime value пользователя)
   - CAC (стоимость привлечения клиента)
   - Churn rate (отток пользователей)

---

## 🚀 Быстрый старт (Quick Wins)

**Что можно сделать за 1-2 недели для первых продаж:**

1. **Минимальная монетизация:**
   - Добавить ограничение: 10 анализов без регистрации
   - Простая форма регистрации
   - Ручная оплата (перевод на счет)
   - Ручная активация тарифа

2. **Базовое улучшение UX:**
   - Добавить загрузку через drag&drop
   - Прогресс-бар при анализе
   - Toast уведомления об успехе/ошибке

3. **Простая аналитика:**
   - Google Analytics
   - Счетчик регистраций/платежей

---

## 📝 Чек-лист готовности к запуску

- [ ] Регистрация и авторизация работают
- [ ] Платежи интегрированы и протестированы
- [ ] База данных настроена и мигрирована
- [ ] Rate limiting активен
- [ ] Безопасность данных обеспечена (152-ФЗ)
- [ ] Мониторинг и логирование работают
- [ ] Документация для пользователей готова
- [ ] Техническая документация обновлена
- [ ] Резервное копирование настроено
- [ ] SSL сертификат установлен
- [ ] Домен настроен
- [ ] Поддержка готова отвечать

---

## 🎁 Дополнительные идеи для дифференциации

1. **Интеграции:**
   - Интеграция с ЕИС (Единая информационная система)
   - Экспорт в 1С
   - API для автоматизации

2. **AI улучшения:**
   - Обучение модели на исторических данных клиента
   - Персональные рекомендации
   - Автоматическое сравнение с похожими тендерами

3. **Коллаборация:**
   - Командные аккаунты
   - Общие папки с анализами
   - Комментарии и обсуждения

---

**Следующие шаги:**
1. Выбрать приоритетные задачи из Фазы 1
2. Настроить БД и миграции
3. Интегрировать платежную систему
4. Запустить закрытую бета-версию


