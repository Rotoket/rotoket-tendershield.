"""
Тестовый скрипт для проверки настроек SMTP
Использование: python test_smtp.py
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys
from config import settings

def test_smtp():
    """Тестирует подключение и отправку email через SMTP"""
    
    print("=" * 50)
    print("🔍 Тест подключения SMTP")
    print("=" * 50)
    
    # Получаем настройки из конфига
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD
    smtp_from = settings.SMTP_FROM or smtp_user
    
    # Проверяем, что настройки заполнены
    if not smtp_user or not smtp_password:
        print("❌ Ошибка: SMTP_USER или SMTP_PASSWORD не заполнены в .env")
        print("\nДобавьте в backend/.env:")
        print("TENDER_SMTP_USER=your-email@gmail.com")
        print("TENDER_SMTP_PASSWORD=your-app-password")
        return False
    
    print(f"\n📧 Настройки SMTP:")
    print(f"   Host: {smtp_host}")
    print(f"   Port: {smtp_port}")
    print(f"   User: {smtp_user}")
    print(f"   From: {smtp_from}")
    print(f"   TLS: {settings.SMTP_USE_TLS}")
    
    # Запрашиваем тестовый email
    test_email = input("\n✉️  Введите email для отправки тестового письма: ").strip()
    
    if not test_email:
        print("❌ Email не указан, пропускаем отправку")
        return False
    
    try:
        print("\n🔄 Подключение к SMTP-серверу...")
        server = smtplib.SMTP(smtp_host, smtp_port)
        print("✅ Подключение установлено")
        
        if settings.SMTP_USE_TLS:
            print("🔒 Включение TLS...")
            server.starttls()
            print("✅ TLS включен")
        
        print("🔐 Авторизация...")
        server.login(smtp_user, smtp_password)
        print("✅ Авторизация успешна")
        
        # Создаём письмо
        msg = MIMEMultipart()
        msg["Subject"] = "Тест TenderShield - Проверка SMTP"
        msg["From"] = smtp_from
        msg["To"] = test_email
        
        body = """
Это тестовое письмо от TenderShield Pro.

Если вы получили это письмо, значит настройки SMTP работают корректно! ✅

Дата отправки: {}
        """.format(__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        msg.attach(MIMEText(body, "plain", "utf-8"))
        
        print(f"\n📤 Отправка письма на {test_email}...")
        server.send_message(msg)
        server.quit()
        
        print("✅ Письмо успешно отправлено!")
        print(f"\n📬 Проверьте почтовый ящик {test_email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Ошибка авторизации: {e}")
        print("\n💡 Возможные причины:")
        print("   1. Неправильный пароль приложения")
        print("   2. Двухфакторная аутентификация не включена")
        print("   3. Пароль приложения не создан")
        print("\n📖 См. инструкцию: API_KEYS_SETUP.md")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ Ошибка подключения: {e}")
        print("\n💡 Возможные причины:")
        print("   1. Неправильный SMTP_HOST или SMTP_PORT")
        print("   2. Брандмауэр блокирует подключение")
        print("   3. Проблемы с интернет-соединением")
        return False
        
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_smtp()
    sys.exit(0 if success else 1)



























