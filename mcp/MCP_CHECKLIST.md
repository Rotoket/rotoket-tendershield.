# ✅ ЧЕКЛИСТ УСТАНОВКИ MCP

## 📋 МИНИМАЛЬНЫЙ ЧЕКЛИСТ ВНЕДРЕНИЯ

### 🎯 MCP Серверы для Tender Shield Pro

- [ ] **MCP pandoc** установлен
  - Команда: `npx @modelcontextprotocol/server-pandoc`
  - Тест: "Используй MCP pandoc и преобразуй файл Проект_контракта.docx в Markdown"

- [ ] **MCP xlsx** установлен
  - Команда: `npx mcp-server-xlsx`
  - Тест: "Используй MCP xlsx и прочитай значение ячейки B12 из файла nmck.xlsx"

- [ ] **MCP python** установлен
  - Команда: `npx @modelcontextprotocol/server-python`
  - Тест: "Используй MCP python и посчитай: (22440 * 1.2 * 720) * 1.15"

- [ ] **MCP postgres** подключён
  - Команда: `npx @modelcontextprotocol/server-postgres`
  - DATABASE_URL настроен: `postgresql://postgres:postgres@localhost:5432/tender_shield`
  - Тест: "Используй MCP postgres и покажи список таблиц в базе данных"

---

### 🔧 MCP Серверы для разработки

- [ ] **sequential-thinking** установлен
- [ ] **context7** установлен
- [ ] **playwright** установлен
- [ ] **filesystem** установлен
- [ ] **git** установлен
- [ ] **docker** установлен
- [ ] **browser** установлен
- [ ] **code-quality** установлен
- [ ] **npm** установлен

---

## 🧪 ПРОВЕРКА РАБОТЫ

### ✅ Cursor видит MCP в tool list

1. Открой Cursor
2. Перейди в: `Settings > MCP Servers`
3. Должно быть видно все 14 серверов

### ✅ MCP вызываются по промпту

**Тест 1: Pandoc**
```
Используй MCP pandoc и преобразуй файл Проект_контракта.docx в Markdown.
```
→ Cursor должен вызвать MCP pandoc и вернуть результат

**Тест 2: XLSX**
```
Используй MCP xlsx и прочитай значение ячейки B12 из файла nmck.xlsx.
```
→ Cursor должен вызвать MCP xlsx и вернуть значение

**Тест 3: Python**
```
Используй MCP python и посчитай: (22440 * 1.2 * 720) * 1.15
```
→ Cursor должен вызвать MCP python и вернуть результат расчёта

**Тест 4: Postgres**
```
Используй MCP postgres и покажи список таблиц в базе данных.
```
→ Cursor должен вызвать MCP postgres и вернуть список таблиц

---

## ⚠️ ПРОВЕРКА КАНОНА

### ✅ MCP НЕ используется после Decision Preview

**Правильно:**
- MCP используется для обработки документов (до Decision Preview)
- MCP используется для расчётов (до Decision Preview)
- Guardrails работают БЕЗ MCP

**Неправильно:**
- MCP используется для генерации текста решений
- MCP используется после фиксации решения
- MCP используется в Guardrails

---

## 📋 КАНОНИЧЕСКИЙ ПАЙПЛАЙН

### ✅ Этап 1: Загрузка документов
- Пользователь загружает файлы

### ✅ Этап 2: MCP Обработка (ДО Decision Preview)
- MCP pandoc → Markdown
- MCP xlsx → Числовые значения
- MCP python → Пересчёт / Проверка

### ✅ Этап 3: Evidence Objects
- На основе обработанных данных

### ✅ Этап 4: Impact Logic
- Для каждого риска

### ✅ Этап 5: Decision Preview
- Формируется Decision Preview

### ✅ Этап 6: Guardrails (БЕЗ MCP)
- Language Guard
- Structural Guard
- Impact Guard
- Data Exhaustion Guard

---

## 🚨 ТИПОВЫЕ ОШИБКИ (НЕ СДЕЛАЙ ЭТО)

- [ ] ❌ Вызывать MCP из frontend
- [ ] ❌ Передавать MCP ключи в DeepSeek
- [ ] ❌ Использовать MCP для генерации текста решений
- [ ] ❌ Считать, что MCP "умнее модели"
- [ ] ❌ Использовать MCP после Decision Preview
- [ ] ❌ Использовать MCP в Guardrails

---

## ✅ ИТОГОВАЯ ПРОВЕРКА

- [ ] Все 14 MCP серверов установлены
- [ ] DATABASE_URL настроен правильно
- [ ] Cursor видит MCP в tool list
- [ ] Тестовые команды работают
- [ ] MCP используется только до Decision Preview
- [ ] Guardrails работают без MCP

---

## 📚 ДОКУМЕНТАЦИЯ

- **UI Setup:** `mcp/MCP_UI_SETUP_GUIDE.md`
- **JSON Setup:** `mcp/MCP_JSON_SETUP_GUIDE.md`
- **Integration:** `mcp/MCP_TENDER_SHIELD_INTEGRATION.md`
- **Postgres:** `mcp/POSTGRES_SETUP_EXPLAINED.md`

---

## ✅ ГОТОВО!

Если все пункты отмечены → MCP настроен правильно и готов к использованию!

**Время установки:** 5-10 минут  
**Ускорение обработки документов:** до 14x






















