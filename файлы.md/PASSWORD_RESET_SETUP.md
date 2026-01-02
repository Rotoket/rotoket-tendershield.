# Настройка восстановления пароля

## ✅ Что реализовано

### Backend
- ✅ Таблица `password_reset_tokens` для хранения токенов
- ✅ Endpoint `POST /api/auth/forgot-password` - запрос восстановления
- ✅ Endpoint `POST /api/auth/reset-password` - сброс пароля по токену
- ✅ Email service с SMTP отправкой
- ✅ Безопасность: всегда возвращает `{"ok": true}`, не раскрывает существование email
- ✅ Токен одноразовый, TTL 30 минут

### Frontend
- ✅ Компонент `ForgotPassword` - экран запроса восстановления
- ✅ Компонент `ResetPassword` - экран ввода нового пароля
- ✅ Обработка токена из URL (`/reset-password?token=XXX`)
- ✅ Переход на экран входа после успешного сброса

## 🔧 Настройка SMTP

### 1. Добавьте в `backend/.env`:

```env
# SMTP настройки
TENDER_SMTP_HOST=smtp.gmail.com
TENDER_SMTP_PORT=587
TENDER_SMTP_USER=your-email@gmail.com
TENDER_SMTP_PASSWORD=your-app-password
TENDER_SMTP_FROM=noreply@tendershield.pro
TENDER_SMTP_USE_TLS=true

# URL фронтенда для ссылок в email
TENDER_FRONTEND_URL=http://localhost:5173
# Для продакшена: TENDER_FRONTEND_URL=https://app.tendershield.pro
```

### 2. Для Gmail:
1. Включите двухфакторную аутентификацию
2. Создайте "Пароль приложения" в настройках аккаунта
3. Используйте этот пароль в `TENDER_SMTP_PASSWORD`

### 3. Альтернативы:
- **Mail.ru**: `smtp.mail.ru:587`
- **Yandex**: `smtp.yandex.ru:587`
- **SendGrid/Mailgun**: см. документацию сервиса

## 🧪 Тестирование

### 1. Запрос восстановления:
```bash
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
```

Ожидаемый ответ: `{"ok": true}` (всегда, даже если email не найден)

### 2. Проверка email:
- Откройте почту указанного адреса
- Найдите письмо "Сброс пароля в Tender Shield Pro"
- Проверьте ссылку: должна быть `/reset-password?token=XXX`

### 3. Сброс пароля:
```bash
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token": "TOKEN_FROM_EMAIL", "new_password": "newpassword123"}'
```

## 🔒 Безопасность

- ✅ Токен одноразовый (помечается как `used` после использования)
- ✅ TTL 30 минут
- ✅ Не раскрывает существование email (всегда `{"ok": true}`)
- ✅ Пароль хешируется перед сохранением
- ✅ Старые неиспользованные токены удаляются при создании нового

## 📝 Примечания

- Если SMTP не настроен, email будет логироваться в консоль (mock mode)
- Для продакшена обязательно настройте реальный SMTP
- URL в email формируется из `TENDER_FRONTEND_URL`

