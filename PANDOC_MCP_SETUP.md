# 🔧 Установка "вечного" MCP-сервера для Pandoc

## Описание

Собственный Python-сервер для конвертации документов тендеров через Pandoc. Работает без зависимости от npm пакетов и гарантированно доступен на любом сервере с Python.

## Преимущества

✅ **Независимость от npm** - работает только через Python  
✅ **Надежность** - не зависит от внешних пакетов, которые могут исчезнуть  
✅ **Расширяемость** - легко добавить новые функции извлечения данных  
✅ **Извлечение НМЦК и ИУН** - встроенная функция для автоматического поиска ключевых данных

---

## Шаг 1: Установка зависимостей

### На сервере (Linux/Windows):

```bash
# Убедитесь, что Pandoc установлен
pandoc --version

# Если Pandoc не установлен:
# Windows: скачайте с https://pandoc.org/installing.html
# Linux: sudo apt-get install pandoc  (Ubuntu/Debian)
#        sudo yum install pandoc      (CentOS/RHEL)

# Установите Python библиотеку MCP
pip install mcp

# Или если используете виртуальное окружение проекта:
cd backend
pip install -r requirements.txt
```

---

## Шаг 2: Проверка работы сервера

### Тестовая проверка:

```bash
# Из корня проекта
python pandoc_mcp.py
```

Если сервер запустился без ошибок - всё готово!

---

## Шаг 3: Конфигурация для Cursor

### Windows:

Откройте файл: `%APPDATA%\Cursor\mcp.json`

### Mac:

Откройте файл: `~/Library/Application Support/Cursor/mcp.json`

### Linux:

Откройте файл: `~/.config/Cursor/mcp.json`

### Добавьте или обновите секцию `pandoc`:

**Для Windows (абсолютный путь):**
```json
{
  "mcpServers": {
    "pandoc": {
      "command": "python",
      "args": ["C:\\Users\\Dom\\Desktop\\tender-shield-pro\\pandoc_mcp.py"],
      "timeout": 60000,
      "description": "Pandoc document converter (Python-based)",
      "env": {
        "PANDOC_PATH": "pandoc"
      }
    }
  }
}
```

**Для Linux/Mac (относительный путь от домашней директории):**
```json
{
  "mcpServers": {
    "pandoc": {
      "command": "python",
      "args": ["/path/to/tender-shield-pro/pandoc_mcp.py"],
      "timeout": 60000,
      "description": "Pandoc document converter (Python-based)",
      "env": {
        "PANDOC_PATH": "pandoc"
      }
    }
  }
}
```

**Если используете виртуальное окружение:**
```json
{
  "mcpServers": {
    "pandoc": {
      "command": "C:\\Users\\Dom\\Desktop\\tender-shield-pro\\backend\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\Dom\\Desktop\\tender-shield-pro\\pandoc_mcp.py"],
      "timeout": 60000,
      "description": "Pandoc document converter (Python-based)",
      "env": {
        "PANDOC_PATH": "pandoc"
      }
    }
  }
}
```

---

## Шаг 4: Перезапуск Cursor

После изменения конфигурации:
1. Закройте Cursor полностью
2. Откройте Cursor снова
3. MCP-сервер должен автоматически подключиться

---

## Использование

### Функция 1: Конвертация в Markdown

```python
# Агент может использовать:
convert_to_markdown(
    file_path="tender/tender 7 oxrana/охрана 2026 изм 1.docx",
    output_path="temp_analysis.md"  # опционально
)
```

### Функция 2: Извлечение НМЦК и ИУН

```python
# Агент может использовать:
extract_nmck_iun(
    file_path="tender/tender 7 oxrana/охрана 2026 изм 1.docx"
)

# Возвращает:
# {
#   "success": true,
#   "nmck": "6,701,935.68 руб.",
#   "nmck_numeric": 6701935.68,
#   "iun": "252253600872825360100100450018010244",
#   "markdown_path": "tender/tender 7 oxrana/охрана 2026 изм 1_converted.md"
# }
```

---

## Поддерживаемые форматы

- ✅ DOCX (Microsoft Word)
- ✅ DOC (старый формат Word)
- ✅ XLSX (Microsoft Excel)
- ✅ XLS (старый формат Excel)
- ✅ ODT (OpenDocument Text)
- ✅ RTF (Rich Text Format)
- ✅ HTML/HTM

---

## Устранение неполадок

### Ошибка: "Pandoc не найден в системе"

**Решение:**
1. Убедитесь, что Pandoc установлен: `pandoc --version`
2. Если Pandoc установлен, но не в PATH, укажите путь через переменную окружения:
   ```json
   "env": {
     "PANDOC_PATH": "C:\\Program Files\\Pandoc\\pandoc.exe"
   }
   ```

### Ошибка: "mcp library not installed"

**Решение:**
```bash
pip install mcp
```

### Ошибка: "File not found"

**Решение:**
- Убедитесь, что путь к файлу указан правильно
- Используйте абсолютные пути или пути относительно рабочей директории проекта

### Сервер не запускается в Cursor

**Решение:**
1. Проверьте путь к Python: `python --version`
2. Проверьте путь к `pandoc_mcp.py` - должен быть абсолютным
3. Проверьте логи Cursor (View → Output → MCP)

---

## Расширение функциональности

Чтобы добавить новые функции извлечения данных, отредактируйте `pandoc_mcp.py`:

```python
@mcp.tool()
def extract_custom_data(file_path: str) -> dict:
    """Ваша новая функция извлечения данных."""
    # Ваш код здесь
    pass
```

После добавления новой функции перезапустите Cursor.

---

## Альтернатива: Использование через командную строку

Если MCP не работает, можно использовать напрямую:

```bash
# Конвертация
python -c "from pandoc_mcp import convert_to_markdown; print(convert_to_markdown('file.docx'))"

# Извлечение НМЦК/ИУН
python -c "from pandoc_mcp import extract_nmck_iun; print(extract_nmck_iun('file.docx'))"
```

---

## Статус

✅ Сервер создан: `pandoc_mcp.py`  
✅ Зависимости добавлены: `backend/requirements.txt`  
✅ Конфигурация обновлена: `mcp/mcp.json`  
✅ Документация создана: `PANDOC_MCP_SETUP.md`

**Готово к использованию!**





