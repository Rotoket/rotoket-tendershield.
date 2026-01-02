---
doc_type: "canon"
tags: ["severity", "шкала", "серьезность", "канон"]
title: "Шкала серьезности рисков"
---

# 📊 ШКАЛА СЕРЬЕЗНОСТИ РИСКОВ

**Каноническая шкала оценки серьезности рисков для анализа закупок**

---

## 🎯 УРОВНИ СЕРЬЕЗНОСТИ

### CRITICAL (Критичный)

**Описание:**
- Блокирует участие в закупке
- Не может быть проигнорирован
- Требует немедленного внимания

**Примеры:**
- ЗАТО без пропуска (не митигируемо)
- Отсутствие обязательного сертификата (не митигируемо)
- Невозможная доставка (не митигируемо)
- Нарушение закона (не митигируемо)

**Классификация:** DEALBREAKER  
**Decision Impact:** DO_NOT_PARTICIPATE (если не митигируемо)

---

### HIGH (Высокий)

**Описание:**
- Значительно влияет на решение
- Требует внимания
- Можно митигировать, но с затратами

**Примеры:**
- ЗАТО с возможностью получения пропуска
- Отсутствие сертификата (можно получить)
- Сложная логистика (можно организовать)
- Высокие штрафы (можно контролировать)

**Классификация:** DEALBREAKER (митигируемый) или CONTROLLED RISK  
**Decision Impact:** PROCEED_WITH_CONDITIONS

---

### MEDIUM (Средний)

**Описание:**
- Влияет на решение, но не критично
- Можно митигировать
- Требует контроля

**Примеры:**
- Короткие сроки подачи заявок
- Частичное соответствие сертификатам
- Сложная логистика (управляемая)
- Неясные требования

**Классификация:** CONTROLLED RISK  
**Decision Impact:** PROCEED_WITH_CONDITIONS или PROCEED

---

### LOW (Низкий)

**Описание:**
- Минимальное влияние на решение
- Можно игнорировать
- Не требует специального внимания

**Примеры:**
- Дублирующие требования
- Неясная спецификация (не критично)
- Стандартная процедура

**Классификация:** MARKET NOISE  
**Decision Impact:** PROCEED (не влияет)

---

## 📊 МАТРИЦА СЕРЬЕЗНОСТИ

| Severity | Classification | SubClassification | Decision Impact | Финансовое влияние |
|----------|----------------|-------------------|-----------------|-------------------|
| CRITICAL | DEALBREAKER | LOCATION_BLOCKER (не митигируемо) | DO_NOT_PARTICIPATE | 0 |
| CRITICAL | DEALBREAKER | CERTIFICATION_MISSING (не митигируемо) | DO_NOT_PARTICIPATE | 0 |
| CRITICAL | DEALBREAKER | EXPERIENCE_INSUFFICIENT | DO_NOT_PARTICIPATE | 0 |
| CRITICAL | DEALBREAKER | LOGISTICS_IMPOSSIBLE (не митигируемо) | DO_NOT_PARTICIPATE | 0 |
| CRITICAL | DEALBREAKER | LEGAL_PROHIBITION | DO_NOT_PARTICIPATE | 0 |
| HIGH | DEALBREAKER | LOCATION_BLOCKER (митигируемо) | PROCEED_WITH_CONDITIONS | -50K до -100K |
| HIGH | DEALBREAKER | CERTIFICATION_MISSING (митигируемо) | PROCEED_WITH_CONDITIONS | -50K до -200K |
| HIGH | CONTROLLED RISK | PENALTY_RISK | PROCEED_WITH_CONDITIONS | -500K (при нарушении) |
| HIGH | CONTROLLED RISK | LOGISTICS_COMPLEX | PROCEED_WITH_CONDITIONS | -50K до -500K |
| MEDIUM | CONTROLLED RISK | DEADLINE_TIGHT | PROCEED_WITH_CONDITIONS | 0 до -50K |
| MEDIUM | CONTROLLED RISK | PARTIAL_CERTIFICATION | PROCEED_WITH_CONDITIONS | -50K до -200K |
| LOW | MARKET NOISE | REDUNDANT_REQUIREMENT | PROCEED | 0 |

---

## 🔢 ВЛИЯНИЕ НА ИУН

**Формула влияния severity на ИУН:**
```
ИУН += Severity Weight

где:
- CRITICAL: +30 (для не митигируемых DEALBREAKER)
- CRITICAL: +20 (для митигируемых DEALBREAKER)
- HIGH: +15 (для CONTROLLED RISK)
- MEDIUM: +10 (для CONTROLLED RISK)
- LOW: +0 (для MARKET NOISE)
```

**Пример:**
- Базовый риск: 10
- CRITICAL DEALBREAKER (митигируемый): +20
- HIGH CONTROLLED RISK: +15
- MEDIUM CONTROLLED RISK: +10
- **ИУН:** 10 + 20 + 15 + 10 = 55

---

## ✅ ИСПОЛЬЗОВАНИЕ В СИСТЕМЕ

**При анализе контракта:**
- Система определяет severity каждого риска
- Классифицирует риски по severity
- Рассчитывает влияние на ИУН
- Принимает решение на основе severity

**В Decision Preview:**
- CRITICAL риски отображаются красным
- HIGH риски отображаются оранжевым
- MEDIUM риски отображаются желтым
- LOW риски не отображаются (или серым)

---

**Использование в системе:**
- ProcurementReasoningEngine использует эту шкалу для оценки рисков
- Decision Preview отображает риски в соответствии с severity
- RiskNarrative использует для сторителлинга рисков


