"""
Тесты для платежной системы
"""

import pytest
from payment import create_payment, activate_subscription_mock, verify_webhook_signature
from database import User, Tariff
from sqlalchemy.orm import Session


class TestPaymentSystem:
    """Тесты для платежной системы"""
    
    def test_create_payment_structure(self, db_session):
        """Тест структуры ответа создания платежа"""
        # Создаем тестового пользователя и тариф
        user = User(
            email="test@example.com",
            hashed_password="test",
            is_active=True
        )
        db_session.add(user)
        db_session.flush()

        # Пытаемся найти существующий тариф с таким именем, чтобы не нарушать уникальность
        tariff = db_session.query(Tariff).filter(Tariff.name == "Start").first()
        if not tariff:
            tariff = Tariff(
                name="Start",
                price=2990,
                analyses_limit=50,
                package_limit=5
            )
            db_session.add(tariff)
            db_session.flush()
        
        result = create_payment(user.id, tariff.id, db_session)
        
        assert "payment_id" in result
        assert "confirmation_url" in result
        assert "amount" in result
        assert result["amount"] == 2990
        assert "currency" in result
        assert result["currency"] == "RUB"
    
    def test_activate_subscription_mock(self, db_session):
        """Тест эмуляции активации подписки"""
        # Создаем тестового пользователя и тариф
        user = db_session.query(User).filter(User.email == "test2@example.com").first()
        if not user:
            user = User(
                email="test2@example.com",
                hashed_password="test",
                is_active=True,
                plan_type="trial"
            )
            db_session.add(user)
            db_session.flush()
        # Используем существующий тариф Pro, если он уже есть, иначе создаем
        tariff = db_session.query(Tariff).filter(Tariff.name == "Pro").first()
        if not tariff:
            tariff = Tariff(
                name="Pro",
                price=9990,
                analyses_limit=200,
                package_limit=10
            )
            db_session.add(tariff)
            db_session.flush()
        
        success = activate_subscription_mock(user.id, tariff.id, db_session)
        
        assert success is True
        db_session.refresh(user)
        assert user.tariff_id == tariff.id
        assert user.plan_type == "pro"
        assert user.subscription_start is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

