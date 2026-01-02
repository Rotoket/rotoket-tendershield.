# Полная интеграция ШАГОВ 3-6 — Единый пайплайн

## Обзор

Все архитектурные слои (ШАГИ 3, 4, 5, 6) интегрированы в единый пайплайн анализа документов Tender Shield Pro.

## 🔄 Полный поток данных

```
Файл
  ↓
ШАГ 6: Document Snapshot (фиксация входных данных)
  ↓
ШАГ 3: Evidence Layer → EvidenceObject[]
  ↓
ШАГ 6: Evidence Snapshot (фиксация Evidence)
  ↓
ШАГ 4: Reasoning Layer → ReasoningResult
  ↓
ШАГ 5: Decision Preview Formatter → formatted_decision_preview
  ↓
ШАГ 6: Decision Snapshot (фиксация решения)
  ↓
ШАГ 6: Decision Freshness Guard (проверка актуальности)
  ↓
Frontend: DecisionPreviewStep5 + DecisionFreshnessGuard → UI
```

## 📦 Backend интеграция

### `backend/main.py` — `analyze_single_file()`

#### Последовательность выполнения:

1. **ШАГ 6: Document Snapshot**
   ```python
   document_snapshot = audit_manager.create_document_snapshot(files=[...], industry=industry)
   ```

2. **ШАГ 3: Evidence Layer**
   ```python
   preprocessing_result = await preprocessor.preprocess_file(temp_path, filename, industry)
   evidence_objects = preprocessing_result.evidence_objects
   ```

3. **ШАГ 6: Evidence Snapshot**
   ```python
   evidence_snapshot = audit_manager.create_evidence_snapshot(
       document_snapshot_id=document_snapshot.snapshot_id,
       evidence_objects=evidence_objects_dict
   )
   ```

4. **ШАГ 4: Reasoning Layer**
   ```python
   reasoning_result = reasoning_engine.process_evidence(evidence_objects, industry)
   ```

5. **ШАГ 6: Decision Snapshot**
   ```python
   decision_snapshot = audit_manager.create_decision_snapshot(
       evidence_snapshot_id=evidence_snapshot_id,
       decision=reasoning_result.decision_preview.decision,
       decision_preview=reasoning_result.decision_preview.dict(),
       decision_graph=reasoning_result.decision_graph.dict()
   )
   ```

6. **ШАГ 5: Decision Preview Formatter**
   ```python
   formatted_decision_preview = formatter.format_preview(reasoning_result.decision_preview)
   ```

7. **Результат:**
   ```python
   result = {
       # ... существующие поля ...
       "decision_preview_step5": formatted_decision_preview,
       "decision_graph": decision_graph_data,
       "audit_trail": {
           "document_snapshot_id": document_snapshot.snapshot_id,
           "evidence_snapshot_id": evidence_snapshot.evidence_set_id,
           "decision_snapshot_id": decision_snapshot.decision_id,
           "freshness_status": decision_snapshot.freshness_status.value,
       }
   }
   ```

## 🎨 Frontend интеграция

### `frontend/src/components/audit/DecisionPreview.tsx`

#### Проверка наличия Step5 preview и Audit Trail:
```typescript
const step5Preview = (result as any).decision_preview_step5;
const auditTrail = (result as any).audit_trail;
const freshnessStatus = auditTrail?.freshness_status || 'ACTUAL';
```

#### Использование DecisionPreviewStep5:
```typescript
if (step5Preview && previewData) {
  return (
    <DecisionPreviewStep5
      previewData={previewData}
      freshnessStatus={freshnessStatus}
      freshnessReason={auditTrail?.freshness_reason}
      decisionSnapshotId={auditTrail?.decision_snapshot_id}
    />
  );
}
```

### `frontend/src/components/audit/DecisionPreviewStep5.tsx`

Компонент отображает:
- 🛡️ **DecisionFreshnessGuard** (если решение устарело)
- 🧭 **Управленческий вывод** (главное)
- 🟥 **DEAL_BREAKER** (если есть)
- 🟨 **Управляемые риски** (скрыты по умолчанию)
- 🔒 **Audit Trail** (скрыт, доступен по запросу)

### `frontend/src/components/audit/DecisionFreshnessGuard.tsx`

UI-компонент для отображения статуса актуальности:
- **ACTUAL** — скрыт по умолчанию (показывается только при `showDetails=true`)
- **STALE** — предупреждение (жёлтый)
- **INVALIDATED** — критическое предупреждение (красный)

## ✅ Проверка интеграции

### Backend
- [x] ШАГ 6: Document Snapshot создаётся в начале анализа
- [x] ШАГ 3: Evidence Layer извлекает Evidence Objects
- [x] ШАГ 6: Evidence Snapshot создаётся после ШАГА 3
- [x] ШАГ 4: Reasoning Layer преобразует Evidence → Decision
- [x] ШАГ 6: Decision Snapshot создаётся после ШАГА 4
- [x] ШАГ 5: Decision Preview форматируется для board-ready вывода
- [x] Audit Trail данные добавляются в результат

### Frontend
- [x] DecisionPreviewStep5 импортирован и используется
- [x] DecisionFreshnessGuard интегрирован в DecisionPreviewStep5
- [x] Статус актуальности передаётся из backend
- [x] UI показывает предупреждение для устаревших решений

## 🔄 Fallback механизм

Если какой-то шаг недоступен:
1. **ШАГ 3 недоступен** → используется сырой текст
2. **ШАГ 4 недоступен** → используется LLM reasoning
3. **ШАГ 5 недоступен** → используется оригинальный DecisionPreview
4. **ШАГ 6 недоступен** → решения не версионируются (но система работает)

## 📊 Логирование

Все шаги логируют свой статус:
- ✅ Успешное выполнение
- ⚠️ Предупреждения (fallback)
- ❌ Ошибки (fallback)

## 🚀 Следующие шаги

1. Тестирование на реальных данных
2. Персистентное хранение snapshots (БД вместо файлов)
3. Time decay для решений
4. Экспорт Audit Trail для enterprise-клиентов
5. Интеграция с MCP для версионирования MCP-нод































