# 🚀 Быстрая установка Pandoc MCP сервера

## Шаг 1: Установите библиотеку MCP

```bash
# В виртуальном окружении backend (рекомендуется)
cd backend
pip install mcp

# Или глобально
pip install mcp
```

## Шаг 2: Проверьте установку Pandoc

```bash
pandoc --version
```

Если Pandoc не установлен:
- **Windows**: Скачайте с https://pandoc.org/installing.html
- **Linux**: `sudo apt-get install pandoc` (Ubuntu/Debian)
- **Mac**: `brew install pandoc`

## Шаг 3: Тестовая проверка

```bash
# Из корня проекта
python pandoc_mcp.py
```

Если сервер запустился без ошибок - всё готово!

## Шаг 4: Настройка Cursor

Файл конфигурации уже обновлен: `mcp/mcp.json`

**Путь к файлу конфигурации Cursor:**
- **Windows**: `%APPDATA%\Cursor\mcp.json`
- **Mac**: `~/Library/Application Support/Cursor/mcp.json`
- **Linux**: `~/.config/Cursor/mcp.json`

**Скопируйте секцию `pandoc` из `mcp/mcp.json` в ваш файл конфигурации Cursor.**

## Готово! 🎉

После перезапуска Cursor MCP-сервер будет доступен для использования.

Подробная документация: `PANDOC_MCP_SETUP.md`





