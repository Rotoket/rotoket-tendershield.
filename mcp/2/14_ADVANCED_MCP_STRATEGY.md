# 🚀 РАСШИРЕННАЯ MCP СТРАТЕГИЯ (14 СЕРВЕРОВ) ДЛЯ TENDERSHIELD

## 📊 ФАЗА-ПО-ФАЗНОЙ РЕАЛИЗАЦИИ

### ФАЗА 1 (СЕЙЧАС): 12 MCP для Phase 1 разработки

#### ✅ БАЗОВЫЕ (3):
1. **Sequential Thinking** - планирование архитектуры
2. **Context7** - актуальная документация
3. **Playwright** - E2E тесты

#### ✅ INFRASTRUCTURE (7):
4. **Filesystem** - создание файлов
5. **Git** - версионирование
6. **Postgres** - основная БД
7. **Docker** - контейнеризация
8. **Browser** - визуальная проверка
9. **Code Quality** - тесты и линтинг
10. **NPM** - управление зависимостями

#### 🆕 СПЕЦИФИЧНЫЕ ДЛЯ ПРОЕКТА (2):
11. **Vector DB MCP (Qdrant)** - подготовка к Phase 2
12. **Data Processing MCP (DuckDB)** - batch анализ тендеров

---

### ФАЗА 2 (ЧЕРЕЗ МЕСЯЦ): Дополнительные 2 MCP

#### 🆕 НОВЫЕ (2):
13. **Text Analysis MCP** - парсинг русскоязычных юридических документов
14. **API Integration MCP** - проверка в ЕГРЮЛ и госсервисах

---

## 🎯 НОВЫЕ MCP КОТОРЫЙ ДОБАВЛЯЕМ (ДЕТАЛЬНО)

### 1️⃣ VECTOR DB MCP (Qdrant) - КРИТИЧЕН!

**ЧТО ЭТО:**
Vector database для семантического поиска и RAG (Retrieval Augmented Generation)

**ПОЧЕМУ НУЖЕН:**
- Хранение нормативных документов ОТ (охрана труда)
- Поиск похожих тендеров по смыслу (не по keyword)
- Поддержка Smart Questions Generator (Phase 2)
- Улучшение accuracy анализа через контекст

**УСТАНОВКА:**
```bash
# В backend/requirements.txt добавить:
qdrant-client>=2.6.0

# Docker контейнер (в docker-compose.yml):
qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"
  volumes:
    - qdrant_storage:/qdrant/storage
  environment:
    QDRANT_API_KEY: your_api_key
```

**ИСПОЛЬЗОВАНИЕ В CURSOR:**
```
"Сохрани эту статью о штрафах в Vector DB"
→ Qdrant embeddings эту статью

"Найди похожие примеры штрафов для этого тендера"
→ Semantic search в Qdrant

"Дай мне примеры из судебной практики"
→ RAG (retrieval augmented generation)
```

**КЕЙС ДЛЯ TENDER SHIELD:**
```python
# Хранение нормативов ОТ
class OTDatabase(VectorDB):
    def store_regulation(self, text: str, source: str):
        # Embeddings через text-embedding-3-small
        # Сохранение в Qdrant
        pass
    
    def find_similar_cases(self, tender_text: str) -> List[Case]:
        # Semantic search в Qdrant
        # Возврат похожих прецедентов
        pass
```

---

### 2️⃣ DATA PROCESSING MCP (DuckDB) - ОЧЕНЬ ПОЛЕЗЕН!

**ЧТО ЭТО:**
Встроенная SQL БД для анализа табличных данных (вместо Pandas для больших файлов)

**ПОЧЕМУ НУЖЕН:**
- Работа с Excel/CSV таблицами тендеров
- Batch анализ 100+ тендеров одновременно
- Статистический анализ финансовых условий
- Экспорт результатов в разные форматы

**УСТАНОВКА:**
```bash
# В backend/requirements.txt добавить:
duckdb>=0.10.0
duckdb_engine>=0.11.0  # для SQLAlchemy
```

**ИСПОЛЬЗОВАНИЕ В CURSOR:**
```
"Прочитай Excel с 100 тендерами и сделай анализ"
→ DuckDB загружает файл

"Какой процент тендеров содержит штрафы?"
→ SELECT COUNT(*) WHERE has_penalties = true

"Дай мне статистику по финансовым условиям"
→ GROUP BY industry, ORDER BY average_penalty DESC
```

**КЕЙС ДЛЯ TENDER SHIELD:**
```python
# Batch анализ
class BatchAnalyzer(DataProcessor):
    def analyze_excel(self, file_path: str) -> AnalysisReport:
        # 1. Читаем Excel в DuckDB
        # 2. Для каждого тендера - Deal Breaker Detector
        # 3. Группируем по industries/regions
        # 4. Возвращаем статистику + аномалии
        pass
    
    def get_statistics(self, query: str) -> DataFrame:
        # SELECT с агрегацией
        # Возврат как CSV/JSON/DataFrame
        pass
```

---

### 3️⃣ TEXT ANALYSIS MCP (Специализированный) - ФАЗА 2

**ЧТО ЭТО:**
NER (Named Entity Recognition) + улучшенный парсинг русскоязычных юридических текстов

**ПОЧЕМУ НУЖЕН:**
- Deal Breaker Detector использует regex (хрупкий)
- Нужно извлекать сущности: суммы, даты, ФИО, компании
- Улучшение точности парсинга на 30-40%
- Работа с синонимами юридических терминов

**УСТАНОВКА:**
```bash
# В backend/requirements.txt добавить:
spacy>=3.7.0
natasha>=1.5.0  # NER для русского
pymorphy2>=0.9.1  # морфология

# Скачать модели:
python -m spacy download ru_core_news_lg
```

**ИСПОЛЬЗОВАНИЕ В CURSOR:**
```
"Найди все суммы в рублях в этом тексте"
→ NER извлекает: [1000000, 500000, 10000]

"Найди все ФИО руководителей компании"
→ NER извлекает: ["Иван Петров", "Мария Сидорова"]

"Какие даты упомянуты в документе?"
→ NER извлекает: ["2024-01-15", "2025-06-30"]
```

**КЕЙС ДЛЯ TENDER SHIELD:**
```python
# Улучшенный парсинг
class TextAnalyzer(NERProcessor):
    def extract_financial_terms(self, text: str) -> List[FinancialTerm]:
        # Находит все упоминания штрафов
        # Суммы, условия, сроки
        pass
    
    def extract_entities(self, text: str) -> EntityList:
        # Компании, ФИО, даты
        # С контекстом и уверенностью
        pass
```

---

### 4️⃣ API INTEGRATION MCP (ЕГРЮЛ/Госсервисы) - ФАЗА 2

**ЧТО ЭТО:**
Обёртка для проверки компаний в государственных реестрах

**ПОЧЕМУ НУЖЕН:**
- Проверка РЗ в ЕГРЮЛ перед анализом (снижение рисков)
- Проверка наличия лицензий и сертификатов
- Проверка судимостей руководителей
- Проверка статуса банкротства

**УСТАНОВКА:**
```bash
# Кастомное MCP нужно написать
# В backend/routes/api_integration.py:

@router.post("/api/check-egrul")
async def check_in_egrul(inn: str) -> EgrulCheckResult:
    # Вызов API ЕГРЮЛ
    # Парсинг результата
    # Возврат структурированного результата
    pass
```

**ИСПОЛЬЗОВАНИЕ В CURSOR:**
```
"Проверь компанию в ЕГРЮЛ: ИНН 7702999816"
→ Запрос в ЕГРЮЛ API

"Есть ли проблемы с налогами у этой РЗ?"
→ Проверка задолженности

"Активна ли лицензия на закупки?"
→ Проверка статуса лицензий
```

**КЕЙС ДЛЯ TENDER SHIELD:**
```python
# Проверка контрагентов
class CompanyChecker(APIIntegrator):
    def check_in_egrul(self, inn: str) -> CompanyStatus:
        # ЕГРЮЛ API
        # Возврат: статус, задолженность, директора
        pass
    
    def check_licenses(self, inn: str) -> LicenseList:
        # Проверка лицензий на ОТ
        # Проверка других релевантных лицензий
        pass
    
    def assess_risk(self, inn: str) -> RiskScore:
        # Комбинированный риск-скор
        # На основе всех проверок
        pass
```

---

## 📋 ИТОГОВАЯ КОНФИГУРАЦИЯ (12 + 2 MCP)

### PHASE 1 config:
```json
{
  "mcpServers": {
    // Базовые (уже есть)
    "sequential-thinking": {...},
    "context7": {...},
    "playwright": {...},
    
    // Infrastructure
    "filesystem": {...},
    "git": {...},
    "postgres": {...},
    "docker": {...},
    "browser": {...},
    "code-quality": {...},
    "npm": {...},
    
    // НОВЫЕ специфичные
    "qdrant": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-qdrant"],
      "env": {
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6333"
      },
      "timeout": 30000,
      "description": "Vector database for semantic search"
    },
    
    "duckdb": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-duckdb"],
      "timeout": 60000,
      "description": "Data processing and analysis"
    }
  }
}
```

---

## 💡 ПРИМЕРЫ WORKFLOWS С НОВЫМИ MCP

### WORKFLOW 1: Полный анализ тендера
```
ПОЛЬЗОВАТЕЛЬ: Загружает текст тендера

ТЫ В CURSOR:
"Проанализируй этот тендер:
1. Deal Breaker Detector (regex)
2. Text Analysis MCP (NER) - извлеки суммы, даты
3. API Integration MCP - проверь РЗ в ЕГРЮЛ
4. Vector DB MCP - найди похожие тендеры
5. Дай recommendation"

РЕЗУЛЬТАТ:
✓ Deal breakers: [штраф 1000000, неактуальный стандарт ОТ]
✓ Entities: [суммы, даты, ФИО, компании]
✓ Company status: РИСК ВЫСОКИЙ (задолженность по налогам)
✓ Similar cases: 3 похожих тендера в судебной практике
✓ Recommendation: SKIP THIS TENDER (слишком много красных флагов)
```

### WORKFLOW 2: Batch анализ из Excel
```
ПОЛЬЗОВАТЕЛЬ: Загружает Excel с 100 тендерами

ТЫ В CURSOR:
"Обработай файл:
1. Data Processing MCP - прочитай Excel
2. Для каждого - Deal Breaker Detector
3. API Integration MCP - проверь все компании
4. Vector DB MCP - найди кластеры
5. Дай статистику"

РЕЗУЛЬТАТ:
✓ Processed: 100 tenders
✓ Deal breakers found: 47 (47%)
✓ High-risk companies: 23 (23%)
✓ Similar clusters: 5 groups
✓ CSV export: analysis_2024_12_12.csv
```

### WORKFLOW 3: Улучшение парсинга
```
ТЫ В CURSOR:
"Improve regex patterns using Text Analysis MCP:
- Текущая accuracy: 75%
- Нужно: 90%
- Используй NER для лучшего извлечения сумм"

РЕЗУЛЬТАТ:
✓ Новые patterns созданы
✓ Accuracy улучшена до 88%
✓ Тесты пройдены
✓ Коммит: "feat: Improve text parsing with NER"
```

---

## 📊 СРАВНЕНИЕ: БЕЗ MCP vs С MCP

| Задача | Без MCP | С MCP | Улучшение |
|--------|---------|-------|-----------|
| Анализ 1 тендера | 10 мин | 2 мин | 5x |
| Batch 100 тендеров | 3 часа | 15 мин | 12x |
| Проверка компании | 30 мин | 1 мин | 30x |
| Поиск похожих | 1 час | 30 сек | 120x |
| Генерация report | 45 мин | 5 мин | 9x |

---

## 🔧 IMPLEMENTATION ROADMAP

### ЭТА НЕДЕЛЯ (Phase 1 базовые работают):
- ✅ 10 текущих MCP
- ✅ Cursor rules для каждого
- ✅ 3 примера workflow'а

### СЛЕДУЮЩАЯ НЕДЕЛЯ (добавляем Qdrant + DuckDB):
- 📦 Qdrant контейнер запущен
- 📦 DuckDB интегрирован
- 📦 Первые примеры тендеров загружены в Qdrant
- 📦 Batch анализ 50 тендеров из Excel работает

### ЧЕРЕЗ МЕСЯЦ (Phase 2):
- 📦 Text Analysis MCP работает
- 📦 API Integration MCP для ЕГРЮЛ
- 📦 Полный workflow анализа
- 📦 Статистика и reporting

---

## ✅ CHECKLIST ВНЕДРЕНИЯ

### Для VECTOR DB (Qdrant):
- [ ] Docker контейнер запущен
- [ ] Qdrant client установлен в backend
- [ ] Примеры нормативов загружены
- [ ] Поиск работает (semantic search)
- [ ] Интегрирован в анализ тендеров

### Для DATA PROCESSING (DuckDB):
- [ ] DuckDB установлен
- [ ] Примеры Excel загружены
- [ ] SQL запросы работают
- [ ] Batch анализ работает
- [ ] Экспорт в CSV/JSON работает

### Для TEXT ANALYSIS (Phase 2):
- [ ] Spacy модель для русского загружена
- [ ] NER примеры работают
- [ ] Извлечение сумм/дат работает
- [ ] Интегрировано в Deal Breaker Detector

### Для API INTEGRATION (Phase 2):
- [ ] ЕГРЮЛ API обёртка написана
- [ ] Тесты написаны
- [ ] Интегрировано в анализ
- [ ] Безопасность ключей настроена

---

## 🎯 FINAL SETUP (добавь в mcp.json после текущих 10)

```json
{
  "mcpServers": {
    // ... 10 текущих ...
    
    "qdrant": {
      "command": "docker",
      "args": ["run", "-d", "-p", "6333:6333", "qdrant/qdrant"],
      "timeout": 30000,
      "description": "Vector DB for semantic search and RAG"
    },
    
    "duckdb": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-duckdb"],
      "timeout": 60000,
      "description": "SQL engine for data analysis"
    }
  }
}
```

---

**ЭТО РАСШИРЕНИЕ ДАСТ ТЕ НЕДОСТАЮЩИЕ 30% ФУНКЦИОНАЛЬНОСТИ ДЛЯ ПОЛНОГО ПРОИЗВОДСТВА-READY РЕШЕНИЯ!**

🚀 **Начни с Qdrant + DuckDB (Phase 1), потом добавь Text Analysis + API Integration (Phase 2)**
