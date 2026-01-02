---
doc_type: "example"
tags: ["примеры", "матрицы", "решения", "фреймворки"]
title: "Матрицы принятия решений"
---

# 📊 МАТРИЦЫ ПРИНЯТИЯ РЕШЕНИЙ

**Примеры матриц для принятия решений об участии в закупках**

---

## 🎯 МАТРИЦА 1: DEALBREAKER → Decision

| DEALBREAKER | Митигируемо? | Сроки митигации | Стоимость митигации | Decision |
|-------------|--------------|-----------------|---------------------|----------|
| LOCATION_BLOCKER (ЗАТО) | Да | 2-4 недели | 50K-100K руб. | PROCEED_WITH_CONDITIONS |
| LOCATION_BLOCKER (ЗАТО) | Нет | Невозможно | - | DO_NOT_PARTICIPATE |
| CERTIFICATION_MISSING | Да | 2-4 недели | 50K-200K руб. | PROCEED_WITH_CONDITIONS |
| CERTIFICATION_MISSING | Нет | > 4 недель | - | DO_NOT_PARTICIPATE |
| EXPERIENCE_INSUFFICIENT | Нет | Невозможно | - | DO_NOT_PARTICIPATE |
| LOGISTICS_IMPOSSIBLE | Да | 1-2 недели | 100K-1M руб. | PROCEED_WITH_CONDITIONS |
| LOGISTICS_IMPOSSIBLE | Нет | Невозможно | - | DO_NOT_PARTICIPATE |
| LEGAL_PROHIBITION | Нет | Невозможно | - | DO_NOT_PARTICIPATE |

---

## 🎯 МАТРИЦА 2: CONTROLLED RISK → Decision

| CONTROLLED RISK | Количество | Финансовое влияние | Decision |
|-----------------|------------|-------------------|----------|
| DEADLINE_TIGHT | 1-2 | Низкое | PROCEED |
| DEADLINE_TIGHT | 3+ | Среднее | PROCEED_WITH_CONDITIONS |
| PENALTY_RISK | 1 | Высокое (штраф 10%) | PROCEED_WITH_CONDITIONS |
| PENALTY_RISK | 2+ | Критичное | POSTPONE |
| LOGISTICS_COMPLEX | 1 | Среднее | PROCEED_WITH_CONDITIONS |
| LOGISTICS_COMPLEX | 2+ | Высокое | POSTPONE |
| PARTIAL_CERTIFICATION | 1 | Среднее | PROCEED_WITH_CONDITIONS |
| PARTIAL_CERTIFICATION | 2+ | Высокое | POSTPONE |

---

## 🎯 МАТРИЦА 3: Financial Impact → Decision

| Best Case | Worst Case | Expected Value | Вероятность Worst Case | Decision |
|-----------|------------|----------------|------------------------|----------|
| > 20% маржи | > 0 | > 0 | < 30% | PROCEED |
| > 20% маржи | > 0 | > 0 | 30-50% | PROCEED_WITH_CONDITIONS |
| > 20% маржи | < 0 | > 0 | > 50% | POSTPONE |
| > 20% маржи | < 0 | < 0 | Любая | DO_NOT_PARTICIPATE |
| < 20% маржи | > 0 | > 0 | < 30% | PROCEED_WITH_CONDITIONS |
| < 20% маржи | > 0 | > 0 | 30-50% | POSTPONE |
| < 20% маржи | < 0 | Любая | Любая | DO_NOT_PARTICIPATE |

---

## 🎯 МАТРИЦА 4: ИУН → Decision

| ИУН | Интерпретация | Decision |
|-----|---------------|----------|
| 0-30 | Рутинно / делегируемо | PROCEED |
| 31-50 | Требует контроля | PROCEED_WITH_CONDITIONS |
| 51-70 | Только при личном внимании директора | PROCEED_WITH_CONDITIONS |
| 71-100 | Неделегируемо / высокая управленческая нагрузка | POSTPONE или DO_NOT_PARTICIPATE |

---

## 🎯 МАТРИЦА 5: Комплексная (DEALBREAKER + RISK + Financial)

| DEALBREAKER | CONTROLLED RISK | Best Case | Worst Case | Decision |
|-------------|-----------------|-----------|------------|----------|
| Нет | 0-2 | > 20% маржи | > 0 | PROCEED |
| Нет | 3-5 | > 20% маржи | > 0 | PROCEED_WITH_CONDITIONS |
| Нет | 6+ | > 20% маржи | > 0 | POSTPONE |
| Митигируемый | 0-2 | > 20% маржи | > 0 | PROCEED_WITH_CONDITIONS |
| Митигируемый | 3-5 | > 20% маржи | > 0 | PROCEED_WITH_CONDITIONS |
| Митигируемый | 6+ | > 20% маржи | > 0 | POSTPONE |
| Не митигируемый | Любое | Любое | Любое | DO_NOT_PARTICIPATE |

---

## ✅ ИСПОЛЬЗОВАНИЕ В СИСТЕМЕ

**При анализе контракта:**
- Система использует эти матрицы для принятия решений
- ProcurementReasoningEngine применяет матрицы автоматически
- Decision Preview отображает решение на основе матриц

**В Decision Preview:**
- Матрицы используются для обоснования решения
- Показывается какая матрица применена
- Отображаются все факторы влияющие на решение

---

**Использование в системе:**
- ProcurementReasoningEngine использует эти матрицы
- Decision Preview ссылается на матрицы
- Audit Trail логирует использование матриц


