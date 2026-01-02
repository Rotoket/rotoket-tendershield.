# Архитектура Tender Shield Pro — Обзор

**Полная архитектурная документация системы Tender Shield Pro**

---

## 📚 Структура документации

### Основные документы:

1. **[Architecture Manifest](./ARCHITECTURE_MANIFEST.md)** — высший архитектурный контракт
2. **[ШАГ 9: Reference Implementation Map](./step9_reference_implementation_map.md)** — каноническая карта реализации

### Документация по шагам:

3. **[ШАГ 3: Preprocessing & Evidence Layer](./step3_preprocessing_evidence_layer.md)** — извлечение фактов
4. **[ШАГ 4: Reasoning & Decision Layer](./step4_reasoning_decision_layer.md)** — формирование решений
5. **[ШАГ 5: Decision Preview & Board-Ready Output](./step5_decision_preview_board_ready.md)** — форматирование вывода
6. **[ШАГ 6: Audit Trail, Versioning & Decision Freshness](./step6_audit_trail_versioning.md)** — версионирование и аудит
7. **[ШАГ 7: Architecture Manifest & Anti-Regression Guardrails](./ARCHITECTURE_MANIFEST.md)** — защита от регрессии
8. **[ШАГ 8: Packaging, Positioning & External Contract](./step8_packaging_positioning_manifest.md)** — позиционирование

### Интеграция:

9. **[Интеграция всех шагов](./integration_all_steps.md)** — как шаги работают вместе

---

## 🧱 Каноническая слоёная архитектура

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
│            MCP Extraction Layer (ШАГ 3)                      │
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

## 🔑 Ключевые принципы

### 1. Разделение ответственности

Каждый слой имеет чётко определённую ответственность:
- **MCP Extraction Layer** — извлечение фактов
- **Evidence Layer** — нормализация данных
- **Decision Logic Layer** — формирование решений
- **Decision Presentation Layer** — форматирование вывода
- **UI Layer** — отображение решения

### 2. Запрет на нарушение границ

❌ Запрещено:
- пропускать слои
- обращаться «напрямую вниз»
- смешивать логику между слоями

### 3. Immutability и Versioning

- Все snapshots неизменяемы
- Любые изменения = новая версия
- Append-only Audit Trail

### 4. DEAL_BREAKER — абсолютный приоритет

- Один DEAL_BREAKER важнее всех плюсов
- Не компенсируется
- Не смягчается

---

## 📦 Основные компоненты

### Backend

- `backend/main.py` — главный FastAPI endpoint
- `backend/preprocessor.py` — Evidence Layer
- `backend/reasoning_layer.py` — Decision Logic Layer
- `backend/decision_preview_formatter.py` — Decision Presentation Layer
- `backend/audit_trail_manager.py` — Audit & Versioning Layer
- `backend/positioning_manifest.py` — Positioning Manifest (ШАГ 8)
- `backend/architecture_compliance_checker.py` — проверка соответствия (ШАГ 9)

### Frontend

- `frontend/src/components/audit/DecisionPreviewStep5.tsx` — главный компонент решения
- `frontend/src/components/audit/DecisionFreshnessGuard.tsx` — предупреждение об устаревании
- `frontend/src/components/decision/DecisionBlock.tsx` — блок фиксации решения

---

## ✅ Критерий целостности системы

Если:
- сменить модель
- сменить команду
- сменить UI
- пересчитать через год

➡️ **Решение, его причины и ограничения остаются теми же.**

Если нет — система сломана.

---

## 🔒 Статус документации

- ✅ обязательна для Cursor
- ✅ обязательна для code review
- ✅ обязательна для онбординга
- ✅ обязательна для CI (архитектурные чеки)

---

## 🧠 Философия системы

**Tender Shield Pro — это не система анализа, а система управленческой честности.**

Система:
- не оптимизирует
- не прогнозирует
- не убеждает
- не «помогает подумать»

Она **фиксирует управленческую реальность**.































