# Исправления проблемы входа в систему

## Проблема
Пользователь не мог войти с email `Rotoket@mail.ru` и паролем `Rotoket10-34`.

## Диагностика

### Тест показал:
✅ Пользователь найден в БД
✅ Пароль верный (verify_password возвращает True)
✅ authenticate_user работает корректно

## Исправления

### 1. Case-insensitive поиск email (backend/auth.py)
**Проблема:** Поиск пользователя был чувствителен к регистру email.

**Исправление:**
```python
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Получает пользователя по email (case-insensitive)"""
    return db.query(User).filter(User.email.ilike(email)).first()
```

Теперь `Rotoket@mail.ru`, `rotoket@mail.ru`, `ROTOKET@MAIL.RU` - все работают одинаково.

### 2. Нормализация email на frontend (authService.ts)
**Добавлено:**
- Trim пробелов
- Приведение к lowercase
- Логирование попыток входа

```typescript
const normalizedEmail = (data.email || '').trim().toLowerCase();
```

## Проверка

Запустите тест:
```bash
cd backend
python test_login.py
```

Ожидаемый результат:
```
[OK] Пользователь найден
[OK] Пароль верный!
[OK] authenticate_user вернул пользователя
```

## Что проверить дальше

1. **Frontend логи:**
   - Откройте консоль браузера (F12)
   - Попробуйте войти
   - Проверьте логи `[AuthService] Login attempt:`

2. **Backend логи:**
   - Запустите backend
   - Попробуйте войти
   - Проверьте логи:
     - "Попытка входа: email=..."
     - "✅ Успешная аутентификация пользователя..."

3. **Если все еще не работает:**
   - Проверьте, что backend запущен
   - Проверьте CORS настройки
   - Проверьте, что токен сохраняется в localStorage

## Важно

- Email теперь всегда нормализуется (lowercase)
- Поиск в БД case-insensitive
- Пароль проверяется корректно (тест подтвердил)

