"""
Модуль для миграции демо-анализов при регистрации пользователя
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import User, Analysis, DemoSession

logger = logging.getLogger(__name__)


def migrate_demo_analyses_to_user(session_id: str, user_id: int, db: Session) -> int:
    """
    Мигрирует демо-анализы в профиль пользователя при регистрации
    
    Args:
        session_id: ID демо-сессии
        user_id: ID нового пользователя
        db: Сессия БД
        
    Returns:
        Количество мигрированных анализов
    """
    try:
        # Находим все демо-анализы для этой сессии
        demo_analyses = db.query(Analysis).filter(
            Analysis.session_id == session_id,
            Analysis.is_demo == True
        ).order_by(Analysis.created_at.desc()).limit(10).all()  # Мигрируем последние 10
        
        if not demo_analyses:
            logger.info(f"Нет демо-анализов для миграции (session_id: {session_id})")
            return 0
        
        # Мигрируем анализы
        migrated_count = 0
        for analysis in demo_analyses:
            analysis.user_id = user_id
            analysis.session_id = None
            analysis.is_demo = False
            migrated_count += 1
        
        db.commit()
        logger.info(f"✅ Мигрировано {migrated_count} демо-анализов для пользователя {user_id}")
        
        return migrated_count
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка миграции демо-анализов: {e}")
        return 0


def register_user_from_demo(
    session_id: str,
    email: str,
    password: str,
    name: str = None,
    company: str = None,
    db: Session = None
) -> User:
    """
    Регистрирует пользователя из демо-сессии с миграцией анализов
    
    Args:
        session_id: ID демо-сессии
        email: Email пользователя
        password: Пароль
        name: Имя пользователя
        company: Название компании
        db: Сессия БД
        
    Returns:
        Созданный пользователь
    """
    from auth import get_password_hash
    from datetime import datetime, timedelta
    
    # Проверяем, существует ли пользователь
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError("Пользователь с таким email уже существует")
    
    # Создаем пользователя с триалом
    hashed_password = get_password_hash(password)
    now = datetime.utcnow()
    trial_end = now + timedelta(days=14)
    
    new_user = User(
        email=email,
        hashed_password=hashed_password,
        name=name,
        company=company,
        is_active=True,
        plan_type="trial",
        trial_start=now,
        trial_end=trial_end,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Мигрируем демо-анализы
    migrated_count = migrate_demo_analyses_to_user(session_id, new_user.id, db)
    
    logger.info(f"✅ Пользователь {email} зарегистрирован, мигрировано {migrated_count} анализов")
    
    return new_user

