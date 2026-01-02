# 🔧 Быстрое исправление отправки email

## Проблема
Система показывает "Письмо отправлено", но письмо не приходит.

## Причина
SMTP не настроен → система работает в режиме MOCK (только логирование).

## Решение за 2 минуты

### 1. Откройте `backend/.env`

### 2. Добавьте/обновите эти строки:

```env
# Email настройки (SMTP)
TENDER_SMTP_HOST=smtp.gmail.com
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=ваш-email@gmail.com
TENDER_SMTP_PASSWORD=ваш-пароль-приложения-16-символов
TENDER_SMTP_FROM=noreply@tendershield.pro
TENDER_SMTP_USE_TLS=true

# URL фронтенда для ссылок в письмах
TENDER_FRONTEND_URL=http://localhost:5174
```

### 3. Для Gmail получите пароль приложения:

1. Перейдите: https://myaccount.google.com/apppasswords
2. Войдите в Google аккаунт
3. Выберите "Пароли приложений" → "Почта" → "Другое устройство"
4. Название: "Tender Shield Pro"
5. Скопируйте 16-символьный пароль
6. Вставьте в `TENDER_SMTP_PASSWORD` (БЕЗ ПРОБЕЛОВ)

### 4. Перезапустите backend:

```bash
cd backend
python -m uvicorn main:app --reload
```

### 5. Проверьте логи:

При запросе сброса пароля в консоли backend должно быть:
- ✅ `Email отправлен: ваш-email@example.com` - если SMTP настроен
- ⚠️ `[MOCK EMAIL]` - если SMTP НЕ настроен

---

## Альтернативы Gmail

### Mail.ru:
```env
TENDER_SMTP_HOST=smtp.mail.ru
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=ваш-email@mail.ru
TENDER_SMTP_PASSWORD=ваш-пароль
```

### Yandex:
```env
TENDER_SMTP_HOST=smtp.yandex.ru
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=ваш-email@yandex.ru
TENDER_SMTP_PASSWORD=ваш-пароль-приложения
```

---

## После настройки

1. Проверьте логи backend при запросе сброса пароля
2. Проверьте почту (включая папку "Спам")
3. Письмо должно содержать ссылку вида: `http://localhost:5174/reset-password?token=...`

