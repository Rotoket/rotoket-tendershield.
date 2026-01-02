# Быстрая настройка Email (для восстановления пароля)

## Проблема
Email не отправляется, форма зависает.

## Решение 1: Mock режим (для разработки)

Если SMTP не настроен, система автоматически переходит в **mock режим** - письма логируются в консоль backend, но не отправляются.

**Проверьте логи backend** - должны быть сообщения:
```
[MOCK EMAIL] ⚠️ SMTP не настроен, эмулируем отправку:
  To: your@email.com
  Subject: Сброс пароля...
```

В этом случае:
- ✅ Форма должна работать (не зависать)
- ✅ Письмо логируется в консоль
- ❌ Реальное письмо не отправляется

## Решение 2: Настройка реального SMTP

### Для Gmail:

1. Включите двухфакторную аутентификацию в Google аккаунте
2. Создайте "Пароль приложения":
   - Перейдите: https://myaccount.google.com/apppasswords
   - Выберите "Почта" и "Другое устройство"
   - Скопируйте 16-символьный пароль

3. Добавьте в `backend/.env`:
```env
TENDER_SMTP_HOST=smtp.gmail.com
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=your-email@gmail.com
TENDER_SMTP_PASSWORD=your-16-char-app-password
TENDER_SMTP_FROM=noreply@tendershield.pro
TENDER_SMTP_USE_TLS=true
```

4. Перезапустите backend

### Для Mail.ru:

```env
TENDER_SMTP_HOST=smtp.mail.ru
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=your-email@mail.ru
TENDER_SMTP_PASSWORD=your-password
TENDER_SMTP_FROM=noreply@tendershield.pro
TENDER_SMTP_USE_TLS=true
```

### Для Yandex:

```env
TENDER_SMTP_HOST=smtp.yandex.ru
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=your-email@yandex.ru
TENDER_SMTP_PASSWORD=your-password
TENDER_SMTP_FROM=noreply@tendershield.pro
TENDER_SMTP_USE_TLS=true
```

## Что исправлено

1. ✅ Добавлен таймаут 10 секунд для SMTP соединения
2. ✅ Улучшена обработка ошибок SMTP
3. ✅ Добавлен таймаут 15 секунд на frontend
4. ✅ Mock режим работает корректно (не зависает)

## Проверка

1. Запустите backend и проверьте логи
2. Попробуйте восстановить пароль
3. Если SMTP не настроен - увидите `[MOCK EMAIL]` в логах
4. Если SMTP настроен - письмо должно отправиться

## Важно

- **Mock режим** - для разработки, письма не отправляются
- **Реальный SMTP** - для production, требует настройки
- Таймауты предотвращают зависание формы

