# 🚀 БЫСТРОЕ ИСПРАВЛЕНИЕ MCP СЕРВЕРОВ

## ❌ ПРОБЛЕМА

Многие MCP серверы показывают ошибки в Cursor:
- git, postgres, pandoc, python, docker, browser, code-quality, npm

## ✅ РЕШЕНИЕ (3 ШАГА)

### ШАГ 1: Проверь, что npx доступен

Открой PowerShell и выполни:
```powershell
npx --version
```

Должно показать версию (например: `10.8.2`)

**Если ошибка:** Перезагрузи компьютер или добавь в PATH:
```
C:\Program Files\nodejs\
```

---

### ШАГ 2: Обнови mcp.json в Cursor

1. **Открой файл:**
   ```
   C:\Users\Dom\AppData\Roaming\Cursor\mcp.json
   ```

2. **Скопируй содержимое из проекта:**
   - Открой: `mcp/mcp.json` в проекте
   - Скопируй ВСЁ содержимое
   - Вставь в `C:\Users\Dom\AppData\Roaming\Cursor\mcp.json`

3. **Проверь JSON синтаксис:**
   - Открой файл в Cursor
   - Убедись, что нет красных подчёркиваний (ошибок)

---

### ШАГ 3: Перезагрузи Cursor

1. **Закрой Cursor полностью:**
   - Файл → Выход
   - Или закрой все окна Cursor

2. **Открой Cursor снова**

3. **Проверь серверы:**
   - Settings → Tools & MCP → MCP Servers
   - Все серверы должны быть зелёными

---

## 🔍 ЕСЛИ ВСЁ ЕЩЁ НЕ РАБОТАЕТ

### Проверь логи ошибок:

1. Открой **Cursor Settings** → **Tools & MCP** → **MCP Servers**
2. Для каждого сервера с ошибкой:
   - Нажми **"Show Output"**
   - Скопируй ошибку
   - Исправь согласно ошибке

### Типичные ошибки:

**Ошибка:** `'npx' is not recognized`
**Решение:** Перезагрузи компьютер или добавь `C:\Program Files\nodejs\` в PATH

**Ошибка:** `ENOENT: no such file or directory`
**Решение:** Проверь, что файл `mcp.json` существует и JSON синтаксис корректен

**Ошибка:** `Connection refused`
**Решение:** Проверь, что PostgreSQL запущен (для postgres сервера)

---

## 📋 ЧЕКЛИСТ

- [ ] `npx --version` работает
- [ ] `mcp.json` скопирован в `C:\Users\Dom\AppData\Roaming\Cursor\mcp.json`
- [ ] JSON синтаксис корректен (нет ошибок)
- [ ] Cursor перезагружен
- [ ] Проверены логи ошибок для каждого сервера

---

## ✅ ГОТОВО!

После выполнения всех шагов все MCP серверы должны работать.

**Проверь:**
- Settings → Tools & MCP → MCP Servers
- Все серверы зелёные (без ошибок)

---

## 📚 ДОПОЛНИТЕЛЬНАЯ ПОМОЩЬ

- **Детальная диагностика:** `mcp/MCP_FIX_WINDOWS.md`
- **Диагностический скрипт:** `mcp/diagnose_mcp_simple.ps1`
- **Настройка:** `mcp/MCP_JSON_SETUP_GUIDE.md`




















