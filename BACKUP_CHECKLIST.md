# ✅ ЧЕКЛИСТ БЭКАПА ДЛЯ WINDOWS 11

## 📦 Что должно быть сохранено

### ✅ Код проекта
- [x] Весь код (backend, frontend, infra)
- [x] Все конфигурационные файлы
- [x] Документация

### ✅ MCP файлы (НОВОЕ!)
- [x] `mcp/README.md` - единая точка входа
- [x] `mcp/SECURITY.md` - правила безопасности
- [x] `mcp/templates/cursor.mcp.example.json` - шаблон конфига MCP
- [x] `mcp/templates/.cursorules.example` - шаблон правил
- [x] `backend/MCP_MEMORY.md` - описание .mcp-memory.json
- [x] Все остальные MCP документы (11 файлов)

### ✅ Правила и конфиги
- [x] `.cursorrules` - правила проекта (169 строк)
- [x] `.gitignore` - обновлен (игнорирует локальные MCP конфиги)
- [x] `backend/.env` - секретные ключи (729 байт)
- [x] `infra/docker-compose.yml` - Docker конфигурация
- [x] `infra/nginx.conf` - Nginx конфигурация

### ✅ База данных
- [ ] Экспорт БД (если Docker был запущен)
- [ ] Список Ollama моделей

---

## 📍 Расположение бэкапа

**Последний бэкап:**
- Проект: `F:\Backup\tender-shield-pro-2025-12-14_16-33-16\`
- Конфиги: `F:\Backup\tender-shield-pro-env-2025-12-14_16-33-16\`

---

## 🔍 Проверка перед переустановкой

Выполните эти команды для проверки:

```powershell
# Проверка MCP файлов
Test-Path "F:\Backup\tender-shield-pro-2025-12-14_16-33-16\mcp\README.md"
Test-Path "F:\Backup\tender-shield-pro-2025-12-14_16-33-16\mcp\SECURITY.md"
Test-Path "F:\Backup\tender-shield-pro-2025-12-14_16-33-16\mcp\templates\cursor.mcp.example.json"

# Проверка конфигов
Test-Path "F:\Backup\tender-shield-pro-env-2025-12-14_16-33-16\backend\.env"
Test-Path "F:\Backup\tender-shield-pro-env-2025-12-14_16-33-16\.cursorrules"

# Проверка Git
cd c:\Users\Dom\Desktop\tender-shield-pro
git log --oneline -5
```

Все должно вернуть `True` и показать последние коммиты.

---

## ⚠️ ВАЖНО: Что НЕ должно быть в бэкапе

Следующие файлы **НЕ должны** быть в репозитории (и правильно игнорируются):
- `%APPDATA%\Cursor\mcp.json` - локальный конфиг Cursor
- `.cursorules` - локальные правила (если есть)
- Любые файлы с секретами (пароли, токены)

Эти файлы нужно будет создать заново после переустановки Windows, используя шаблоны из `mcp/templates/`.

---

## 🚀 После переустановки Windows 11

1. Восстановите проект из бэкапа или Git
2. Создайте локальный MCP конфиг:
   ```powershell
   # Скопируйте шаблон
   Copy-Item "mcp\templates\cursor.mcp.example.json" "$env:APPDATA\Cursor\mcp.json"
   
   # Отредактируйте mcp.json и замените CHANGE_ME на реальные значения
   notepad "$env:APPDATA\Cursor\mcp.json"
   ```
3. Следуйте инструкциям в `mcp/README.md`

---

**Дата последнего бэкапа:** 2025-12-14 16:33:16
**Статус:** ✅ Все файлы сохранены, готово к переустановке Windows 11
