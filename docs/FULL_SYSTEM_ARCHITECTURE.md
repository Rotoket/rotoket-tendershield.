# Полная архитектура Tender Shield Pro
## Единый обзор всех архитектурных слоёв

**Версия:** 1.0  
**Дата:** 2025-01-XX  
**Статус:** АКТИВЕН

---

## 🎯 Миссия системы

**Tender Shield Pro — это decision system для директора,**  
**которая объясняет,**  
**можно ли принимать управленческое решение**  
**и почему.**

Система фиксирует управленческую реальность, а не анализирует или прогнозирует.

---

## 🧱 Каноническая цепочка шагов

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
ШАГ 7: Manifest Compliance Check (проверка соответствия)
  ↓
Frontend: DecisionPreviewStep5 + DecisionFreshnessGuard → UI
```

---

## 📦 Архитектурные слои

### ШАГ 3: Preprocessing & Evidence Layer

**Назначение:** Преобразование документов в проверяемые Evidence Objects.

**Принципы:**
- LLM НЕ извлекает таблицы, суммы, структуру
- Format-aware preprocessing обязателен
- MCP — только специализированные ноды
- Excel — источник истины (highest confidence)
- OCR — только с валидацией и confidence map

**Модули:**
- `backend/evidence_types.py` — типы Evidence Objects
- `backend/preprocessor.py` — ядро препроцессора
- `backend/evidence_adapter.py` — адаптер для LLM

**Документация:** `docs/step3_preprocessing_evidence_layer.md`

---

### ШАГ 4: Reasoning & Decision Layer

**Назначение:** Преобразование Evidence Objects в управленческие выводы.

**Принципы:**
- РЕШЕНИЕ ≠ СУММА РИСКОВ
- РЕШЕНИЕ = ЛОГИКА ПРОТИВОРЕЧИЙ И НАГРУЗКИ
- DEAL_BREAKER — жёсткие правила, нельзя понижать
- Противоречия — центральный механизм

**Модули:**
- `backend/reasoning_types.py` — типы Risk Signal, Decision Graph
- `backend/reasoning_layer.py` — ядро Reasoning Engine
  - `DealBreakerRules` — жёсткие правила классификации
  - `ContradictionDetector` — детектор противоречий
  - `ReasoningEngine` — основной движок

**Документация:** `docs/step4_reasoning_decision_layer.md`

---

### ШАГ 5: Decision Preview & Board-Ready Output

**Назначение:** Преобразование Decision Graph в управленческий вывод для директора.

**Принципы:**
- ДИРЕКТОР ЧИТАЕТ РЕШЕНИЕ, А НЕ ХОД МЫСЛЕЙ СИСТЕМЫ
- Управленческая ясность > полнота
- Язык и тон — деловой, нейтральный
- UI подчёркивает решение, не анализ

**Модули:**
- `backend/decision_preview_formatter.py` — форматирование Decision Preview
- `frontend/src/components/audit/DecisionPreviewStep5.tsx` — UI компонент

**Документация:** `docs/step5_decision_preview_board_ready.md`

---

### ШАГ 6: Audit Trail, Versioning & Decision Freshness

**Назначение:** Обеспечение воспроизводимости и контроля актуальности решений.

**Принципы:**
- РЕШЕНИЕ БЕЗ ИСТОРИИ = НЕДЕЙСТВИТЕЛЬНОЕ РЕШЕНИЕ
- Versioning — жёсткое правило: любое изменение = новая версия
- Decision Freshness Guard — статусы ACTUAL/STALE/INVALIDATED
- Audit Trail скрыт по умолчанию, доступен по запросу

**Модули:**
- `backend/audit_trail_types.py` — типы snapshots
- `backend/audit_trail_manager.py` — менеджер Audit Trail
- `frontend/src/components/audit/DecisionFreshnessGuard.tsx` — UI компонент

**Документация:** `docs/step6_audit_trail_versioning.md`

---

### ШАГ 7: Architecture Manifest & Anti-Regression Guardrails

**Назначение:** Высший архитектурный контракт и защита от деградации.

**Принципы:**
- DEAL_BREAKER — абсолютный приоритет
- Особое мнение эксперта — отдельный слой
- Решение "НЕ УЧАСТВОВАТЬ" — стратегическая память (Reason Codes)
- Границы ответственности — система не утверждает безопасность/выгоду
- Анти-регрессионные правила — запрет упрощений

**Модули:**
- `docs/ARCHITECTURE_MANIFEST.md` — высший контракт
- `backend/decision_reason_codes.py` — Reason Codes для отказов
- `backend/manifest_compliance_checker.py` — автоматическая проверка

**Документация:** `docs/step7_architecture_manifest.md`

---

## 🔄 Полный поток данных

### Backend (`backend/main.py`)

1. **Загрузка файла** → Document Snapshot (ШАГ 6)
2. **Препроцессинг** → Evidence Objects (ШАГ 3)
3. **Evidence Snapshot** → Фиксация Evidence (ШАГ 6)
4. **Reasoning** → Risk Signals, Decision Preview (ШАГ 4)
5. **Decision Snapshot** → Фиксация решения (ШАГ 6)
6. **Reason Codes** → Извлечение для отказов (ШАГ 7)
7. **Manifest Check** → Проверка соответствия (ШАГ 7)
8. **Decision Preview Formatting** → Board-ready формат (ШАГ 5)

### Frontend

1. **DecisionPreview** → Проверяет наличие Step5 preview
2. **DecisionPreviewStep5** → Отображает управленческий вывод
3. **DecisionFreshnessGuard** → Показывает предупреждение для устаревших решений
4. **Audit Trail** → Скрыт, доступен по запросу

---

## ✅ Проверка соответствия Manifest

### DEAL_BREAKER — абсолютный приоритет
- ✅ Реализовано в `DealBreakerRules` (жёсткие правила)
- ✅ Проверяется в `ManifestComplianceChecker`
- ✅ UI визуально выделяет DEAL_BREAKER

### Особое мнение эксперта
- ✅ Реализовано как отдельный слой (`ExpertOpinion`)
- ✅ Не влияет на ИУН и Decision
- ✅ Сохраняется в Audit Trail

### Решение "НЕ УЧАСТВОВАТЬ" — стратегическая память
- ✅ Reason Codes извлекаются автоматически
- ✅ Сохраняются в Decision Snapshot
- ⏳ Агрегация статистики (в разработке)

### Границы ответственности
- ✅ Язык решения проверяется в `ManifestComplianceChecker`
- ✅ Запрещённые формулировки блокируются

---

## 🚫 Анти-регрессионные правила

**Запрещено навсегда:**
- ❌ перенос логики в LLM «для удобства»
- ❌ автосмягчение формулировок
- ❌ скрытие сложности ради UX
- ❌ метрики без объяснения
- ❌ «временно упростить»

**Проверка:** `ManifestComplianceChecker` автоматически проверяет соответствие.

---

## 📊 Статус реализации

### ✅ Реализовано:
- [x] ШАГ 3: Evidence Layer
- [x] ШАГ 4: Reasoning Layer
- [x] ШАГ 5: Decision Preview Formatter
- [x] ШАГ 6: Audit Trail & Versioning
- [x] ШАГ 7: Architecture Manifest
- [x] Интеграция всех шагов в единый пайплайн
- [x] UI компоненты для всех слоёв

### ⏳ В разработке:
- [ ] Расширенная MCP-интеграция для ШАГА 3
- [ ] Агрегация статистики отказов (Reason Codes)
- [ ] Персистентное хранение snapshots (БД)
- [ ] Time decay для решений
- [ ] Экспорт Audit Trail для enterprise

---

## 🔒 Статус Architecture Manifest

**Этот Manifest:**
- обязателен для Cursor
- обязателен для MCP
- обязателен для backend и UI
- обязателен для онбординга
- обязателен для enterprise-контрактов

**Любое отклонение = осознанный архитектурный форк.**

---

## 🧠 Финальный смысл

**Tender Shield Pro —**  
**это не система анализа,**  
**а система управленческой честности.**

---

**Документация по шагам:**
- `docs/step3_preprocessing_evidence_layer.md`
- `docs/step4_reasoning_decision_layer.md`
- `docs/step5_decision_preview_board_ready.md`
- `docs/step6_audit_trail_versioning.md`
- `docs/step7_architecture_manifest.md`
- `docs/ARCHITECTURE_MANIFEST.md` (высший контракт)
- `docs/integration_all_steps.md` (интеграция)































