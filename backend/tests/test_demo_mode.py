"""
Тесты для демо-режима
"""

import pytest
from datetime import datetime, timedelta
from database import DemoSession


class TestDemoSession:
    """Тесты для модели DemoSession"""
    
    def test_can_analyze_first_time(self):
        """Тест: первый анализ должен быть разрешен"""
        demo = DemoSession(
            id="test-session-1",
            analyses_count=0,
            last_analysis_at=None
        )
        
        can_analyze, reason = demo.can_analyze()
        assert can_analyze is True
        assert reason == "OK"
    
    def test_can_analyze_within_limit(self):
        """Тест: анализ в пределах лимита (3 в сутки)"""
        demo = DemoSession(
            id="test-session-2",
            analyses_count=2,
            last_analysis_at=datetime.utcnow() - timedelta(hours=1)
        )
        
        can_analyze, reason = demo.can_analyze()
        assert can_analyze is True
    
    def test_cannot_analyze_limit_reached(self):
        """Тест: лимит достигнут (3 анализа за последние 24 часа)"""
        demo = DemoSession(
            id="test-session-3",
            analyses_count=3,
            last_analysis_at=datetime.utcnow() - timedelta(hours=2)
        )
        
        can_analyze, reason = demo.can_analyze()
        assert can_analyze is False
        assert "лимит" in reason.lower() or "попробуйте" in reason.lower()
    
    def test_can_analyze_after_24_hours(self):
        """Тест: можно анализировать после 24 часов (сброс счетчика)"""
        demo = DemoSession(
            id="test-session-4",
            analyses_count=3,
            last_analysis_at=datetime.utcnow() - timedelta(hours=25)
        )
        
        can_analyze, reason = demo.can_analyze()
        # После 24 часов счетчик должен сброситься
        assert can_analyze is True
    
    def test_increment_analyses(self):
        """Тест: увеличение счетчика анализов"""
        demo = DemoSession(
            id="test-session-5",
            analyses_count=1,
            last_analysis_at=None
        )
        
        initial_count = demo.analyses_count
        demo.increment_analyses()
        
        assert demo.analyses_count == initial_count + 1
        assert demo.last_analysis_at is not None


class TestDemoModeIntegration:
    """Интеграционные тесты для демо-режима"""
    
    def test_demo_session_creation(self):
        """Тест создания демо-сессии"""
        demo = DemoSession(
            id="test-integration-1",
            device_fingerprint="test-device",
            analyses_count=0
        )
        
        assert demo.id == "test-integration-1"
        assert demo.analyses_count == 0
        assert demo.created_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

