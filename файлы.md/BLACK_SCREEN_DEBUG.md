# 🔍 Диагностика черного экрана

## Исправления

1. ✅ Убрана дублированная проверка `if (!result) return null;` в DecisionPreview
2. ✅ Добавлена обработка ошибок в App.tsx (global error handlers)
3. ✅ Исправлен импорт иконки Minus → MinusIcon

## Что проверить в браузере

### 1. Откройте консоль разработчика (F12)

**Проверьте:**
- Есть ли ошибки в консоли (красные сообщения)?
- Что показывает вкладка Console?

### 2. Проверьте вкладку Network

- Загружаются ли все файлы?
- Есть ли ошибки 404 или 500?

### 3. Проверьте React DevTools

Если установлены React DevTools:
- Видно ли компонент App в дереве?
- Есть ли ошибки в компонентах?

## Возможные причины

### Причина 1: Ошибка JavaScript в консоли

**Решение:** Скопируйте ошибку из консоли и сообщите мне

### Причина 2: Backend не запущен

**Проверка:**
```bash
cd backend
python -m uvicorn main:app --reload
```

Должен быть доступен на `http://localhost:8000`

### Причина 3: CSS не загружается

**Проверка:** В консоли браузера выполните:
```javascript
document.getElementById('root').innerHTML
```

Если видите HTML, но нет стилей - проблема с CSS.

### Причина 4: Ошибка в DecisionPreview

**Временное решение:** Закомментируйте использование DecisionPreview в TenderAnalysis:

```typescript
{/* Decision Preview — ориентация директора перед решением */}
{/* {!localDecision && (
  <DecisionPreview ... />
)} */}
```

## Быстрая диагностика

Откройте консоль браузера и выполните:

```javascript
// Проверка, что React загружен
console.log('React:', typeof React !== 'undefined');
console.log('Root element:', document.getElementById('root'));

// Проверка ошибок
window.addEventListener('error', (e) => {
  console.error('Global error:', e.error);
});

window.addEventListener('unhandledrejection', (e) => {
  console.error('Unhandled rejection:', e.reason);
});
```

## Следующие шаги

1. Откройте консоль (F12)
2. Перезагрузите страницу (F5)
3. Скопируйте все ошибки из консоли
4. Сообщите мне, что видно в консоли

