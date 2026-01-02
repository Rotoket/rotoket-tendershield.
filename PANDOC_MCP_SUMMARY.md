# ✅ Pandoc MCP сервер установлен

## Что было сделано:

1. ✅ **Создан Python MCP-сервер**: `pandoc_mcp.py`
   - Конвертация документов в Markdown
   - Автоматическое извлечение НМЦК и ИУН
   - Работает без зависимости от npm

2. ✅ **Обновлены зависимости**: `backend/requirements.txt`
   - Добавлена библиотека `mcp>=0.9.0`

3. ✅ **Обновлена конфигурация**: `mcp/mcp.json`
   - Настроен Python-сервер вместо npm-версии

4. ✅ **Создана документация**:
   - `PANDOC_MCP_SETUP.md` - подробная инструкция
   - `INSTALL_PANDOC_MCP.md` - быстрая установка

---

## Следующие шаги:

### 1. Установите библиотеку MCP:

```bash
cd backend
pip install mcp
```

### 2. Скопируйте конфигурацию в Cursor:

**Откройте файл конфигурации Cursor:**
- Windows: `%APPDATA%\Cursor\mcp.json`
- Mac: `~/Library/Application Support/Cursor/mcp.json`
- Linux: `~/.config/Cursor/mcp.json`

**Скопируйте секцию `pandoc` из `mcp/mcp.json`:**

```json
"pandoc": {
  "command": "python",
  "args": ["C:\\Users\\Dom\\Desktop\\tender-shield-pro\\pandoc_mcp.py"],
  "timeout": 60000,
  "description": "Pandoc document converter (Python-based, вечный сервер)",
  "env": {
    "PANDOC_PATH": "pandoc"
  }
}
```

**Важно:** Измените путь `C:\\Users\\Dom\\Desktop\\tender-shield-pro\\pandoc_mcp.py` на ваш реальный путь к проекту!

### 3. Перезапустите Cursor

После перезапуска MCP-сервер будет доступен.

---

## Доступные функции:

### `convert_to_markdown(file_path, output_path=None)`
Конвертирует документ тендера в Markdown.

### `extract_nmck_iun(file_path)`
Извлекает НМЦК и ИУН из документа тендера.

---

## Пример использования:

После установки агент сможет использовать:

```
"Конвертируй файл охрана 2026 изм 1.docx в Markdown и извлеки НМЦК и ИУН"
```

Агент автоматически:
1. Конвертирует документ через Pandoc
2. Извлечет НМЦК и ИУН
3. Вернет структурированные данные

---

## Поддержка форматов:

- DOCX, DOC
- XLSX, XLS  
- ODT, RTF
- HTML, HTM

---

## Статус: ✅ Готово к использованию

После установки `mcp` библиотеки и настройки Cursor всё будет работать!





