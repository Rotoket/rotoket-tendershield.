"""
Модуль для аналитики и метрик системы
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database import User, Analysis, PackageAnalysis, Usage, Tariff

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Сервис для сбора и анализа метрик"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Получить статистику пользователя"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        # Количество анализов
        analyses_count = self.db.query(func.count(Analysis.id)).filter(
            Analysis.user_id == user_id
        ).scalar() or 0
        
        # Количество пакетных анализов
        packages_count = self.db.query(func.count(PackageAnalysis.id)).filter(
            PackageAnalysis.user_id == user_id
        ).scalar() or 0
        
        # Использование за текущий месяц
        current_month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        usage = self.db.query(Usage).filter(
            and_(
                Usage.user_id == user_id,
                Usage.month >= current_month_start
            )
        ).first()
        
        return {
            "user_id": user_id,
            "email": user.email,
            "plan_type": user.plan_type,
            "total_analyses": analyses_count,
            "total_packages": packages_count,
            "current_month_analyses": usage.analyses_count if usage else 0,
            "tariff_limit": user.tariff.analyses_limit if user.tariff else 0,
            "trial_active": user.is_trial_active() if hasattr(user, 'is_trial_active') else False,
            "trial_days_left": user.get_remaining_trial_days() if hasattr(user, 'get_remaining_trial_days') else 0
        }
    
    def get_system_stats(self) -> Dict:
        """Получить общую статистику системы"""
        # Всего пользователей
        total_users = self.db.query(func.count(User.id)).scalar() or 0
        
        # Активных пользователей (с анализами за последние 30 дней)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        active_users = self.db.query(func.count(func.distinct(Analysis.user_id))).filter(
            Analysis.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # Всего анализов
        total_analyses = self.db.query(func.count(Analysis.id)).scalar() or 0
        
        # Анализов за последние 30 дней
        recent_analyses = self.db.query(func.count(Analysis.id)).filter(
            Analysis.created_at >= thirty_days_ago
        ).scalar() or 0
        
        # Распределение по тарифам
        tariff_distribution = {}
        for tariff in self.db.query(Tariff).all():
            count = self.db.query(func.count(User.id)).filter(
                User.tariff_id == tariff.id
            ).scalar() or 0
            tariff_distribution[tariff.name] = count
        
        # Распределение по отраслям
        industry_distribution = self.db.query(
            Analysis.industry,
            func.count(Analysis.id)
        ).group_by(Analysis.industry).all()
        
        return {
            "total_users": total_users,
            "active_users_30d": active_users,
            "total_analyses": total_analyses,
            "recent_analyses_30d": recent_analyses,
            "tariff_distribution": tariff_distribution,
            "industry_distribution": {ind: count for ind, count in industry_distribution}
        }
    
    def get_analyses_timeline(self, user_id: Optional[int] = None, days: int = 30) -> List[Dict]:
        """Получить временную линию анализов"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(
            func.date(Analysis.created_at).label('date'),
            func.count(Analysis.id).label('count')
        ).filter(
            Analysis.created_at >= start_date
        )
        
        if user_id:
            query = query.filter(Analysis.user_id == user_id)
        
        results = query.group_by(func.date(Analysis.created_at)).all()
        
        return [
            {
                "date": result.date.isoformat(),
                "count": result.count
            }
            for result in results
        ]
    
    def get_popular_industries(self, limit: int = 5) -> List[Dict]:
        """Получить популярные отрасли"""
        results = self.db.query(
            Analysis.industry,
            func.count(Analysis.id).label('count')
        ).group_by(Analysis.industry).order_by(
            func.count(Analysis.id).desc()
        ).limit(limit).all()
        
        return [
            {
                "industry": result.industry,
                "count": result.count
            }
            for result in results
        ]
    
    def get_average_scores(self) -> Dict:
        """Получить средние оценки по отраслям"""
        results = self.db.query(
            Analysis.industry,
            func.avg(Analysis.score).label('avg_score'),
            func.count(Analysis.id).label('count')
        ).group_by(Analysis.industry).all()
        
        return {
            result.industry: {
                "average_score": float(result.avg_score) if result.avg_score else 0,
                "analyses_count": result.count
            }
            for result in results
        }

