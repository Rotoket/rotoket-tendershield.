# 📧 Настройка отправки email для сброса пароля

## Проблема

Если в `.env` файле не настроены `TENDER_SMTP_USER` и `TENDER_SMTP_PASSWORD`, система работает в режиме **MOCK EMAIL** - письма только логируются, но не отправляются.

## Решение

### Вариант 1: Настройка Gmail (рекомендуется)

1. **Откройте `backend/.env` файл**

2. **Добавьте настройки SMTP:**

```env
TENDER_SMTP_HOST=smtp.gmail.com
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=ваш-email@gmail.com
TENDER_SMTP_PASSWORD=ваш-пароль-приложения
TENDER_SMTP_FROM=noreply@tendershield.pro
TENDER_SMTP_USE_TLS=true
TENDER_FRONTEND_URL=http://localhost:5174
```

3. **Получите пароль приложения для Gmail:**

   - Перейдите на https://myaccount.google.com/apppasswords
   - Войдите в аккаунт Google
   - Выберите "Пароли приложений"
   - Выберите "Почта" и "Другое устройство"
   - Введите название (например, "Tender Shield Pro")
   - Скопируйте сгенерированный пароль (16 символов)
   - Вставьте его в `TENDER_SMTP_PASSWORD`

### Вариант 2: Настройка Mail.ru

```env
TENDER_SMTP_HOST=smtp.mail.ru
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=ваш-email@mail.ru
TENDER_SMTP_PASSWORD=ваш-пароль-приложения
TENDER_SMTP_FROM=noreply@tendershield.pro
TENDER_SMTP_USE_TLS=true
```

### Вариант 3: Настройка Yandex

```env
TENDER_SMTP_HOST=smtp.yandex.ru
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=ваш-email@yandex.ru
TENDER_SMTP_PASSWORD=ваш-пароль-приложения
TENDER_SMTP_FROM=noreply@tendershield.pro
TENDER_SMTP_USE_TLS=true
```

## Проверка настроек

После настройки перезапустите backend и проверьте логи:

```bash
cd backend
python -m uvicorn main:app --reload
```

При запросе сброса пароля вы должны увидеть в логах:
- ✅ `Email отправлен: ваш-email@example.com - Сброс пароля в Tender Shield Pro` (если SMTP настроен)
- ⚠️ `[MOCK EMAIL] ⚠️ SMTP не настроен` (если SMTP не настроен)

## Проверка отправки

1. Запросите сброс пароля через форму
2. Проверьте логи backend - должно быть `✅ Email отправлен`
3. Проверьте почту (включая спам)

## Если письма не приходят

1. Проверьте логи backend на наличие ошибок SMTP
2. Убедитесь, что пароль приложения правильный (не основной пароль!)
3. Проверьте, не блокирует ли брандмауэр порт 587
4. Для Gmail: убедитесь, что включен доступ для "ненадежных приложений" или используйте пароль приложения

