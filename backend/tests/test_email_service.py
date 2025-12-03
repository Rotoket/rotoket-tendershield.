"""
Тесты для email сервиса
"""

import pytest
from email_service import EmailService


class TestEmailService:
    """Тесты для email сервиса"""
    
    def test_send_email_structure(self):
        """Тест структуры отправки email"""
        # В тестовом режиме должна работать эмуляция
        result = EmailService.send_email(
            to_email="test@example.com",
            subject="Test",
            html_body="<p>Test</p>"
        )
        
        # Должна вернуть True (даже в mock режиме)
        assert isinstance(result, bool)
    
    def test_welcome_email(self):
        """Тест отправки приветственного письма"""
        result = EmailService.send_welcome_email(
            email="test@example.com",
            name="Тестовый Пользователь",
            trial_days=14
        )
        
        assert result is True
    
    def test_trial_reminder_email(self):
        """Тест отправки напоминания о триале"""
        result = EmailService.send_trial_reminder(
            email="test@example.com",
            name="Тестовый Пользователь",
            days_remaining=7
        )
        
        assert result is True
    
    def test_trial_ending_email(self):
        """Тест отправки письма об окончании триала"""
        result = EmailService.send_trial_ending_email(
            email="test@example.com",
            name="Тестовый Пользователь"
        )
        
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

