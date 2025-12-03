"""
Модуль для работы с платежной системой Yandex Kassa
Базовая интеграция для обработки платежей и подписок
"""

import uuid
import hmac
import hashlib
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from database import User, Tariff
from config import settings

logger = logging.getLogger(__name__)

# Настройки Yandex Kassa (из переменных окружения)
YOOKASSA_SHOP_ID = getattr(settings, 'YOOKASSA_SHOP_ID', None)
YOOKASSA_SECRET_KEY = getattr(settings, 'YOOKASSA_SECRET_KEY', None)
YOOKASSA_TEST_MODE = getattr(settings, 'YOOKASSA_TEST_MODE', True)

# Если Yandex Kassa не настроена, используем эмуляцию для разработки
USE_MOCK_PAYMENT = not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY


def create_payment(user_id: int, tariff_id: int, db: Session) -> Dict:
    """Создает платеж для подписки на тариф
    
    Args:
        user_id: ID пользователя
        tariff_id: ID тарифа
        db: Сессия БД
        
    Returns:
        Словарь с информацией о платеже (payment_id, confirmation_url)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    tariff = db.query(Tariff).filter(Tariff.id == tariff_id).first()
    if not tariff:
        raise HTTPException(status_code=404, detail="Тариф не найден")
    
    if tariff.price == 0:
        raise HTTPException(status_code=400, detail="Этот тариф бесплатный")
    
    # Генерируем уникальный ID платежа
    payment_id = str(uuid.uuid4())
    
    if USE_MOCK_PAYMENT:
        # Эмуляция платежа для разработки
        logger.warning("Используется эмуляция платежа (Yandex Kassa не настроена)")
        return {
            "payment_id": payment_id,
            "confirmation_url": f"http://localhost:8000/api/payment/mock-confirm?payment_id={payment_id}",
            "amount": tariff.price,
            "currency": "RUB",
            "description": f"Подписка {tariff.name} на месяц",
            "test_mode": True
        }
    
    # Реальная интеграция с Yandex Kassa
    try:
        from yookassa import Configuration, Payment
        
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY
        
        payment = Payment.create({
            "amount": {
                "value": f"{tariff.price}.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"{settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else 'http://localhost:5173'}/payment/success"
            },
            "capture": True,
            "description": f"Подписка {tariff.name} на месяц",
            "metadata": {
                "user_id": user_id,
                "tariff_id": tariff_id,
                "payment_id": payment_id
            }
        }, payment_id)
        
        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "amount": tariff.price,
            "currency": "RUB",
            "description": f"Подписка {tariff.name} на месяц",
            "test_mode": YOOKASSA_TEST_MODE
        }
    except ImportError:
        logger.error("Библиотека yookassa не установлена. Используется эмуляция.")
        return {
            "payment_id": payment_id,
            "confirmation_url": f"http://localhost:8000/api/payment/mock-confirm?payment_id={payment_id}",
            "amount": tariff.price,
            "currency": "RUB",
            "description": f"Подписка {tariff.name} на месяц",
            "test_mode": True
        }
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        raise HTTPException(status_code=500, detail="Ошибка создания платежа")


def verify_webhook_signature(body: str, signature: str) -> bool:
    """Проверяет подпись webhook от Yandex Kassa"""
    if USE_MOCK_PAYMENT:
        return True  # В тестовом режиме пропускаем проверку
    
    if not YOOKASSA_SECRET_KEY:
        return False
    
    expected_signature = hmac.new(
        YOOKASSA_SECRET_KEY.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


def process_payment_webhook(webhook_data: Dict, db: Session) -> bool:
    """Обрабатывает webhook от Yandex Kassa о статусе платежа
    
    Args:
        webhook_data: Данные webhook
        db: Сессия БД
        
    Returns:
        True если платеж успешно обработан
    """
    event_type = webhook_data.get("event")
    payment_data = webhook_data.get("object", {})
    
    if event_type != "payment.succeeded":
        logger.info(f"Webhook событие {event_type} пропущено")
        return False
    
    payment_id = payment_data.get("id")
    metadata = payment_data.get("metadata", {})
    user_id = metadata.get("user_id")
    tariff_id = metadata.get("tariff_id")
    
    if not user_id or not tariff_id:
        logger.error(f"В webhook отсутствуют user_id или tariff_id: {payment_id}")
        return False
    
    user = db.query(User).filter(User.id == user_id).first()
    tariff = db.query(Tariff).filter(Tariff.id == tariff_id).first()
    
    if not user or not tariff:
        logger.error(f"Пользователь или тариф не найдены: user_id={user_id}, tariff_id={tariff_id}")
        return False
    
    # Активируем подписку
    now = datetime.utcnow()
    user.tariff_id = tariff_id
    user.plan_type = tariff.name.lower() if tariff.name else "pro"
    user.subscription_start = now
    user.subscription_end = now + timedelta(days=30)  # Месячная подписка
    
    # Если был триал, завершаем его
    if user.plan_type == "trial":
        user.trial_end = now
    
    db.commit()
    logger.info(f"Подписка активирована для пользователя {user.email} на тариф {tariff.name}")
    
    return True


def activate_subscription_mock(user_id: int, tariff_id: int, db: Session) -> bool:
    """Эмуляция активации подписки (для тестирования без реальных платежей)"""
    user = db.query(User).filter(User.id == user_id).first()
    tariff = db.query(Tariff).filter(Tariff.id == tariff_id).first()
    
    if not user or not tariff:
        return False
    
    now = datetime.utcnow()
    user.tariff_id = tariff_id
    user.plan_type = tariff.name.lower() if tariff.name else "pro"
    user.subscription_start = now
    user.subscription_end = now + timedelta(days=30)
    
    if user.plan_type == "trial":
        user.trial_end = now
    
    db.commit()
    logger.info(f"[MOCK] Подписка активирована для пользователя {user.email} на тариф {tariff.name}")
    
    return True

