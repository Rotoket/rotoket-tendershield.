# Интеграция ШАГОВ 3, 4, 5 — Полный пайплайн

## Обзор интеграции

Все три архитектурных слоя (ШАГ 3, 4, 5) интегрированы в единый пайплайн анализа документов.

## 🔄 Поток данных

```
Файл → ШАГ 3 (Evidence Layer) → ШАГ 4 (Reasoning Layer) → ШАГ 5 (Decision Preview) → UI
```

### ШАГ 3: Preprocessing & Evidence Layer
- **Вход:** Файл (PDF, Excel, DOCX, чертежи)
- **Выход:** `EvidenceObject[]`
- **Модуль:** `backend/preprocessor.py`
- **Статус:** ✅ Интегрирован в `analyze_single_file()`

### ШАГ 4: Reasoning & Decision Layer
- **Вход:** `EvidenceObject[]`
- **Выход:** `ReasoningResult` (Risk Signals, Contradictions, Decision Preview, Decision Graph)
- **Модуль:** `backend/reasoning_layer.py`
- **Статус:** ✅ Интегрирован в `analyze_single_file()`

### ШАГ 5: Decision Preview Formatter
- **Вход:** `DecisionPreview` (из ReasoningResult)
- **Выход:** Отформатированный `DecisionPreview` (board-ready)
- **Модуль:** `backend/decision_preview_formatter.py`
- **Статус:** ✅ Интегрирован в `analyze_single_file()`

## 📦 Backend интеграция

### `backend/main.py`

#### Импорты
```python
# ШАГ 3
from preprocessor import EvidencePreprocessor
from evidence_adapter import evidence_objects_to_llm_prompt, evidence_objects_to_summary

# ШАГ 4
from reasoning_layer import ReasoningEngine
from reasoning_types import ReasoningResult

# ШАГ 5
from decision_preview_formatter import DecisionPreviewFormatter
```

#### Пайплайн в `analyze_single_file()`

1. **ШАГ 3:** Извлечение Evidence Objects
```python
preprocessor = EvidencePreprocessor()
preprocessing_result = await preprocessor.preprocess_file(temp_path, filename, industry)
evidence_objects = preprocessing_result.evidence_objects
```

2. **ШАГ 4:** Reasoning на Evidence Objects
```python
reasoning_engine = ReasoningEngine()
reasoning_result = reasoning_engine.process_evidence(evidence_objects, industry)
```

3. **ШАГ 5:** Форматирование Decision Preview
```python
formatter = DecisionPreviewFormatter()
formatted_decision_preview = formatter.format_preview(reasoning_result.decision_preview)
```

4. **Результат:** Добавление в финальный ответ
```python
result = {
    # ... существующие поля ...
    "decision_preview_step5": formatted_decision_preview,
    "decision_graph": reasoning_result.decision_graph.dict() if reasoning_result else None,
}
```

## 🎨 Frontend интеграция

### `frontend/src/components/audit/DecisionPreview.tsx`

#### Проверка наличия Step5 preview
```typescript
const step5Preview = (result as any).decision_preview_step5;
const decisionGraph = (result as any).decision_graph;

// Если есть Step5 preview, используем его (приоритет)
if (step5Preview && previewData) {
  return <DecisionPreviewStep5 previewData={previewData} ... />;
}

// Fallback на оригинальный DecisionPreview
return <div>...</div>;
```

### `frontend/src/components/audit/DecisionPreviewStep5.tsx`

Компонент отображает:
- 🧭 Управленческий вывод (главное)
- 🟥 DEAL_BREAKER (если есть)
- 🟨 Управляемые риски (скрыты по умолчанию)
- 🔒 Audit Trail (скрыт, доступен по запросу)

## ✅ Проверка интеграции

### Backend
- [x] ШАГ 3 вызывается в `analyze_single_file()`
- [x] ШАГ 4 вызывается после ШАГА 3 (если есть Evidence Objects)
- [x] ШАГ 5 вызывается после ШАГА 4 (если есть ReasoningResult)
- [x] `decision_preview_step5` добавляется в результат
- [x] `decision_graph` добавляется в результат

### Frontend
- [x] `DecisionPreviewStep5` импортирован в `DecisionPreview`
- [x] Проверка наличия `step5Preview` реализована
- [x] Fallback на оригинальный компонент работает

## 🔄 Fallback механизм

Если какой-то шаг недоступен:
1. **ШАГ 3 недоступен** → используется сырой текст (старый подход)
2. **ШАГ 4 недоступен** → используется LLM reasoning (старый подход)
3. **ШАГ 5 недоступен** → используется оригинальный `DecisionPreview` компонент

## 📊 Логирование

Все шаги логируют свой статус:
- ✅ Успешное выполнение
- ⚠️ Предупреждения (fallback)
- ❌ Ошибки (fallback)

## 🚀 Следующие шаги

1. Тестирование на реальных данных
2. Оптимизация производительности
3. Расширение MCP-интеграции для ШАГА 3
4. Улучшение детектора противоречий в ШАГЕ 4































