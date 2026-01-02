---
doc_type: "canon"
tags: ["evidence", "классификация", "канон", "риски"]
title: "Классификация evidence в контексте закупок"
---

# 📊 КЛАССИФИКАЦИЯ EVIDENCE

**Каноническая система классификации evidence для анализа закупок 44-ФЗ и 223-ФЗ**

---

## 🎯 ОСНОВНЫЕ КЛАССИФИКАЦИИ

### 1. EvidenceClassification (базовая)

**DEALBREAKER:**
- Критичный стоп-фактор
- Блокирует участие в закупке
- Не может быть проигнорирован

**CONTROLLED RISK:**
- Управляемый риск
- Можно митигировать
- Требует внимания, но не блокирует участие

**MARKET NOISE:**
- Рыночный шум
- Не влияет на решение
- Можно игнорировать

---

## 🔍 ПОДКЛАССИФИКАЦИИ (EvidenceSubClassification)

### DEALBREAKER subcategories

**LOCATION_BLOCKER:**
- ЗАТО, спецрежим
- Нет доступа в город
- **Mitigation:** Получить пропуск (2-4 недели, 50K-100K руб.)

**CERTIFICATION_MISSING:**
- Критичный сертификат отсутствует
- ТР ЕАЭС, СанПиН, лицензии
- **Mitigation:** Получить сертификат (2-4 недели, 50K-200K руб.)

**EXPERIENCE_INSUFFICIENT:**
- Опыт < 20% от цены контракта
- Нет опыта в нужной сфере
- **Mitigation:** Не митигируемо (опыт нельзя "купить")

**LOGISTICS_IMPOSSIBLE:**
- Нельзя доставить товар
- Невозможно обеспечить условия транспортировки
- **Mitigation:** Организовать логистику (1-2 недели, 100K-1M руб.)

**LEGAL_PROHIBITION:**
- Прямое нарушение закона
- Нарушение 44-ФЗ, 223-ФЗ, 135-ФЗ
- **Mitigation:** Не митигируемо (нарушение закона нельзя исправить)

---

### CONTROLLED RISK subcategories

**DEADLINE_TIGHT:**
- Короткий срок подачи заявок
- Недостаточно времени на подготовку
- **Mitigation:** Организовать быструю подготовку

**PRICE_BELOW_MARKET:**
- Цена подозрительно низкая
- Нет маржи
- **Mitigation:** Пересмотреть цену или отказаться

**VENDOR_NEW:**
- Новый поставщик без истории
- Нет опыта работы с заказчиком
- **Mitigation:** Получить рекомендации, начать с малых контрактов

**COMPLEX_REQUIREMENTS:**
- Сложные требования
- Высокий риск ошибок
- **Mitigation:** Детальная проработка требований

**PARTIAL_CERTIFICATION:**
- Часть сертификатов есть
- Не все сертификаты получены
- **Mitigation:** Получить недостающие сертификаты

**PENALTY_RISK:**
- Риск штрафов (10% от цены)
- Высокий риск нарушения сроков
- **Mitigation:** Строгий контроль сроков

**QUALITY_VARIANCE:**
- Вариативность качества
- Высокий риск споров при приемке
- **Mitigation:** Детальная проработка требований к качеству

**LOGISTICS_COMPLEX:**
- Сложная логистика
- Высокие затраты на доставку
- **Mitigation:** Организовать эффективную логистику

---

### MARKET NOISE subcategories

**REDUNDANT_REQUIREMENT:**
- Требование дублирует норму
- Не влияет на решение
- **Mitigation:** Не требуется

**VAGUE_SPECIFICATION:**
- Неясная спецификация
- Не влияет на решение
- **Mitigation:** Не требуется

**STANDARD_PROCEDURE:**
- Стандартная процедура
- Не влияет на решение
- **Mitigation:** Не требуется

---

## 📚 ПРАВОВЫЕ ОСНОВАНИЯ (EvidenceLegalBasis)

**FZ_44:**
- Федеральный закон 44-ФЗ
- Применимо к государственным и муниципальным закупкам

**FZ_223:**
- Федеральный закон 223-ФЗ
- Применимо к закупкам отдельными видами юридических лиц

**TR_EAES_040:**
- ТР ЕАЭС 040/2016
- Применимо к рыбной продукции

**SANPIN:**
- СанПиН 2.3/2.4.3590-20
- Применимо к пищевым продуктам в детских учреждениях

**GOST:**
- ГОСТ стандарты
- Применимо если указан в контракте

**CUSTOM:**
- Специфичное требование заказчика
- Применимо к конкретному заказчику

---

## 🔢 РАСЧЕТ ВЛИЯНИЯ НА РЕШЕНИЕ

**Для DEALBREAKER:**
- Если не митигируемо → `DO_NOT_PARTICIPATE`
- Если митигируемо → `PROCEED_WITH_CONDITIONS` (с условием митигации)

**Для CONTROLLED RISK:**
- Влияет на ИУН (Индекс управленческой нагрузки)
- Влияет на Financial Impact
- Может изменить решение на `PROCEED_WITH_CONDITIONS`

**Для MARKET NOISE:**
- Не влияет на решение
- Не влияет на ИУН
- Не влияет на Financial Impact

---

## 📊 МАТРИЦА КЛАССИФИКАЦИИ

| Evidence | Classification | SubClassification | Legal Basis | Decision Impact |
|----------|----------------|-------------------|-------------|-----------------|
| ЗАТО без пропуска | DEALBREAKER | LOCATION_BLOCKER | FZ_44, FZ_223 | DO_NOT или PROCEED_WITH_CONDITIONS |
| Нет ТР ЕАЭС сертификата | DEALBREAKER | CERTIFICATION_MISSING | TR_EAES_040 | DO_NOT или PROCEED_WITH_CONDITIONS |
| Опыт < 20% | DEALBREAKER | EXPERIENCE_INSUFFICIENT | FZ_44 | DO_NOT |
| Невозможная доставка | DEALBREAKER | LOGISTICS_IMPOSSIBLE | FZ_44, FZ_223 | DO_NOT или PROCEED_WITH_CONDITIONS |
| Нарушение 44-ФЗ | DEALBREAKER | LEGAL_PROHIBITION | FZ_44 | DO_NOT |
| Короткие сроки | CONTROLLED RISK | DEADLINE_TIGHT | FZ_44, FZ_223 | PROCEED_WITH_CONDITIONS |
| Высокие штрафы | CONTROLLED RISK | PENALTY_RISK | FZ_44, FZ_223 | PROCEED_WITH_CONDITIONS |
| Сложная логистика | CONTROLLED RISK | LOGISTICS_COMPLEX | FZ_44, FZ_223 | PROCEED_WITH_CONDITIONS |
| Дублирующее требование | MARKET NOISE | REDUNDANT_REQUIREMENT | CUSTOM | PROCEED |

---

## ✅ ИСПОЛЬЗОВАНИЕ В СИСТЕМЕ

**При анализе контракта:**
- Система классифицирует каждое evidence
- Определяет sub_classification
- Определяет legal_basis
- Рассчитывает влияние на решение
- Предлагает mitigation strategies

**В Decision Preview:**
- DEALBREAKER отображаются красным
- CONTROLLED RISK отображаются желтым
- MARKET NOISE не отображаются (или серым)

**В Financial Impact:**
- DEALBREAKER влияют на worst case (стоимость митигации)
- CONTROLLED RISK влияют на expected value
- MARKET NOISE не влияют

---

**Использование в системе:**
- При анализе контракта система использует эту классификацию
- ProcurementReasoningEngine использует для принятия решений
- Decision Preview отображает в соответствии с классификацией


