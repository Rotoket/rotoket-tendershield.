"""
Тестовый скрипт для проверки настроек YooKassa
Использование: python test_yookassa.py
"""
import sys
from config import settings

def test_yookassa():
    """Тестирует подключение к YooKassa"""
    
    print("=" * 50)
    print("🔍 Тест подключения YooKassa")
    print("=" * 50)
    
    shop_id = settings.YOOKASSA_SHOP_ID
    secret_key = settings.YOOKASSA_SECRET_KEY
    test_mode = settings.YOOKASSA_TEST_MODE
    
    # Проверяем, что ключи заполнены
    if not shop_id or not secret_key:
        print("❌ Ошибка: YOOKASSA_SHOP_ID или YOOKASSA_SECRET_KEY не заполнены в .env")
        print("\nДобавьте в backend/.env:")
        print("TENDER_YOOKASSA_SHOP_ID=your_shop_id")
        print("TENDER_YOOKASSA_SECRET_KEY=your_secret_key")
        print("TENDER_YOOKASSA_TEST_MODE=true")
        print("\n📖 Полная инструкция: API_KEYS_SETUP.md")
        return False
    
    print(f"\n💳 Настройки YooKassa:")
    print(f"   Shop ID: {shop_id}")
    print(f"   Secret Key: {secret_key[:10]}...{secret_key[-5:]} (скрыт)")
    print(f"   Тестовый режим: {'✅ Да' if test_mode else '❌ Нет'}")
    
    # Проверяем, установлена ли библиотека
    try:
        from yookassa import Configuration, Payment
        print("\n✅ Библиотека yookassa установлена")
    except ImportError:
        print("\n❌ Библиотека yookassa не установлена")
        print("\nУстановите её командой:")
        print("   pip install yookassa>=3.0.0")
        return False
    
    try:
        print("\n🔄 Настройка конфигурации YooKassa...")
        Configuration.account_id = shop_id
        Configuration.secret_key = secret_key
        print("✅ Конфигурация установлена")
        
        print("\n🔄 Создание тестового платежа...")
        payment = Payment.create({
            "amount": {
                "value": "1.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://example.com/payment/success"
            },
            "description": "Тестовый платёж TenderShield",
            "metadata": {
                "test": "true"
            }
        })
        
        print("✅ Тестовый платёж создан успешно!")
        print(f"\n📋 Информация о платеже:")
        print(f"   Payment ID: {payment.id}")
        print(f"   Status: {payment.status}")
        print(f"   Amount: {payment.amount.value} {payment.amount.currency}")
        print(f"   Confirmation URL: {payment.confirmation.confirmation_url if hasattr(payment, 'confirmation') else 'N/A'}")
        
        if test_mode:
            print("\n⚠️  ВНИМАНИЕ: Используется тестовый режим!")
            print("   Для продакшена установите TENDER_YOOKASSA_TEST_MODE=false")
            print("   и используйте боевые ключи.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при создании платежа: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        
        # Более детальная диагностика
        error_str = str(e).lower()
        if "unauthorized" in error_str or "401" in error_str:
            print("\n💡 Возможные причины:")
            print("   1. Неправильный Shop ID или Secret Key")
            print("   2. Используются тестовые ключи в боевом режиме (или наоборот)")
            print("   3. Ключи не активированы в личном кабинете YooKassa")
        elif "forbidden" in error_str or "403" in error_str:
            print("\n💡 Возможные причины:")
            print("   1. Доступ к API ограничен в настройках магазина")
            print("   2. Недостаточно прав у аккаунта")
        
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_yookassa()
    sys.exit(0 if success else 1)





