# ШАГ 3: Preprocessing & Evidence Layer

## Архитектурный контракт

Этот документ описывает архитектурный слой препроцессинга документов для Tender Shield Pro. Любые изменения кода, MCP, пайплайна или логики НЕ ДОЛЖНЫ нарушать изложенные ниже принципы.

## 🎯 Цель ШАГА 3

Создать детерминированный, формат-осознанный слой препроцессинга, который преобразует Excel, PDF, сканы и чертежи в проверяемые Evidence Objects, до передачи данных в LLM.

## 🚫 LLM НЕ ИМЕЕТ ПРАВА

LLM НЕ извлекает:
- таблицы
- суммы
- структуру документов
- выводы из сырого OCR

LLM используется исключительно для **reasoning** на основе готовых Evidence.

## 🧱 Архитектурные принципы

### 1. LLM ≠ Extractor

LLM не участвует в:
- OCR
- table extraction
- parsing Excel
- interpreting drawings

Любая попытка «упростить» и отдать это LLM считается архитектурным дефектом.

### 2. Format-Aware Preprocessing (обязателен)

Каждый файл до анализа классифицируется по типу:
- `excel_structured`
- `pdf_textual`
- `pdf_scanned`
- `pdf_with_tables`
- `drawing_vector`
- `drawing_scanned`
- `docx_textual`

Неверная классификация = недостоверный анализ.

### 3. MCP — только специализированные

Допустимы только специализированные MCP-ноды:
- `excel-mcp`
- `pdf-table-mcp`
- `pdf-ocr-mcp`
- `drawing-metadata-mcp`

Единый универсальный препроцессор запрещён.

Каждый MCP обязан:
- работать детерминированно
- возвращать confidence
- указывать источник ошибки

### 4. Excel — источник истины (highest confidence)

Для Excel файлов обязательно извлекаются:
- таблицы (структура)
- формулы (не только значения)
- межлистовые зависимости
- итоговые поля
- валюты и единицы измерения

LLM НЕ СЧИТАЕТ Excel данные.

### 5. PDF и OCR — только с валидацией

OCR данные:
- никогда не идут напрямую в LLM
- сопровождаются confidence map
- при низкой уверенности маркируются как `CONTROLLED_RISK: LOW_EVIDENCE`

### 6. Чертежи — только метаданные

Из чертежей извлекаются только управленческие сигналы, а не геометрия:
- стадия проектирования
- полнота спецификаций
- ссылки на нормы
- ожидаемая координационная нагрузка

Попытка «понять чертёж» через LLM запрещена.

## 📦 Единственный допустимый выход ШАГА 3

### Evidence Object (обязательный формат)

```python
{
  "evidence_id": "E-XXXX",
  "source_file": "string",
  "fact": "string",
  "classification": "DEAL_BREAKER | CONTROLLED_RISK | MARKET_NOISE",
  "financial_impact_rub": number | null,
  "confidence": "high | medium | low",
  "derived_from": ["mcp-node-id"],
  "page_reference": "string | null",
  "section_reference": "string | null",
  "raw_extract": "string | null"
}
```

LLM работает только с этим форматом.

## 🔗 Связь с другими шагами

**ШАГ 3 НЕ ПРИНИМАЕТ РЕШЕНИЙ**

**ШАГ 3 НЕ ВЫСТАВЛЯЕТ ИУН**

**ШАГ 3 НЕ АГРЕГИРУЕТ РИСКИ**

Он:
- поставляет Evidence
- фиксирует уверенность
- формирует Audit Trail

## 🚫 Анти-паттерны (строго запрещены)

- передача raw OCR / PDF текста в LLM
- «временные» парсеры без confidence
- попытка оптимизации за счёт reasoning модели
- скрытые вычисления внутри LLM
- недетерминированный результат

## ✅ Критерий корректности ШАГА 3

Если:
- LLM отключить полностью
- Evidence Objects сохранить
- Decision пересчитать позже

➡️ результат должен быть воспроизводимым.

## 📁 Структура кода

### `backend/evidence_types.py`
Определяет канонические типы:
- `EvidenceObject`
- `EvidenceClassification`
- `EvidenceConfidence`
- `FileFormatType`
- `PreprocessingResult`

### `backend/preprocessor.py`
Ядро препроцессора:
- `FileClassifier` — классификация файлов
- `EvidencePreprocessor` — извлечение Evidence Objects

### `backend/evidence_adapter.py`
Адаптер для LLM:
- `evidence_objects_to_llm_prompt()` — преобразование Evidence в промпт
- `evidence_objects_to_summary()` — сводка для логирования

## 🔄 Интеграция в пайплайн

1. Файл загружается на сервер
2. `EvidencePreprocessor.preprocess_file()` классифицирует и извлекает Evidence
3. `evidence_objects_to_llm_prompt()` преобразует Evidence в промпт
4. LLM получает только готовые Evidence, не сырой текст
5. Если Evidence Layer недоступен — fallback на сырой текст (старый подход)

## 📊 Статус реализации

- ✅ Типы Evidence Objects
- ✅ Классификатор файлов
- ✅ Ядро препроцессора
- ✅ Адаптер для LLM
- ✅ Интеграция в `analyze_single_file`
- ⏳ Excel extractor (MCP интеграция)
- ⏳ PDF OCR validator (MCP интеграция)
- ⏳ Drawing metadata extractor (MCP интеграция)
- ⏳ Audit Trail для Evidence extraction

## 🔒 Статус Prompt

Этот prompt:
- является архитектурным контрактом
- должен использоваться во всех Cursor-агентах
- не может быть изменён без пересмотра всей системы































