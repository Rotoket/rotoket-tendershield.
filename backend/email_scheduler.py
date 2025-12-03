"""
Планировщик для отправки email уведомлений о триалах
Запускается как фоновый процесс или через cron
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import get_db, User
from email_service import EmailService

logger = logging.getLogger(__name__)


def send_trial_reminders(db: Session):
    """Отправляет напоминания о триалах"""
    now = datetime.utcnow()
    
    # Пользователи с триалом, у которых осталось 7 дней
    seven_days_later = now + timedelta(days=7)
    users_7_days = db.query(User).filter(
        User.plan_type == "trial",
        User.trial_end.isnot(None),
        User.trial_end <= seven_days_later,
        User.trial_end > now
    ).all()
    
    for user in users_7_days:
        days_remaining = (user.trial_end - now).days
        if days_remaining == 7:
            try:
                EmailService.send_trial_reminder(
                    email=user.email,
                    name=user.name,
                    days_remaining=7
                )
                logger.info(f"Отправлено напоминание о триале пользователю {user.email}")
            except Exception as e:
                logger.error(f"Ошибка отправки напоминания {user.email}: {e}")
    
    # Пользователи с триалом, у которых осталось 1 день
    one_day_later = now + timedelta(days=1)
    users_1_day = db.query(User).filter(
        User.plan_type == "trial",
        User.trial_end.isnot(None),
        User.trial_end <= one_day_later,
        User.trial_end > now
    ).all()
    
    for user in users_1_day:
        days_remaining = (user.trial_end - now).days
        if days_remaining == 1:
            try:
                EmailService.send_trial_ending_email(
                    email=user.email,
                    name=user.name
                )
                logger.info(f"Отправлено письмо об окончании триала пользователю {user.email}")
            except Exception as e:
                logger.error(f"Ошибка отправки письма об окончании триала {user.email}: {e}")
    
    # Пользователи, у которых триал закончился вчера
    yesterday = now - timedelta(days=1)
    users_ended = db.query(User).filter(
        User.plan_type == "trial",
        User.trial_end.isnot(None),
        User.trial_end <= yesterday,
        User.trial_end > yesterday - timedelta(days=1)
    ).all()
    
    for user in users_ended:
        try:
            EmailService.send_trial_ended_email(
                email=user.email,
                name=user.name
            )
            logger.info(f"Отправлено письмо после окончания триала пользователю {user.email}")
        except Exception as e:
            logger.error(f"Ошибка отправки письма после окончания триала {user.email}: {e}")


def run_email_scheduler():
    """Запускает планировщик email уведомлений"""
    logger.info("📧 Запуск планировщика email уведомлений...")
    
    db = next(get_db())
    try:
        send_trial_reminders(db)
        logger.info("✅ Планировщик завершил работу")
    except Exception as e:
        logger.error(f"❌ Ошибка планировщика: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    run_email_scheduler()

