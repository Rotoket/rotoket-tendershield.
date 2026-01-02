# 🔧 ИСПРАВЛЕНИЕ MCP СЕРВЕРОВ НА WINDOWS

## ❌ ПРОБЛЕМА

Многие MCP серверы показывают ошибки в Cursor на Windows:
- `git`: Error
- `postgres`: Error  
- `pandoc`: Error
- `python`: Error
- `docker`: Error
- `browser`: Error
- `code-quality`: Error
- `npm`: Error

## 🔍 ПРИЧИНЫ

1. **npx не найден в PATH** - Cursor не может найти команду `npx`
2. **Неправильный формат команды** - на Windows может потребоваться `npx.cmd`
3. **Отсутствие переменных окружения** - некоторые серверы требуют дополнительные настройки
4. **Проблемы с правами доступа** - npx может не иметь прав на выполнение

## ✅ РЕШЕНИЕ 1: ПРОВЕРЬ PATH

### Шаг 1: Проверь, что npx доступен

Открой PowerShell и выполни:
```powershell
where.exe npx
```

Должно показать:
```
C:\Program Files\nodejs\npx
C:\Program Files\nodejs\npx.cmd
```

### Шаг 2: Проверь PATH

```powershell
$env:PATH -split ';' | Select-String -Pattern 'nodejs'
```

Должно показать:
```
C:\Program Files\nodejs\
```

### Шаг 3: Если PATH не содержит nodejs

Добавь в PATH:
1. Открой "Система" → "Дополнительные параметры системы"
2. Нажми "Переменные среды"
3. В "Системные переменные" найди `Path`
4. Добавь: `C:\Program Files\nodejs\`
5. Перезагрузи компьютер

---

## ✅ РЕШЕНИЕ 2: ИСПОЛЬЗУЙ ПОЛНЫЙ ПУТЬ

Если PATH не работает, используй полный путь к npx в `mcp.json`:

### Для Windows:

```json
{
  "mcpServers": {
    "git": {
      "command": "C:\\Program Files\\nodejs\\npx.cmd",
      "args": ["-y", "@modelcontextprotocol/server-git"],
      "description": "Git operations"
    }
  }
}
```

**⚠️ Проблема:** Это неудобно для каждого сервера.

---

## ✅ РЕШЕНИЕ 3: ПРОВЕРЬ ЛОГИ ОШИБОК

### Шаг 1: Открой логи в Cursor

1. Открой **Output** панель (внизу экрана)
2. Выбери фильтр: `MCP: user-<имя_сервера>`
3. Нажми "Show Output" на сервере с ошибкой

### Шаг 2: Найди ошибку

Типичные ошибки:
- `'npx' is not recognized` → npx не в PATH
- `ENOENT: no such file or directory` → неправильный путь
- `Access denied` → проблемы с правами
- `Connection refused` → сервер не может подключиться

---

## ✅ РЕШЕНИЕ 4: ПЕРЕУСТАНОВИ NODE.JS

Если ничего не помогает:

1. **Удали Node.js:**
   - Панель управления → Программы → Удалить Node.js

2. **Скачай свежую версию:**
   - https://nodejs.org/
   - Выбери LTS версию (20.x или 22.x)

3. **Установи с опцией "Add to PATH":**
   - При установке отметь "Add to PATH"
   - Перезагрузи компьютер

4. **Проверь:**
   ```powershell
   node --version
   npx --version
   ```

---

## ✅ РЕШЕНИЕ 5: ИСПОЛЬЗУЙ NVM (РЕКОМЕНДУЕТСЯ)

NVM (Node Version Manager) упрощает управление Node.js:

### Установка NVM для Windows:

1. Скачай: https://github.com/coreybutler/nvm-windows/releases
2. Установи `nvm-setup.exe`
3. Открой PowerShell (от имени администратора)

### Использование:

```powershell
# Установи Node.js
nvm install 20.18.0

# Используй эту версию
nvm use 20.18.0

# Проверь
node --version
npx --version
```

---

## ✅ РЕШЕНИЕ 6: ПРОВЕРЬ CURSOR SETTINGS

### Шаг 1: Открой Cursor Settings

1. `Ctrl+,` (Settings)
2. `Tools & MCP` → `MCP Servers`

### Шаг 2: Проверь каждый сервер

Для каждого сервера с ошибкой:
1. Нажми "Show Output"
2. Скопируй ошибку
3. Исправь согласно ошибке

### Шаг 3: Перезагрузи Cursor

1. Закрой Cursor полностью
2. Открой Cursor снова
3. Проверь, что серверы загрузились

---

## 🔧 БЫСТРОЕ ИСПРАВЛЕНИЕ

### Вариант 1: Используй готовый скрипт

Создай файл `fix_mcp_path.ps1`:

```powershell
# Проверка PATH
$nodePath = "C:\Program Files\nodejs"
if ($env:PATH -notlike "*$nodePath*") {
    Write-Host "Добавляю $nodePath в PATH..."
    [Environment]::SetEnvironmentVariable("Path", $env:Path + ";$nodePath", "User")
    Write-Host "✅ PATH обновлён. Перезагрузи компьютер!"
} else {
    Write-Host "✅ PATH уже содержит nodejs"
}

# Проверка npx
$npx = Get-Command npx -ErrorAction SilentlyContinue
if ($npx) {
    Write-Host "✅ npx найден: $($npx.Path)"
} else {
    Write-Host "❌ npx не найден. Установи Node.js!"
}
```

Запусти:
```powershell
.\fix_mcp_path.ps1
```

### Вариант 2: Ручное исправление

1. **Скопируй mcp.json:**
   - Открой: `C:\Users\Dom\AppData\Roaming\Cursor\mcp.json`
   - Скопируй содержимое из `mcp/mcp.json`

2. **Проверь JSON синтаксис:**
   - Открой в Cursor
   - Убедись, что нет ошибок

3. **Перезагрузи Cursor:**
   - Закрой полностью
   - Открой снова

---

## 📋 ЧЕКЛИСТ ИСПРАВЛЕНИЯ

- [ ] Проверил, что Node.js установлен (`node --version`)
- [ ] Проверил, что npx доступен (`npx --version`)
- [ ] Проверил PATH (содержит `C:\Program Files\nodejs\`)
- [ ] Скопировал `mcp.json` в `C:\Users\Dom\AppData\Roaming\Cursor\mcp.json`
- [ ] Проверил JSON синтаксис (нет ошибок)
- [ ] Перезагрузил Cursor
- [ ] Проверил логи ошибок для каждого сервера
- [ ] Исправил ошибки согласно логам

---

## 🆘 ЕСЛИ НИЧЕГО НЕ ПОМОГАЕТ

1. **Проверь версию Cursor:**
   - Должна быть последняя версия
   - Обнови через Help → Check for Updates

2. **Проверь версию Node.js:**
   - Должна быть 18.x или выше
   - Обнови через nvm или официальный установщик

3. **Проверь права доступа:**
   - Запусти Cursor от имени администратора
   - Проверь, что npx имеет права на выполнение

4. **Очисти кэш Cursor:**
   - Закрой Cursor
   - Удали: `C:\Users\Dom\AppData\Roaming\Cursor\Cache`
   - Открой Cursor снова

---

## ✅ ГОТОВО!

После исправления все MCP серверы должны работать.

**Проверь:**
- Settings → Tools & MCP → MCP Servers
- Все серверы должны быть зелёными (без ошибок)




















