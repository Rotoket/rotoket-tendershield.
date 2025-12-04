# 🚀 Быстрый старт: Получение API-ключей

## 📋 Что нужно сделать (чек-лист)

- [ ] **YooKassa** — для приёма платежей
- [ ] **SMTP (Gmail)** — для отправки email
- [ ] **JWT Secret Key** — для безопасности (генерируется самостоятельно)

---

## 1️⃣ YooKassa (5-10 минут)

1. Перейдите на: **https://yookassa.ru/**
2. Войдите/зарегистрируйтесь через Яндекс
3. Создайте магазин: **"Мой магазин"** → **"Добавить магазин"**
4. Получите ключи: **"Настройки"** → **"API"**
   - Shop ID
   - Секретный ключ (тестовый начинается с `test_`)
5. Включите **"Тестовый режим"** для разработки

📖 **Подробная инструкция:** [API_KEYS_SETUP.md](API_KEYS_SETUP.md#1-yookassa-yandex-kassa--приём-платежей)

**Проверка:** `python backend/test_yookassa.py`

---

## 2️⃣ SMTP Gmail (3-5 минут)

1. Используйте Gmail-аккаунт (или создайте новый)
2. Включите двухфакторную аутентификацию: **https://myaccount.google.com/security**
3. Создайте пароль приложения: **"Пароли приложений"**
   - Приложение: `Почта`
   - Устройство: `TenderShield Server`
4. Скопируйте 16-символьный пароль (без пробелов)

📖 **Подробная инструкция:** [API_KEYS_SETUP.md](API_KEYS_SETUP.md#2-smtp-gmail--отправка-email)

**Проверка:** `python backend/test_smtp.py`

---

## 3️⃣ JWT Secret Key (1 минута)

1. Перейдите на: **https://www.lastpass.com/features/password-generator**
2. Установите длину: **64 символа**
3. Скопируйте сгенерированный ключ

Или через Python:
```python
import secrets
print(secrets.token_urlsafe(64))
```

📖 **Подробная инструкция:** [API_KEYS_SETUP.md](API_KEYS_SETUP.md#3-jwt-secret-key--ключ-безопасности)

---

## 4️⃣ Заполнение .env файла

1. Скопируйте шаблон:
   ```bash
   cp backend/env.example backend/.env
   ```

2. Откройте `backend/.env` и заполните все ключи:
   ```env
   TENDER_YOOKASSA_SHOP_ID=ваш_shop_id
   TENDER_YOOKASSA_SECRET_KEY=test_ваш_ключ
   TENDER_SMTP_USER=your-email@gmail.com
   TENDER_SMTP_PASSWORD=ваш_пароль_приложения
   TENDER_SECRET_KEY=ваш_сгенерированный_ключ
   ```

3. **Проверьте, что `.env` не в Git:**
   ```bash
   git status  # Не должен показывать backend/.env
   ```

---

## ✅ Проверка работоспособности

После заполнения всех ключей, проверьте их:

```bash
# Проверка YooKassa
python backend/test_yookassa.py

# Проверка SMTP
python backend/test_smtp.py
```

Если всё работает — вы готовы к запуску! 🎉

---

## 📖 Полная документация

Подробные инструкции со скриншотами и решениями проблем:
👉 **[API_KEYS_SETUP.md](API_KEYS_SETUP.md)**

---

## ❓ Частые проблемы

**YooKassa: "Unauthorized"**
→ Проверьте, что используете правильные ключи (тестовые для теста, боевые для продакшена)

**Gmail: "Authentication failed"**
→ Убедитесь, что создали именно **пароль приложения**, а не обычный пароль от аккаунта

**Файл .env не работает**
→ Проверьте, что все переменные начинаются с префикса `TENDER_`



