# Установка MCP Pandoc для TenderShield

## Проблема
`mcp-pandoc` требует Python 3.11+, у тебя установлен Python 3.10.11

## Решение: Установить Python 3.11+

### Способ 1: Через winget (быстро)

```powershell
winget install Python.Python.3.11
```

Или для Python 3.12:
```powershell
winget install Python.Python.3.12
```

### Способ 2: Через официальный сайт
1. Перейди на https://www.python.org/downloads/
2. Скачай Python 3.11 или 3.12
3. Установи (обязательно отметь "Add Python to PATH")

### Способ 3: Через Microsoft Store
Открой Microsoft Store и найди "Python 3.11" или "Python 3.12"

---

## После установки Python 3.11+

### Шаг 1: Установить mcp-pandoc

```powershell
py -3.11 -m pip install mcp-pandoc
```

### Шаг 2: Добавить в mcp.json

Конфигурация будет добавлена автоматически после установки Python 3.11+

---

## Проверка установки

```powershell
py -3.11 --version
py -3.11 -m pip list | Select-String "mcp-pandoc"
```

