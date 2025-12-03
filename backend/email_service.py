"""
Сервис для отправки email уведомлений
Базовая реализация для триалов и регистрации
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime, timedelta
from config import settings

logger = logging.getLogger(__name__)

# Настройки SMTP (можно переопределить через переменные окружения)
SMTP_HOST = getattr(settings, 'SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = getattr(settings, 'SMTP_PORT', 587)
SMTP_USER = getattr(settings, 'SMTP_USER', '')
SMTP_PASSWORD = getattr(settings, 'SMTP_PASSWORD', '')
SMTP_FROM = getattr(settings, 'SMTP_FROM', 'noreply@tendershield.pro')
SMTP_USE_TLS = getattr(settings, 'SMTP_USE_TLS', True)

# Флаг для эмуляции отправки (если SMTP не настроен)
USE_MOCK_EMAIL = not SMTP_USER or not SMTP_PASSWORD


class EmailService:
    """Сервис для отправки email"""
    
    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Отправляет email
        
        Args:
            to_email: Email получателя
            subject: Тема письма
            html_body: HTML содержимое
            text_body: Текстовое содержимое (опционально)
            
        Returns:
            True если отправлено успешно
        """
        if USE_MOCK_EMAIL:
            # Эмуляция отправки для разработки
            logger.info(f"[MOCK EMAIL] Отправка письма:")
            logger.info(f"  To: {to_email}")
            logger.info(f"  Subject: {subject}")
            logger.info(f"  Body: {html_body[:100]}...")
            return True
        
        try:
            # Создаем сообщение
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = SMTP_FROM
            msg['To'] = to_email
            
            # Добавляем текстовую и HTML версии
            if text_body:
                text_part = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Отправляем
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            
            logger.info(f"✅ Email отправлен: {to_email} - {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки email: {e}")
            return False
    
    @staticmethod
    def send_welcome_email(email: str, name: str = None, trial_days: int = 14) -> bool:
        """Отправляет приветственное письмо после регистрации"""
        subject = "Добро пожаловать в Tender Shield Pro! 🎉"
        
        name_display = name if name else "Специалист"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .features {{ list-style: none; padding: 0; }}
                .features li {{ padding: 10px 0; border-bottom: 1px solid #ddd; }}
                .features li:before {{ content: "✅ "; margin-right: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Добро пожаловать, {name_display}!</h1>
                </div>
                <div class="content">
                    <p>Спасибо за регистрацию в Tender Shield Pro!</p>
                    
                    <p>У вас есть <strong>{trial_days} дней бесплатного триала</strong> с полным доступом ко всем функциям:</p>
                    
                    <ul class="features">
                        <li>Неограниченные анализы тендерной документации</li>
                        <li>Пакетный анализ нескольких документов</li>
                        <li>Генерация документов (протокол разногласий, жалобы в ФАС)</li>
                        <li>Экспорт результатов в PDF и Excel</li>
                        <li>История всех анализов</li>
                        <li>База знаний по тендерному законодательству</li>
                    </ul>
                    
                    <p><strong>Начните прямо сейчас:</strong></p>
                    <a href="https://app.tendershield.pro/analyzer" class="button">Загрузить первый документ</a>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        Если у вас есть вопросы, мы всегда готовы помочь!<br>
                        С уважением,<br>
                        Команда Tender Shield Pro
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(email, subject, html_body)
    
    @staticmethod
    def send_trial_reminder(email: str, name: str = None, days_remaining: int = 7) -> bool:
        """Отправляет напоминание о триале"""
        subject = f"Осталось {days_remaining} дней триала в Tender Shield Pro"
        
        name_display = name if name else "Специалист"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f39c12; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Осталось {days_remaining} дней триала</h1>
                </div>
                <div class="content">
                    <p>Привет, {name_display}!</p>
                    
                    <p>У вас осталось <strong>{days_remaining} дней</strong> бесплатного триала в Tender Shield Pro.</p>
                    
                    <p>Успели протестировать все функции? Готовы ли обсудить, как Tender Shield Pro может помочь вашей компании?</p>
                    
                    <p>Если у вас есть вопросы или нужна помощь, мы всегда на связи!</p>
                    
                    <a href="https://app.tendershield.pro/profile" class="button">Перейти в профиль</a>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        С уважением,<br>
                        Команда Tender Shield Pro
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(email, subject, html_body)
    
    @staticmethod
    def send_trial_ending_email(email: str, name: str = None) -> bool:
        """Отправляет письмо об окончании триала"""
        subject = "Триал заканчивается завтра - продлите доступ!"
        
        name_display = name if name else "Специалист"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #e74c3c; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
                .offer {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Триал заканчивается завтра!</h1>
                </div>
                <div class="content">
                    <p>Привет, {name_display}!</p>
                    
                    <p>Завтра заканчивается ваш бесплатный триал в Tender Shield Pro.</p>
                    
                    <div class="offer">
                        <p><strong>🎁 Специальное предложение:</strong></p>
                        <p>Продлите доступ на 7 дополнительных дней всего за <strong>1₽</strong> + получите скидку 20% на первый месяц!</p>
                    </div>
                    
                    <p>Или выберите один из наших тарифов:</p>
                    <ul>
                        <li><strong>Start</strong> - 2,990₽/мес (50 анализов)</li>
                        <li><strong>Pro</strong> - 9,990₽/мес (200 анализов)</li>
                    </ul>
                    
                    <a href="https://app.tendershield.pro/pricing" class="button">Выбрать тариф</a>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        Если у вас есть вопросы, напишите нам!<br>
                        С уважением,<br>
                        Команда Tender Shield Pro
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(email, subject, html_body)
    
    @staticmethod
    def send_trial_ended_email(email: str, name: str = None) -> bool:
        """Отправляет письмо после окончания триала"""
        subject = "Триал закончился - вернитесь в Tender Shield Pro!"
        
        name_display = name if name else "Специалист"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #95a5a6; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Триал закончился</h1>
                </div>
                <div class="content">
                    <p>Привет, {name_display}!</p>
                    
                    <p>Ваш бесплатный триал в Tender Shield Pro закончился.</p>
                    
                    <p>Но мы хотим, чтобы вы остались с нами! Вы можете:</p>
                    <ul>
                        <li>Продолжить с <strong>Free тарифом</strong> (2 анализа/месяц)</li>
                        <li>Выбрать платный тариф для неограниченного доступа</li>
                    </ul>
                    
                    <a href="https://app.tendershield.pro/pricing" class="button">Выбрать тариф</a>
                    
                    <p style="margin-top: 30px; color: #666; font-size: 14px;">
                        С уважением,<br>
                        Команда Tender Shield Pro
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(email, subject, html_body)

