# SYSTEM: FULL PRODUCT REALITY CHECK (PRE-10.2)

**Дата проверки:** 16.12.2025  
**Метод:** Фактический аудит кода, не описания

---

## 1. TOP-LEVEL SCREENS/ROUTES

**Источник:** `App.tsx` (строки 132-181), `AppView` enum из `types.ts`

### 1.1. ANALYZER (AppView.ANALYZER)
- **Компонент:** `TenderAnalysis` с `mode='single'` → рендерит `Analyzer.tsx`
- **Ответственность:** Анализ одного документа тендера с фиксацией решения
- **Участие в Decision Flow:** ✅ **YES** — содержит `DecisionBlock` (строка 706), фиксирует `userDecision`
- **Использование без Decision:** ⚠️ **PARTIAL** — анализ можно провести, но отчёты/экспорты заблокированы (`disabled={!result.userDecision}`)

### 1.2. AUDIT (AppView.AUDIT)
- **Компонент:** `TenderAnalysis` с `mode='package'` → рендерит `ComplexAudit.tsx`
- **Ответственность:** Комплексный анализ пакета документов с фиксацией решения
- **Участие в Decision Flow:** ✅ **YES** — содержит `DecisionBlock` (строка 563), фиксирует `userDecision`
- **Использование без Decision:** ⚠️ **PARTIAL** — анализ можно провести, но отчёты/экспорты заблокированы (`disabled={!result.userDecision}`)

### 1.3. GENERATOR (AppView.GENERATOR)
- **Компонент:** `DocumentGenerator.tsx`
- **Ответственность:** Генерация протоколов разногласий и жалоб
- **Участие в Decision Flow:** ⚠️ **INDIRECT** — получает `decision` из пропса или `localStorage` (строка 42-50), но не требует его для работы
- **Использование без Decision:** ✅ **YES** — компонент работает без обязательного решения, использует `isActionAllowed(decision, action)` для блокировки действий (строка 5)

### 1.4. CALCULATOR (AppView.CALCULATOR)
- **Компонент:** `Calculator.tsx`
- **Ответственность:** Расчёт маржинальности участия в тендере
- **Участие в Decision Flow:** ⚠️ **INDIRECT** — получает `decision` из пропса или `localStorage` (строка 23-31), использует `isActionAllowed` для блокировки (строка 5)
- **Использование без Decision:** ✅ **YES** — калькулятор работает без обязательного решения

### 1.5. HISTORY (AppView.HISTORY)
- **Компонент:** `HistoryView.tsx`
- **Ответственность:** Журнал завершённых анализов с решениями
- **Участие в Decision Flow:** ✅ **YES** — отображает `user_decision` для каждого элемента, генерирует отчёты только при наличии решения
- **Использование без Decision:** ✅ **YES** — можно просматривать историю, но отчёты требуют `item.user_decision` (строка 516, 574)

### 1.6. KNOWLEDGE (AppView.KNOWLEDGE)
- **Компонент:** `KnowledgeView.tsx`
- **Ответственность:** Поиск по базе знаний (нормы, законы)
- **Участие в Decision Flow:** ❌ **NO** — не связан с Decision Layer
- **Использование без Decision:** ✅ **YES** — полностью независимый экран

### 1.7. PROFILE (AppView.PROFILE)
- **Компонент:** `Profile.tsx`
- **Ответственность:** Управление профилем пользователя, тарифами, платежами
- **Участие в Decision Flow:** ❌ **NO** — не связан с Decision Layer
- **Использование без Decision:** ✅ **YES** — полностью независимый экран

### 1.8. ANALYTICS (AppView.ANALYTICS)
- **Компонент:** `Analytics.tsx`
- **Ответственность:** Аналитика по решениям (Decision KPI) и общая статистика
- **Участие в Decision Flow:** ⚠️ **READ-ONLY** — показывает KPI на основе решений из истории, но не требует решения для просмотра
- **Использование без Decision:** ✅ **YES** — можно просматривать аналитику без решения (показывает "Недостаточно данных" если решений нет)

### 1.9. HELP (AppView.HELP)
- **Компонент:** `HelpGuide.tsx`
- **Ответственность:** Справочный центр
- **Участие в Decision Flow:** ❌ **NO** — не связан с Decision Layer
- **Использование без Decision:** ✅ **YES** — полностью независимый экран

---

## 2. DECISION-RELATED COMPONENTS

### 2.1. DecisionBlock
**Файл:** `frontend/src/components/decision/DecisionBlock.tsx`

**Использование:**
- ✅ `Analyzer.tsx` (строка 706) — только в Director Mode
- ✅ `ComplexAudit.tsx` (строка 563) — только в Director Mode

**Поведение:**
- Фиксирует решение через `onDecision` callback
- Блокирует повторный выбор после фиксации (строка 82-84)
- Требует комментарий для `do_not_participate` и `participate_with_conditions` (строка 87-93)
- Требует подтверждение для `participate` при наличии deal breakers (строка 96-103)

### 2.2. userDecision Storage
**Места хранения:**
1. **В состоянии компонента:** `result.userDecision` в `Analyzer.tsx` и `ComplexAudit.tsx`
2. **localStorage:** `last_user_decision` (строка 729 в `Analyzer.tsx`, строка 588 в `ComplexAudit.tsx`)
3. **App.tsx state:** `currentDecision` (строка 34) — **НО НЕ ИСПОЛЬЗУЕТСЯ** (см. раздел 5)

**Поток данных:**
```
DecisionBlock.onDecision
  → setResult({ ...result, userDecision })
  → localStorage.setItem('last_user_decision', JSON.stringify(userDecision))
  → onDecisionChange?.(userDecision) [если есть callback]
```

### 2.3. Decision → History Flow
**Источник:** `HistoryView.tsx`

- История загружается через `fetchAuditHistory` (строка 98)
- Каждый элемент истории содержит `user_decision?: UserDecision`
- Отображение через `DecisionBadge` компонент (строка 415-420, 471-476)
- **Проблема:** История может содержать элементы без решения (старые анализы)

### 2.4. Decision → Reports Flow
**Источник:** `Analyzer.tsx`, `ComplexAudit.tsx`, `HistoryView.tsx`

**Board Pack:**
- `Analyzer.tsx` (строка 960-1009) — только если `result.userDecision` существует
- `HistoryView.tsx` (строка 436-507) — только если `item.user_decision` существует

**Compliance Export:**
- `Analyzer.tsx` (строка 1011-1065) — `disabled={!result.userDecision || !can(role, 'generate_compliance_export')}`
- `HistoryView.tsx` (строка 513-577) — `disabled={!item.user_decision || !can(role, 'generate_compliance_export')}`

**Excel Export:**
- `Analyzer.tsx` (строка 853) — `disabled={!result.userDecision}`

---

## 3. REPORTS/EXPORTS WITHOUT DECISION

### 3.1. ✅ ЗАЩИЩЕНО (требуют Decision)

**Analyzer.tsx:**
- Excel export (строка 853): `disabled={!result.userDecision}`
- Board Pack (строка 960): рендерится только если `result.userDecision` существует
- Compliance Export (строка 1013): `disabled={!result.userDecision || !can(role, 'generate_compliance_export')}`

**ComplexAudit.tsx:**
- Отчёт (строка 1062): `disabled={!result.userDecision}`
- Генератор документов (строка 1043): `disabled={!result.userDecision}`

**HistoryView.tsx:**
- Board Pack (строка 436): проверка `item.user_decision` перед генерацией
- Compliance Export (строка 516): `disabled={!item.user_decision || !can(role, 'generate_compliance_export')}`

### 3.2. ⚠️ ПОТЕНЦИАЛЬНЫЕ ПРОБЛЕМЫ

**DocumentGenerator.tsx:**
- Компонент получает `decision` из пропса или `localStorage`, но **не требует его для работы**
- Использует `isActionAllowed(decision, action)` для блокировки действий (строка 5), но если `decision` отсутствует, действия могут быть заблокированы, но компонент всё равно доступен

**Calculator.tsx:**
- Компонент получает `decision` из пропса или `localStorage`, но **не требует его для работы**
- Использует `isActionAllowed(decision, action)` для блокировки действий, но сам расчёт доступен без решения

**HistoryView.tsx:**
- История может содержать элементы **без решения** (старые анализы)
- Для таких элементов отчёты недоступны, но сам просмотр истории возможен

---

## 4. UNUSED/DUPLICATED/LEGACY COMPONENTS

### 4.1. Неиспользуемые компоненты (не импортируются нигде)

**Проверено через `grep` по импортам:**
- ❌ `TenderAnalysisView.tsx` — не импортируется
- ❌ `TenderList.tsx` — не импортируется
- ❌ `TenderDetail.tsx` — не импортируется
- ❌ `PackageHubDashboard.tsx` — не импортируется (используется `TenderHubDashboard.tsx`)
- ❌ `LegalControl.tsx` — не импортируется (возможно, legacy Audit Trail viewer)

### 4.2. Дублированные компоненты

**Dashboard.tsx vs Analytics.tsx:**
- Оба показывают Decision KPI
- `Dashboard.tsx` — компактный вид (строка 10-45)
- `Analytics.tsx` — расширенная аналитика (строка 24-522)
- **Проблема:** `Dashboard.tsx` не используется в `App.tsx` (нет роута)

### 4.3. Legacy/неиспользуемый код

**App.tsx:**
- `currentDecision` state (строка 34) — **объявлен, но не обновляется**
- `setCurrentDecision` — **никогда не вызывается**
- `decision={currentDecision}` передаётся в `DocumentGenerator` и `Calculator` (строки 152, 154), но всегда `undefined`

**TenderAnalysis.tsx:**
- `onDecisionChange` prop (строка 38) — **объявлен, но не используется**
- В `TenderAnalysis.tsx` нет вызова `onDecisionChange` при изменении решения

---

## 5. VIOLATIONS / WEAK SPOTS

### 5.1. ❌ КРИТИЧЕСКОЕ: Decision не передаётся из Analyzer/ComplexAudit в App.tsx

**Проблема:**
- `Analyzer.tsx` и `ComplexAudit.tsx` имеют `onDecisionChange` callback (строки 133, 59)
- `TenderAnalysis.tsx` принимает `onDecisionChange` (строка 38), но **не передаёт его в Analyzer/ComplexAudit**
- `App.tsx` не передаёт `onDecisionChange` в `TenderAnalysis` (строки 136-149)
- Результат: `currentDecision` в `App.tsx` всегда `undefined`, `DocumentGenerator` и `Calculator` получают решение только из `localStorage`

**Канонический поток нарушен:**
```
Analyzer → Decision → App.tsx → DocumentGenerator/Calculator
```
**Реальный поток:**
```
Analyzer → localStorage → DocumentGenerator/Calculator (через чтение localStorage)
```

### 5.2. ⚠️ СРЕДНЕЕ: DocumentGenerator и Calculator не требуют Decision

**Проблема:**
- Компоненты работают без обязательного решения
- Используют `isActionAllowed` для блокировки действий, но сам компонент доступен
- **Канон:** "Любой отчёт, экспорт, Board Pack, KPI: ❌ запрещён без зафиксированного решения"

**Текущее состояние:**
- Компоненты доступны, но действия внутри могут быть заблокированы
- Это соответствует канону частично (действия заблокированы), но не полностью (компонент доступен)

### 5.3. ⚠️ СРЕДНЕЕ: История может содержать элементы без решения

**Проблема:**
- Старые анализы могут не иметь `user_decision`
- История отображает такие элементы с текстом "Решение не зафиксировано"
- Отчёты для таких элементов недоступны (правильно)
- **Канон:** "Анализ без решения = незавершённый объект"

**Текущее состояние:**
- История показывает незавершённые анализы, что может быть полезно для аудита
- Но это нарушает канон "анализ считается завершённым только после фиксации решения"

### 5.4. ⚠️ НИЗКОЕ: Dashboard.tsx не используется

**Проблема:**
- `Dashboard.tsx` существует, но нет роута в `App.tsx`
- Дублирует функциональность `Analytics.tsx` (Decision KPI)

### 5.5. ⚠️ НИЗКОЕ: Неиспользуемые компоненты

**Проблема:**
- 5 компонентов не импортируются нигде
- Захламляют код, могут вводить в заблуждение

---

## 6. CANONICAL FLOW VERIFICATION

**Канонический поток (из .cursorrules v10.0):**
```
Context → Deal Breakers → Decision → Financials → Risks → Reports / History
```

### 6.1. Analyzer.tsx — ✅ СООТВЕТСТВУЕТ

**Порядок блоков (строки 683-870):**
1. ✅ TenderContextPanel (строка 686)
2. ✅ DealBreakersPanel (строка 693)
3. ✅ DecisionBlock (строка 706) — только в Director Mode
4. ✅ FinancialMetricsGrid (строка 787)
5. ✅ HeroVerdict (строка 793)
6. ✅ AIConsultantIntro (строка 812)
7. ✅ RiskNarrative (строка 825)
8. ✅ DecisionSupport (строка 836)
9. ✅ Deep Dive (строка 872)

### 6.2. ComplexAudit.tsx — ✅ СООТВЕТСТВУЕТ

**Порядок блоков (строки 541-715):**
1. ✅ PackageContextPanel (строка 544)
2. ✅ DealBreakersPanel (строка 547)
3. ✅ DecisionBlock (строка 563) — только в Director Mode
4. ✅ FinancialMetricsGrid (строка 647)
5. ✅ HeroVerdict (строка 665)
6. ✅ AIConsultantIntro (строка 682)
7. ✅ RiskNarrative (строка 690)
8. ✅ DecisionSupport (строка 706)
9. ✅ Documents → Deep Dive (строка 718)

### 6.3. HistoryView.tsx — ✅ СООТВЕТСТВУЕТ (частично)

**Порядок:**
- История показывает элементы в хронологическом порядке
- Каждый элемент отображает: контекст → вердикт → решение → действия
- Отчёты доступны только после решения

**Проблема:**
- Элементы без решения всё равно отображаются (старые анализы)

### 6.4. DocumentGenerator.tsx — ⚠️ НЕ СООТВЕТСТВУЕТ

**Проблема:**
- Компонент доступен без обязательного решения
- Действия внутри могут быть заблокированы, но сам компонент работает

### 6.5. Calculator.tsx — ⚠️ НЕ СООТВЕТСТВУЕТ

**Проблема:**
- Компонент доступен без обязательного решения
- Расчёт доступен без решения

---

## 7. SUMMARY

### ✅ ЧТО РАБОТАЕТ ПРАВИЛЬНО

1. **Analyzer и ComplexAudit** — канонический порядок блоков соблюдён
2. **DecisionBlock** — правильно фиксирует решение, блокирует повторный выбор
3. **Отчёты в Analyzer/ComplexAudit** — требуют решение перед генерацией
4. **HistoryView** — отчёты требуют решение
5. **Audit Trail** — события фиксируются при решении и экспорте

### ❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ

1. **Decision не передаётся из Analyzer/ComplexAudit в App.tsx**
   - `currentDecision` всегда `undefined`
   - `DocumentGenerator` и `Calculator` получают решение только из `localStorage`
   - Нарушает канонический поток данных

### ⚠️ СРЕДНИЕ ПРОБЛЕМЫ

1. **DocumentGenerator и Calculator не требуют Decision**
   - Компоненты доступны без решения
   - Действия могут быть заблокированы, но сам компонент работает

2. **История может содержать элементы без решения**
   - Старые анализы отображаются без решения
   - Нарушает канон "анализ считается завершённым только после фиксации решения"

### ⚠️ НИЗКИЕ ПРОБЛЕМЫ

1. **Dashboard.tsx не используется** — нет роута
2. **5 неиспользуемых компонентов** — захламляют код
3. **onDecisionChange в TenderAnalysis не используется** — объявлен, но не передаётся дальше

---

## 8. RECOMMENDATIONS (для этапа 10.2)

1. **Исправить поток Decision:**
   - Передать `onDecisionChange` из `App.tsx` в `TenderAnalysis`
   - Передать `onDecisionChange` из `TenderAnalysis` в `Analyzer`/`ComplexAudit`
   - Обновлять `currentDecision` в `App.tsx` при фиксации решения

2. **Усилить требования Decision для DocumentGenerator и Calculator:**
   - Показывать сообщение "Сначала зафиксируйте решение" если `decision` отсутствует
   - Или блокировать доступ к компонентам без решения

3. **Обработать старые анализы в истории:**
   - Либо скрывать элементы без решения
   - Либо явно помечать как "Незавершённый анализ"

4. **Очистить неиспользуемые компоненты:**
   - Удалить или интегрировать `Dashboard.tsx`
   - Удалить неиспользуемые компоненты (`TenderAnalysisView`, `TenderList`, `TenderDetail`, `PackageHubDashboard`, `LegalControl`)

---

**Конец отчёта.**






