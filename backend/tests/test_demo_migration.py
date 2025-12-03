"""
Тесты для миграции демо-анализов
"""

import pytest
from datetime import datetime
from database import User, Analysis, DemoSession
from demo_migration import migrate_demo_analyses_to_user
from sqlalchemy.orm import Session


class TestDemoMigration:
    """Тесты для миграции демо-анализов"""
    
    def test_migrate_demo_analyses(self, db_session):
        """Тест миграции демо-анализов в профиль пользователя"""
        # На всякий случай очищаем старые демо-анализы для этой сессии,
        # чтобы тест был идемпотентным при повторных запусках.
        db_session.query(Analysis).filter(Analysis.session_id == "test-migration-session").delete()
        db_session.commit()

        # Создаем или переиспользуем демо-сессию
        demo_session = db_session.query(DemoSession).filter(DemoSession.id == "test-migration-session").first()
        if not demo_session:
            demo_session = DemoSession(
                id="test-migration-session",
                device_fingerprint="test-device"
            )
            db_session.add(demo_session)
            db_session.flush()
        
        # Создаем демо-анализы
        for i in range(3):
            analysis = Analysis(
                session_id=demo_session.id,
                is_demo=True,
                filename=f"test_{i}.pdf",
                industry="UNIVERSAL",
                result_json={"score": 75, "verdict": "PARTICIPATE"},
                score=75,
                verdict="PARTICIPATE"
            )
            db_session.add(analysis)
        
        db_session.commit()
        
        # Создаем пользователя (или переиспользуем, если уже существует)
        from auth import get_password_hash
        user = db_session.query(User).filter(User.email == "migration@test.com").first()
        if not user:
            user = User(
                email="migration@test.com",
                hashed_password=get_password_hash("test123"),
                is_active=True
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
        
        # Считаем количество не-демо анализов пользователя до миграции
        base_analyses = db_session.query(Analysis).filter(
            Analysis.user_id == user.id,
            Analysis.is_demo == False
        ).count()

        # Мигрируем анализы
        migrated_count = migrate_demo_analyses_to_user(demo_session.id, user.id, db_session)
        
        # Должны быть мигрированы ровно 3 новых анализа
        assert migrated_count == 3
        
        # Проверяем, что анализы привязаны к пользователю
        migrated_analyses = db_session.query(Analysis).filter(
            Analysis.user_id == user.id,
            Analysis.is_demo == False
        ).all()
        
        # Разница по количеству должна составлять 3, даже если у пользователя уже были анализы
        assert len(migrated_analyses) - base_analyses == 3
        assert all(a.session_id is None for a in migrated_analyses)
        assert all(not a.is_demo for a in migrated_analyses)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

