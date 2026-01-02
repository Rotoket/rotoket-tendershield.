# ШАГ 9: Reference Implementation Map (Code & MCP Boundaries)

**Статус:** Каноническая карта реализации Tender Shield Pro

**Цель:** Зафиксировать:
- слои системы
- границы ответственности
- допустимые точки расширения
- места, где запрещена импровизация

**ШАГ 9 НЕ добавляет фичи**  
**ШАГ 9 НЕ оптимизирует производительность**  
**ШАГ 9 ЗАЩИЩАЕТ ЦЕЛОСТНОСТЬ РЕШЕНИЯ**

---

## 🧱 КАНОНИЧЕСКАЯ СЛОЁНАЯ АРХИТЕКТУРА

```
┌─────────────────────────────────────────┐
│         UI Layer                         │
│  (React Components, User Interaction)     │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  Decision Presentation Layer (ШАГ 5)    │
│  (DecisionPreview, Board-Ready Format)  │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  Decision Logic Layer (ШАГ 4)           │
│  (RiskSignal, Contradiction,            │
│   DecisionGraph, Reasoning)             │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  Evidence Layer (ШАГ 3)                  │
│  (EvidenceObject[], Normalization)      │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  MCP Extraction Layer (ШАГ 3)           │
│  (excel-mcp, pdf-table-mcp,             │
│   pdf-ocr-mcp, drawing-metadata-mcp)    │
└─────────────────┬───────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────┐
│  Raw Documents / Storage                │
│  (Files, Database, File System)         │
└─────────────────────────────────────────┘
```

### ❌ Запрещено:

- пропускать слои
- обращаться «напрямую вниз»
- смешивать логику между слоями

---

## 1️⃣ MCP EXTRACTION LAYER (ШАГ 3)

### Назначение

- извлечение фактов
- детерминированный препроцессинг
- формат-осознанная обработка

### Допустимые MCP:

- `excel-mcp` — обработка Excel файлов
- `pdf-table-mcp` — извлечение таблиц из PDF
- `pdf-ocr-mcp` — OCR для сканированных PDF
- `drawing-metadata-mcp` — метаданные чертежей

### Обязанности MCP:

✅ принимать один тип входа  
✅ возвращать структурированные данные  
✅ возвращать confidence  
✅ логировать ошибки

### ❌ MCP НЕ ИМЕЕТ ПРАВА:

- принимать решения
- интерпретировать риск
- обращаться к LLM
- агрегировать данные
- формировать выводы

### Канонический интерфейс MCP:

```python
class MCPProcessor:
    def process(self, file_path: str, file_type: FileFormatType) -> MCPResult:
        """
        Обрабатывает файл и возвращает структурированные данные.
        
        Returns:
            MCPResult с полями:
            - data: Dict[str, Any]  # структурированные данные
            - confidence: float      # уверенность (0.0-1.0)
            - errors: List[str]     # список ошибок
            - source_refs: List[str] # ссылки на источники
        """
        pass
```

### Файлы слоя:

- `backend/preprocessor.py` — `FileClassifier`, `EvidencePreprocessor`
- `backend/evidence_types.py` — `FileFormatType`, `EvidenceObject`
- `mcp/*/` — MCP-ноды для разных форматов

---

## 2️⃣ EVIDENCE LAYER (ШАГ 3)

### Назначение

- нормализация данных
- семантическое выравнивание
- формирование Evidence Objects

### Допустимые выходы:

- `EvidenceObject[]` — список проверяемых фактов

### Правила:

✅ один Evidence = один проверяемый факт  
✅ Evidence неизменяем после фиксации  
✅ любые изменения = новая версия  
✅ каждый Evidence имеет `evidence_id`, `source_file`, `fact`, `classification`, `confidence`

### ❌ Запрещено:

- агрегировать Evidence
- «улучшать» формулировки
- терять ссылку на источник
- изменять существующие Evidence
- создавать Evidence без источника

### Файлы слоя:

- `backend/evidence_types.py` — `EvidenceObject`, `PreprocessingResult`
- `backend/evidence_adapter.py` — адаптеры для преобразования MCP → Evidence
- `backend/preprocessor.py` — `EvidencePreprocessor`

### Канонический интерфейс:

```python
class EvidencePreprocessor:
    def extract_evidence(self, file_path: str) -> PreprocessingResult:
        """
        Извлекает Evidence Objects из файла.
        
        Returns:
            PreprocessingResult с полями:
            - evidence_objects: List[EvidenceObject]
            - file_format: FileFormatType
            - raw_text_content: Optional[str]
            - error: Optional[str]
        """
        pass
```

---

## 3️⃣ DECISION LOGIC LAYER (ШАГ 4)

### Назначение

- формирование Risk Signals
- выявление противоречий
- построение Decision Graph

### Допустимые сущности:

- `RiskSignal` — управленческое следствие из Evidence
- `Contradiction` — противоречия между Evidence
- `DecisionGraph` — граф решения (Evidence → Risk → Contradiction → Load → Decision)
- `DecisionPreview` — предварительный вывод для директора

### Правила:

✅ reasoning ТОЛЬКО здесь  
✅ DEAL_BREAKER абсолютен  
✅ логика объяснима без UI  
✅ один Risk может быть выведен из нескольких Evidence  
✅ Decision Graph обязателен для каждого решения

### ❌ Запрещено:

- работать с файлами
- видеть OCR / таблицы
- формировать тексты для пользователя
- обращаться к MCP напрямую
- изменять Evidence Objects
- скрывать DEAL_BREAKER

### Файлы слоя:

- `backend/reasoning_types.py` — `RiskSignal`, `Contradiction`, `DecisionGraph`, `DecisionPreview`
- `backend/reasoning_layer.py` — `ReasoningEngine`, `DealBreakerRules`, `ContradictionDetector`

### Канонический интерфейс:

```python
class ReasoningEngine:
    def process_evidence(
        self, 
        evidence_objects: List[EvidenceObject]
    ) -> ReasoningResult:
        """
        Преобразует Evidence Objects в Risk Signals и Decision Graph.
        
        Input:
            evidence_objects: List[EvidenceObject]  # только из Evidence Layer
        
        Returns:
            ReasoningResult с полями:
            - risk_signals: List[RiskSignal]
            - contradictions: List[Contradiction]
            - decision_graph: DecisionGraph
            - decision_preview: DecisionPreview
        """
        pass
```

---

## 4️⃣ DECISION PRESENTATION LAYER (ШАГ 5)

### Назначение

- превратить Decision Graph в управленческий вывод
- обеспечить board-ready формат

### Выход:

- `DecisionPreview` (отформатированный)

### Правила:

✅ один экран = одно решение  
✅ максимум 2–4 причины  
✅ никакой аналитики  
✅ язык директора (без AI-лексики)  
✅ скрытие второстепенных деталей

### ❌ Запрещено:

- пересчитывать риски
- добавлять новые смыслы
- «улучшать UX» за счёт логики
- показывать все риски
- использовать вероятностные формулировки
- обращаться к Evidence напрямую

### Файлы слоя:

- `backend/decision_preview_formatter.py` — `DecisionPreviewFormatter`
- `frontend/src/components/audit/DecisionPreviewStep5.tsx` — UI компонент

### Канонический интерфейс:

```python
class DecisionPreviewFormatter:
    def format_preview(
        self, 
        decision_graph: DecisionGraph
    ) -> FormattedDecisionPreview:
        """
        Форматирует Decision Graph в board-ready формат.
        
        Input:
            decision_graph: DecisionGraph  # только из Decision Logic Layer
        
        Returns:
            FormattedDecisionPreview с полями:
            - decision_label: str
            - why: List[str]  # 2-4 причины
            - main_risk: Optional[str]
            - management_load: ManagementLoadExplanation
            - risk_mitigation: Optional[List[str]]
        """
        pass
```

---

## 5️⃣ AUDIT & VERSIONING LAYER (ШАГ 6)

### Назначение

- snapshot'ы
- версии
- актуальность решения
- воспроизводимость

### Правила:

✅ append-only  
✅ immutable snapshots  
✅ явные статусы ACTUAL / STALE / INVALIDATED  
✅ каждый snapshot имеет hash входных данных  
✅ явные связи `derived_from`

### ❌ Запрещено:

- перезаписывать историю
- чинить прошлые решения
- скрывать устаревание
- изменять существующие snapshots
- удалять snapshots

### Файлы слоя:

- `backend/audit_trail_types.py` — `DocumentSnapshot`, `EvidenceSnapshot`, `DecisionSnapshot`
- `backend/audit_trail_manager.py` — `AuditTrailManager`

### Канонический интерфейс:

```python
class AuditTrailManager:
    def create_document_snapshot(
        self, 
        files: List[FileMetadata]
    ) -> DocumentSnapshot:
        """Создаёт immutable snapshot документов."""
        pass
    
    def create_evidence_snapshot(
        self, 
        evidence_objects: List[EvidenceObject],
        derived_from: str
    ) -> EvidenceSnapshot:
        """Создаёт immutable snapshot Evidence Objects."""
        pass
    
    def create_decision_snapshot(
        self, 
        decision_preview: DecisionPreview,
        derived_from: str
    ) -> DecisionSnapshot:
        """Создаёт immutable snapshot решения."""
        pass
    
    def check_freshness(
        self, 
        decision_snapshot_id: str
    ) -> DecisionFreshnessStatus:
        """Проверяет актуальность решения."""
        pass
```

---

## 6️⃣ CROSS-CUTTING: EXPERT OPINION LAYER (ШАГ 7)

### Назначение

- фиксация сомнений
- защита решений в будущем

### Правила:

✅ read-only для Decision  
✅ не влияет на ИУН  
✅ всегда отдельно от Risk  
✅ не может редактироваться после сохранения  
✅ логируется в Audit Trail

### ❌ Запрещено:

- влиять на классификацию рисков
- влиять на расчёт ИУН
- влиять на итоговое решение
- блокировать участие
- менять статус решения

### Файлы слоя:

- `frontend/src/types.ts` — `ExpertOpinion`
- `frontend/src/utils/expertOpinionStorage.ts`
- `frontend/src/components/audit/DecisionPreview.tsx` — UI для Expert Opinion

---

## 7️⃣ UI LAYER

### Назначение

- показать решение
- не мешать директору

### Правила:

✅ решение — в центре  
✅ аналитика — по запросу  
✅ audit — скрыт  
✅ один экран = одно решение  
✅ скрытие второстепенных деталей

### ❌ Запрещено:

- превращать UI в дашборд
- показывать «все риски»
- стимулировать копание
- показывать вероятности
- использовать AI-лексику
- обращаться к backend слоям напрямую

### Файлы слоя:

- `frontend/src/components/audit/DecisionPreviewStep5.tsx` — главный компонент решения
- `frontend/src/components/audit/DecisionFreshnessGuard.tsx` — предупреждение об устаревании
- `frontend/src/components/audit/DealBreakersPanel.tsx` — панель DEAL_BREAKER'ов
- `frontend/src/components/audit/FinancialMetricsGrid.tsx` — финансовые метрики
- `frontend/src/components/decision/DecisionBlock.tsx` — блок фиксации решения

---

## 8️⃣ ТОЧКИ РАСШИРЕНИЯ (РАЗРЕШЕНО)

### Разрешены ТОЛЬКО:

1. **Новые MCP** (новый формат документов)
   - Добавить новый MCP-процессор
   - Зарегистрировать в `FileClassifier`
   - Обновить `FileFormatType` enum

2. **Новые Reason Codes отказа**
   - Добавить в `DecisionReasonCode` enum
   - Обновить `extract_reason_codes_from_decision()`

3. **Новые типы Evidence**
   - Добавить новый `EvidenceClassification` (если необходимо)
   - Обновить `EvidenceObject` (осторожно!)

4. **Новые визуальные представления Decision Preview** (без изменения смысла)
   - Создать новый UI-компонент
   - Использовать тот же `DecisionPreviewData`

### Каждое расширение:

✅ не ломает шаги 3–7  
✅ не меняет границы слоёв  
✅ проходит через versioning  
✅ документируется  
✅ тестируется

---

## 🚫 АБСОЛЮТНЫЕ АНТИ-ПАТТЕРНЫ

### Запрещённые формулировки в коде / PR / обсуждениях:

❌ «быстро протащим данные»  
❌ «временно добавим в UI»  
❌ «пусть LLM сам решит»  
❌ «потом поправим архитектуру»  
❌ «это же просто рефактор»  
❌ «для удобства сделаем так»  
❌ «это не критично, можно нарушить границы»  
❌ «оптимизируем, убрав слой»

**Все они = нарушение Manifest.**

### Что делать вместо этого:

✅ «добавим новый MCP для формата X»  
✅ «расширим Reason Codes»  
✅ «создадим новый UI-компонент для Decision Preview»  
✅ «обновим документацию архитектуры»

---

## ✅ КРИТЕРИЙ КОРРЕКТНОСТИ ШАГА 9

Если:

- новый разработчик читает этот документ
- пишет код
- и не задаёт вопросов «а где это делать»

➡️ **архитектура работает.**

Если возникают вопросы — границы нарушены.

---

## 🔒 СТАТУС PROMPT

- ✅ обязателен для Cursor
- ✅ обязателен для code review
- ✅ обязателен для онбординга
- ✅ обязателен для CI (архитектурные чеки)

---

## 📦 РЕАЛИЗАЦИЯ

### Файлы карты:

- `docs/step9_reference_implementation_map.md` — этот документ
- `backend/architecture_compliance_checker.py` — автоматическая проверка соответствия

### Визуализация:

```
┌─────────────────────────────────────────────────────────────┐
│                    UI Layer                                  │
│  (React Components, User Interaction)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│         Decision Presentation Layer (ШАГ 5)                  │
│  (DecisionPreview, Board-Ready Format)                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Decision Logic Layer (ШАГ 4)                    │
│  (RiskSignal, Contradiction, DecisionGraph, Reasoning)      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Evidence Layer (ШАГ 3)                      │
│  (EvidenceObject[], Normalization)                           │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│            MCP Extraction Layer (ШАГ 3)                       │
│  (excel-mcp, pdf-table-mcp, pdf-ocr-mcp, etc.)             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              Raw Documents / Storage                         │
│  (Files, Database, File System)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧠 СМЫСЛ ШАГА 9

**Архитектура — это не код, а запрет на неправильный код.**

ШАГ 9 защищает целостность решения, фиксируя:
- что можно делать
- что нельзя делать
- где можно расширять
- где запрещена импровизация

Это карта для разработчиков, которая гарантирует, что система останется **decision system для директора**, а не превратится в аналитику или автоматизацию.































