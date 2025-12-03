"""
Модуль для уведомлений пользователей о важных событиях
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from database import User, Analysis, Usage, Tariff

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для управления уведомлениями"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_limit_warnings(self, user_id: int) -> List[Dict]:
        """
        Проверяет предупреждения о лимитах для пользователя
        
        Returns:
            Список уведомлений
        """
        notifications = []
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.tariff:
            return notifications
        
        # Получаем использование за текущий месяц
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage = self.db.query(Usage).filter(
            and_(
                Usage.user_id == user_id,
                Usage.month >= current_month_start
            )
        ).first()
        
        analyses_count = usage.analyses_count if usage else 0
        limit = user.tariff.analyses_limit
        
        # Предупреждение при 80% использования
        if limit > 0:
            usage_percent = (analyses_count / limit) * 100
            remaining = limit - analyses_count
            
            if usage_percent >= 80 and remaining > 0:
                notifications.append({
                    'type': 'warning',
                    'title': 'Приближается лимит анализов',
                    'message': f'Осталось {remaining} из {limit} анализов в этом месяце',
                    'action': 'upgrade',
                    'priority': 'high' if usage_percent >= 90 else 'medium'
                })
            
            # Критическое предупреждение при 95%
            if usage_percent >= 95 and remaining > 0:
                notifications.append({
                    'type': 'critical',
                    'title': 'Критически близок лимит',
                    'message': f'Осталось всего {remaining} анализов! Обновите тариф для продолжения работы.',
                    'action': 'upgrade',
                    'priority': 'critical'
                })
            
            # Лимит достигнут
            if analyses_count >= limit:
                notifications.append({
                    'type': 'error',
                    'title': 'Лимит анализов достигнут',
                    'message': f'Вы использовали все {limit} анализов в этом месяце. Обновите тариф для продолжения.',
                    'action': 'upgrade',
                    'priority': 'critical'
                })
        
        # Проверка триала
        if hasattr(user, 'is_trial_active') and user.is_trial_active():
            days_left = user.get_remaining_trial_days() if hasattr(user, 'get_remaining_trial_days') else 0
            
            if days_left <= 3 and days_left > 0:
                notifications.append({
                    'type': 'warning',
                    'title': 'Триал скоро закончится',
                    'message': f'Осталось {days_left} дней бесплатного триала',
                    'action': 'subscribe',
                    'priority': 'high'
                })
            elif days_left <= 0:
                notifications.append({
                    'type': 'info',
                    'title': 'Триал закончился',
                    'message': 'Ваш бесплатный триал завершен. Выберите тариф для продолжения работы.',
                    'action': 'subscribe',
                    'priority': 'medium'
                })
        
        return notifications
    
    def check_inactivity(self, user_id: int, days: int = 7) -> Optional[Dict]:
        """
        Проверяет неактивность пользователя
        
        Args:
            user_id: ID пользователя
            days: Количество дней неактивности для уведомления
            
        Returns:
            Уведомление или None
        """
        # Получаем последний анализ пользователя
        last_analysis = self.db.query(Analysis).filter(
            Analysis.user_id == user_id
        ).order_by(Analysis.created_at.desc()).first()
        
        if not last_analysis:
            return None
        
        days_since_last = (datetime.utcnow() - last_analysis.created_at).days
        
        if days_since_last >= days:
            return {
                'type': 'info',
                'title': 'Давно не было активности',
                'message': f'Вы не использовали систему {days_since_last} дней. Попробуйте проанализировать новый тендер!',
                'action': 'analyze',
                'priority': 'low'
            }
        
        return None
    
    def get_all_notifications(self, user_id: int) -> List[Dict]:
        """
        Получает все уведомления для пользователя
        
        Returns:
            Список всех уведомлений
        """
        notifications = []
        
        # Проверяем лимиты
        notifications.extend(self.check_limit_warnings(user_id))
        
        # Проверяем неактивность
        inactivity = self.check_inactivity(user_id)
        if inactivity:
            notifications.append(inactivity)
        
        # Сортируем по приоритету
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        notifications.sort(key=lambda x: priority_order.get(x.get('priority', 'low'), 3))
        
        return notifications

